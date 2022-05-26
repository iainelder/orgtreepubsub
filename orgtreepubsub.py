from typing import Any, Iterable, Optional, Union
from mypy_boto3_organizations.client import OrganizationsClient
from mypy_boto3_organizations.type_defs import (
    OrganizationTypeDef,
    RootTypeDef,
    OrganizationalUnitTypeDef,
    AccountTypeDef,
    TagTypeDef,
)
from boto3 import Session
from pubsub import pub
from pubsub.core import Topic

Account = AccountTypeDef
Org = OrganizationTypeDef
OrgUnit = OrganizationalUnitTypeDef
Root = RootTypeDef
Tag = TagTypeDef

Parent = Union[Root, OrgUnit]
Resource = Union[Account, OrgUnit, Root]


def main() -> None:
    pub.subscribe(spy, pub.ALL_TOPICS)
    publish_organization(Session())


def spy(topic: Topic = pub.AUTO_TOPIC, **data: Any) -> None:
    print(f"{topic.getName()} {data}")


def publish_organization(session: Session) -> None:
    client = session.client("organizations")

    pub.subscribe(publish_roots, "organization", client=client)
    pub.subscribe(publish_organizational_units, "parent", client=client)
    pub.subscribe(publish_accounts, "parent", client=client)
    pub.subscribe(publish_tags, "root", client=client)
    pub.subscribe(publish_tags, "organizational_unit", client=client)
    pub.subscribe(publish_tags, "account", client=client)

    org = describe_organization(client)
    pub.sendMessage("organization", org=org)


def publish_roots(client: OrganizationsClient, org: Org) -> None:
    for root in list_roots(client):
        pub.sendMessage("root", resource=root)
        pub.sendMessage("parent", parent=root)


def publish_organizational_units(client: OrganizationsClient, parent: Parent) -> None:
    for orgunit in list_organizational_units_for_parent(client, parent):
        pub.sendMessage("organizational_unit", resource=orgunit, parent=parent)
        pub.sendMessage("parent", parent=orgunit)


def publish_accounts(client: OrganizationsClient, parent: Parent) -> None:
    for account in list_accounts_for_parent(client, parent):
        pub.sendMessage("account", resource=account, parent=parent)


def publish_tags(
    client: OrganizationsClient, resource: Resource, parent: Optional[Parent] = None
) -> None:
    for tag in list_tags_for_resource(client, resource):
        pub.sendMessage("tag", tag=tag, resource=resource)


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
