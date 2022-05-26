from queue import Queue
from concurrent.futures import ThreadPoolExecutor, Future, wait
from typing import Any, Callable, Iterable, Optional, Union, Set
from mypy_boto3_organizations.client import OrganizationsClient
from mypy_boto3_organizations.type_defs import (
    OrganizationTypeDef,
    RootTypeDef,
    OrganizationalUnitTypeDef,
    AccountTypeDef,
    TagTypeDef,
)
from boto3 import Session
from pubsub import pub  # type: ignore[import]
from pubsub.core import Topic  # type: ignore[import]

Account = AccountTypeDef
Org = OrganizationTypeDef
OrgUnit = OrganizationalUnitTypeDef
Root = RootTypeDef
Tag = TagTypeDef

Parent = Union[Root, OrgUnit]
Resource = Union[Account, OrgUnit, Root]

Task = Callable[..., None]


def main() -> None:
    pub.subscribe(spy, pub.ALL_TOPICS)
    discover_all_things_in_organization(Session())


def spy(topic: Topic = pub.AUTO_TOPIC, **data: Any) -> None:
    print(f"{topic.getName()} {data}")


def discover_all_things_in_organization(session: Session, max_workers: int = 8) -> None:
    client = session.client("organizations")
    queue: "Queue[Task]" = Queue()

    pub.subscribe(publish_roots, "organization", client=client, queue=queue)
    pub.subscribe(publish_organizational_units, "parent", client=client, queue=queue)
    pub.subscribe(publish_accounts, "parent", client=client, queue=queue)
    pub.subscribe(publish_tags, "root", client=client, queue=queue)
    pub.subscribe(publish_tags, "organizational_unit", client=client, queue=queue)
    pub.subscribe(publish_tags, "account", client=client, queue=queue)

    def init() -> None:
        publish_organization(client, queue)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures: Set[Future[None]] = {executor.submit(init)}

        while futures:

            done, _ = wait(futures, timeout=0.5, return_when="FIRST_COMPLETED")

            while not queue.empty():
                futures.add(executor.submit(queue.get()))

            for future in done:
                try:
                    future.result()
                except Exception as exc:
                    print(repr(exc))

            futures -= done


def publish_organization(client: OrganizationsClient, queue: "Queue[Task]") -> None:
    def _work() -> None:
        org = describe_organization(client)
        pub.sendMessage("organization", org=org)
    queue.put(_work)


def publish_roots(client: OrganizationsClient, queue: "Queue[Task]", org: Org) -> None:
    def _work() -> None:
        for root in list_roots(client):
            pub.sendMessage("root", resource=root)
            pub.sendMessage("parent", parent=root)
    queue.put(_work)


def publish_organizational_units(
    client: OrganizationsClient, queue: "Queue[Task]", parent: Parent
) -> None:
    def _work() -> None:
        for orgunit in list_organizational_units_for_parent(client, parent):
            pub.sendMessage("organizational_unit", resource=orgunit, parent=parent)
            pub.sendMessage("parent", parent=orgunit)
    queue.put(_work)


def publish_accounts(client: OrganizationsClient, queue: "Queue[Task]", parent: Parent) -> None:
    def _work() -> None:
        for account in list_accounts_for_parent(client, parent):
            pub.sendMessage("account", resource=account, parent=parent)
    queue.put(_work)


def publish_tags(
    client: OrganizationsClient,
    queue: "Queue[Task]",
    resource: Resource,
    parent: Optional[Parent] = None
) -> None:
    def _work() -> None:
        for tag in list_tags_for_resource(client, resource):
            pub.sendMessage("tag", tag=tag, resource=resource)
    queue.put(_work)


def describe_organization(client: OrganizationsClient) -> Org:
    return client.describe_organization()["Organization"]


def list_roots(client: OrganizationsClient) -> Iterable[Root]:
    pages = client.get_paginator("list_roots").paginate()
    for page in pages:
        for root in page["Roots"]:
            yield root


def list_organizational_units_for_parent(
    client: OrganizationsClient, parent: Parent
) -> Iterable[OrgUnit]:
    pages = (
        client
        .get_paginator("list_organizational_units_for_parent")
        .paginate(ParentId=parent["Id"])
    )
    for page in pages:
        for orgunit in page["OrganizationalUnits"]:
            yield orgunit


def list_accounts_for_parent(
    client: OrganizationsClient, parent: Parent
) -> Iterable[Account]:
    pages = (
        client
        .get_paginator("list_accounts_for_parent")
        .paginate(ParentId=parent["Id"])
    )
    for page in pages:
        for account in page["Accounts"]:
            yield account


def list_tags_for_resource(
    client: OrganizationsClient, resource: Resource
) -> Iterable[Tag]:
    pages = (
        client
        .get_paginator("list_tags_for_resource")
        .paginate(ResourceId=resource["Id"])
    )
    for page in pages:
        for tag in page["Tags"]:
            yield tag


if __name__ == "__main__":
    main()
