# pyright: reportTypedDictNotRequiredAccess=false, reportUnknownMemberType=false

from typing import Any
from pubsub import pub  # type: ignore[import]
from boto3 import Session
import boto3
from mypy_boto3_organizations.type_defs import TagTypeDef
from type_defs import Account, OrgUnit, OrganizationError
from orgtreepubsub import crawl_organization
from pytest import raises
from unittest.mock import Mock
from botocore.exceptions import ClientError
from pytest_mock import MockerFixture
import pytest


@pytest.fixture(autouse=True)
def new_org() -> None:
    boto3.client("organizations").create_organization(FeatureSet="ALL")


def test_in_new_org_publishes_organization() -> None:
    spy = Mock()
    pub.subscribe(spy, "organization")

    crawl_organization(Session())

    client = boto3.client("organizations")
    org = client.describe_organization()["Organization"]
    spy.assert_called_once_with(org=org)


def test_in_new_org_publishes_root_as_resource() -> None:
    spy = Mock()
    pub.subscribe(spy, "root")

    crawl_organization(Session())

    client = boto3.client("organizations")
    org = client.describe_organization()["Organization"]
    root = client.list_roots()["Roots"][0]
    spy.assert_called_once_with(org=org, resource=root)


def test_in_new_org_publishes_root_as_parent() -> None:
    spy = Mock()
    pub.subscribe(spy, "parent")

    crawl_organization(Session())

    client = boto3.client("organizations")
    root = client.list_roots()["Roots"][0]
    spy.assert_called_once_with(parent=root)


def test_in_new_org_publishes_mgmt_account() -> None:
    spy = Mock()
    pub.subscribe(spy, "account")

    crawl_organization(Session())

    client = boto3.client("organizations")
    root = client.list_roots()["Roots"][0]
    mgmt_account = Account.from_boto3(client.list_accounts()["Accounts"][0])
    spy.assert_called_once_with(parent=root, resource=mgmt_account)


def test_in_new_org_publishes_no_orgunit() -> None:
    spy = Mock()
    pub.subscribe(spy, "organizational_unit")

    crawl_organization(Session())

    spy.assert_not_called()


def test_in_new_org_publishes_no_tag() -> None:
    spy = Mock()
    pub.subscribe(spy, "tag")

    crawl_organization(Session())

    spy.assert_not_called()


def test_publishes_empty_orgunit_as_resource() -> None:
    client = boto3.client("organizations")
    root = client.list_roots()["Roots"][0]
    orgunit = OrgUnit.from_boto3(
        client.create_organizational_unit(ParentId=root["Id"], Name="OU1")["OrganizationalUnit"]
    )

    spy = Mock()
    pub.subscribe(spy, "organizational_unit")

    crawl_organization(Session())

    spy.assert_called_once_with(parent=root, resource=orgunit)


def test_publishes_empty_orgunit_as_parent() -> None:
    client = boto3.client("organizations")
    root = client.list_roots()["Roots"][0]
    orgunit = OrgUnit.from_boto3(
        client.create_organizational_unit(ParentId=root["Id"], Name="OU1")["OrganizationalUnit"]
    )

    spy = Mock()
    pub.subscribe(spy, "parent")

    crawl_organization(Session())

    spy.assert_any_call(parent=orgunit)


def test_when_orgunit_contains_account_crawl_publishes_account_as_resource() -> None:
    client = boto3.client("organizations")
    root = client.list_roots()["Roots"][0]
    orgunit = OrgUnit.from_boto3(
        client.create_organizational_unit(ParentId=root["Id"], Name="OU1")["OrganizationalUnit"]
    )
    child_request = client.create_account(AccountName="Account1", Email="1@aws.com")["CreateAccountStatus"]
    child_account = Account.from_boto3(client.describe_account(AccountId=child_request["AccountId"])["Account"])
    client.move_account(AccountId=child_account.id, SourceParentId=root["Id"], DestinationParentId=orgunit.id)

    spy = Mock()
    pub.subscribe(spy, "account")

    crawl_organization(Session())

    spy.assert_any_call(parent=orgunit, resource=child_account)


def test_when_orgunit_contains_orgunit_crawl_publishes_child_orgunit_as_resource() -> None:
    client = boto3.client("organizations")
    root = client.list_roots()["Roots"][0]
    parent_orgunit = OrgUnit.from_boto3(
        client.create_organizational_unit(ParentId=root["Id"], Name="OU1")["OrganizationalUnit"]
    )
    child_orgunit = OrgUnit.from_boto3(
        client.create_organizational_unit(ParentId=parent_orgunit.id, Name="OU2")["OrganizationalUnit"]
    )

    spy = Mock()
    pub.subscribe(spy, "organizational_unit")

    crawl_organization(Session())

    spy.assert_any_call(parent=parent_orgunit, resource=child_orgunit)


def test_when_orgunit_contains_orgunit_crawl_publishes_child_orgunit_as_parent() -> None:
    client = boto3.client("organizations")
    root = client.list_roots()["Roots"][0]
    parent_orgunit = OrgUnit.from_boto3(
        client.create_organizational_unit(ParentId=root["Id"], Name="OU1")["OrganizationalUnit"]
    )
    child_orgunit = OrgUnit.from_boto3(
        client.create_organizational_unit(ParentId=parent_orgunit.id, Name="OU2")["OrganizationalUnit"]
    )

    spy = Mock()
    pub.subscribe(spy, "parent")

    crawl_organization(Session())

    spy.assert_any_call(parent=child_orgunit)


def test_when_publishes_tag_on_root() -> None:
    client = boto3.client("organizations")
    root = client.list_roots()["Roots"][0]
    tag: TagTypeDef = {"Key": "RootTag", "Value": "RootValue"}
    client.tag_resource(ResourceId=root["Id"], Tags=[tag])

    spy = Mock()
    pub.subscribe(spy, "tag")

    crawl_organization(Session())

    spy.assert_called_once_with(resource=root, tag=tag)


def test_publishes_tag_on_orgunit() -> None:
    client = boto3.client("organizations")
    root = client.list_roots()["Roots"][0]
    orgunit = OrgUnit.from_boto3(
        client.create_organizational_unit(ParentId=root["Id"], Name="OU1")["OrganizationalUnit"]
    )
    tag: TagTypeDef = {"Key": "OrgunitTag", "Value": "OrgunitValue"}
    client.tag_resource(ResourceId=orgunit.id, Tags=[tag])

    spy = Mock()
    pub.subscribe(spy, "tag")

    crawl_organization(Session())

    spy.assert_called_once_with(resource=orgunit, tag=tag)


def test_publishes_tag_on_account() -> None:
    client = boto3.client("organizations")
    request = client.create_account(AccountName="Account1", Email="1@aws.com")["CreateAccountStatus"]
    account = Account.from_boto3(client.describe_account(AccountId=request["AccountId"])["Account"])
    tag: TagTypeDef = {"Key": "AccountTag", "Value": "AccountValue"}
    client.tag_resource(ResourceId=account.id, Tags=[tag])

    spy = Mock()
    pub.subscribe(spy, "tag")

    crawl_organization(Session())

    spy.assert_called_once_with(resource=account, tag=tag)


def test_when_resource_has_two_tags_publishes_twice() -> None:
    client = boto3.client("organizations")
    root = client.list_roots()["Roots"][0]
    tag1: TagTypeDef = {"Key": "RootTag1", "Value": "RootValue1"}
    tag2: TagTypeDef = {"Key": "RootTag2", "Value": "RootValue2"}
    client.tag_resource(ResourceId=root["Id"], Tags=[tag1, tag2])

    spy = Mock()
    pub.subscribe(spy, "tag")

    crawl_organization(Session())

    spy.assert_any_call(resource=root, tag=tag1)
    spy.assert_any_call(resource=root, tag=tag2)


def test_raises_organization_error_on_client_error(mocker: MockerFixture) -> None:
    def list_roots(*args: Any, **kwargs: Any) -> None:
        raise ClientError(
            {"Error": {"Message": "broken!", "Code": "OhNo"}}, "list_roots"
        )

    mocker.patch(
        "moto.organizations.models.OrganizationsBackend.list_roots",
        list_roots,
    )

    with raises(OrganizationError) as exc:
        crawl_organization(Session())
    assert type(exc.value.__cause__) == ClientError
