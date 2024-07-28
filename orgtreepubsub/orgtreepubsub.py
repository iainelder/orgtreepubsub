from queue import Queue
from concurrent.futures import ThreadPoolExecutor, Future, wait
from typing import Callable, Iterable, Set

from boto3 import Session
from botocore.exceptions import ClientError
from mypy_boto3_organizations import OrganizationsClient

from .type_defs import Account, Org, OrgUnit, Root, Tag, Parent, Resource
from .type_defs import OrganizationError, OrganizationDoesNotExistError
from blinker import Signal


Task = Callable[..., None]


class OrgCrawler:

    def __init__(self, session: Session,) -> None:

        self.queue = Queue[Task]()
        self.client: OrganizationsClient = session.client("organizations")

        self.init: Task = lambda: None

        self.on_organization = Signal()
        self.on_root = Signal()
        self.on_orgunit = Signal()
        self.on_account = Signal()
        self.on_parentage = Signal()
        self.on_tag = Signal()

    def crawl(self, max_workers: int = 4, loop_wait_timeout: float = 0.1) -> None:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures: Set[Future[None]] = {executor.submit(self.init)}

            while futures:

                done, _ = wait(
                    futures, timeout=loop_wait_timeout, return_when="FIRST_COMPLETED"
                )

                while not self.queue.empty():
                    futures.add(executor.submit(self.queue.get()))

                for future in done:
                    raise_if_result_is_error_else_continue(future)

                futures -= done

    def publish_organization(self) -> None:
        def _work() -> None:
            org = self.describe_organization()
            self.on_organization.send(self, org=org)
        self.queue.put(_work)

    def describe_organization(self) -> Org:
        return Org.from_boto3(self.client.describe_organization()["Organization"])

    def publish_roots(self) -> None:
        def _work() -> None:
            for root in self.list_roots():
                self.on_root.send(self, resource=root)
        self.queue.put(_work)

    def list_roots(self) -> Iterable[Root]:
        pages = self.client.get_paginator("list_roots").paginate()
        for page in pages:
            for root in page["Roots"]:
                yield Root.from_boto3(root)

    def publish_orgunits_under_resource(self, resource: Parent) -> None:
        def _work() -> None:
            for orgunit in self.list_organizational_units_for_parent(resource):
                self.on_orgunit.send(self, resource=orgunit)
                self.on_parentage.send(self, parent=resource, child=orgunit)
        self.queue.put(_work)

    def list_organizational_units_for_parent(self, parent: Parent) -> Iterable[OrgUnit]:
        pages = (
            self.client.get_paginator("list_organizational_units_for_parent")
            .paginate(ParentId=parent.id)
        )
        for page in pages:
            for orgunit in page["OrganizationalUnits"]:
                yield OrgUnit.from_boto3(orgunit)

    def publish_accounts_under_resource(self, resource: Parent) -> None:
        def _work() -> None:
            for account in self.list_accounts_for_parent(resource):
                self.on_account.send(self, resource=account)
                self.on_parentage.send(self, parent=resource, child=account)
        self.queue.put(_work)

    def list_accounts_for_parent(self, parent: Parent) -> Iterable[Account]:
        pages = (
            self.client.get_paginator("list_accounts_for_parent")
            .paginate(ParentId=parent.id)
        )
        for page in pages:
            for account in page["Accounts"]:
                yield Account.from_boto3(account)

    def publish_tags(self, resource: Resource) -> None:
        def _work() -> None:
            for tag in self.list_tags_for_resource(resource):
                self.on_tag.send(self, tag=tag, resource=resource)
        self.queue.put(_work)

    def list_tags_for_resource(self, resource: Resource) -> Iterable[Tag]:
        pages = (
            self.client.get_paginator("list_tags_for_resource")
            .paginate(ResourceId=resource.id)
        )
        for page in pages:
            for tag in page["Tags"]:
                yield Tag.from_boto3(tag)


def raise_if_result_is_error_else_continue(future: "Future[None]") -> None:
    try:
        future.result()
    except ClientError as error:
        if organization_does_not_exist(error):
            raise OrganizationDoesNotExistError() from error
        else:
            raise OrganizationError() from error


def organization_does_not_exist(error: ClientError) -> bool:
    return error.response["Error"]["Code"] == "AWSOrganizationsNotInUseException" # pyright: ignore[reportTypedDictNotRequiredAccess]
