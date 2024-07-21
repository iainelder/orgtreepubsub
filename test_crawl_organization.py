# The tests use boto3 TypedDict access. See type_defs.py for why to suppress.
# pyright: reportTypedDictNotRequiredAccess=false

# For boto3.client.
# pyright: reportUnknownMemberType=false

from typing import Any
from boto3 import Session
import boto3
from mypy_boto3_organizations.type_defs import TagTypeDef
from type_defs import Account, OrgUnit, Root, Org, Tag, OrganizationError
from orgtreepubsub import OrgCrawler
from pytest import raises
from unittest.mock import Mock
from botocore.exceptions import ClientError
from pytest_mock import MockerFixture
import pytest
import topics

@pytest.fixture(autouse=True)
def new_org() -> None:
    boto3.client("organizations").create_organization(FeatureSet="ALL")


def test_in_new_org_publishes_organization() -> None:
    spy = Mock()
    topics.organization.connect(spy)

    crawler = OrgCrawler(Session())
    crawler.crawl()

    client = boto3.client("organizations")
    org = Org.from_boto3(client.describe_organization()["Organization"])
    spy.assert_called_once_with(crawler, org=org)


def test_in_new_org_publishes_root_as_resource() -> None:
    spy = Mock()
    topics.root.connect(spy)

    crawler = OrgCrawler(Session())
    crawler.crawl()

    client = boto3.client("organizations")
    org = Org.from_boto3(client.describe_organization()["Organization"])
    root = Root.from_boto3(client.list_roots()["Roots"][0])
    spy.assert_called_once_with(crawler, org=org, resource=root)


def test_in_new_org_publishes_root_as_parent() -> None:
    spy = Mock()
    topics.parent.connect(spy)

    crawler = OrgCrawler(Session())
    crawler.crawl()

    client = boto3.client("organizations")
    root = Root.from_boto3(client.list_roots()["Roots"][0])
    spy.assert_called_once_with(crawler, parent=root)


def test_in_new_org_publishes_mgmt_account() -> None:
    spy = Mock()
    topics.account.connect(spy)

    crawler = OrgCrawler(Session())
    crawler.crawl()

    client = boto3.client("organizations")
    root = Root.from_boto3(client.list_roots()["Roots"][0])
    mgmt_account = Account.from_boto3(client.list_accounts()["Accounts"][0])
    spy.assert_called_once_with(crawler, parent=root, resource=mgmt_account)


def test_in_new_org_publishes_no_orgunit() -> None:
    spy = Mock()
    topics.orgunit.connect(spy)

    OrgCrawler(Session()).crawl()

    spy.assert_not_called()


def test_in_new_org_publishes_no_tag() -> None:
    spy = Mock()
    topics.tag.connect(spy)

    OrgCrawler(Session()).crawl()

    spy.assert_not_called()


def test_publishes_empty_orgunit_as_resource() -> None:
    client = boto3.client("organizations")
    root = Root.from_boto3(client.list_roots()["Roots"][0])
    orgunit = OrgUnit.from_boto3(
        client.create_organizational_unit(ParentId=root.id, Name="OU1")["OrganizationalUnit"]
    )

    spy = Mock()
    topics.orgunit.connect(spy)

    crawler = OrgCrawler(Session())
    crawler.crawl()

    spy.assert_called_once_with(crawler, parent=root, resource=orgunit)


def test_publishes_empty_orgunit_as_parent() -> None:
    client = boto3.client("organizations")
    root = client.list_roots()["Roots"][0]
    orgunit = OrgUnit.from_boto3(
        client.create_organizational_unit(ParentId=root["Id"], Name="OU1")["OrganizationalUnit"]
    )

    spy = Mock()
    topics.parent.connect(spy)

    crawler = OrgCrawler(Session())
    crawler.crawl()

    spy.assert_any_call(crawler, parent=orgunit)


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
    topics.account.connect(spy)

    crawler = OrgCrawler(Session())
    crawler.crawl()

    spy.assert_any_call(crawler, parent=orgunit, resource=child_account)


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
    topics.orgunit.connect(spy)

    crawler = OrgCrawler(Session())
    crawler.crawl()

    spy.assert_any_call(crawler, parent=parent_orgunit, resource=child_orgunit)


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
    topics.parent.connect(spy)

    crawler = OrgCrawler(Session())
    crawler.crawl()

    spy.assert_any_call(crawler, parent=child_orgunit)


def test_publishes_tag_on_root() -> None:
    client = boto3.client("organizations")
    root = Root.from_boto3(client.list_roots()["Roots"][0])
    boto3_tag: TagTypeDef = {"Key": "RootTag", "Value": "RootValue"}
    client.tag_resource(ResourceId=root.id, Tags=[boto3_tag])
    lib_tag = Tag.from_boto3(boto3_tag)

    spy = Mock()
    topics.tag.connect(spy)

    crawler = OrgCrawler(Session())
    crawler.crawl()

    spy.assert_called_once_with(crawler, resource=root, tag=lib_tag)


def test_publishes_tag_on_orgunit() -> None:
    client = boto3.client("organizations")
    root = client.list_roots()["Roots"][0]
    orgunit = OrgUnit.from_boto3(
        client.create_organizational_unit(ParentId=root["Id"], Name="OU1")["OrganizationalUnit"]
    )
    boto3_tag: TagTypeDef = {"Key": "OrgunitTag", "Value": "OrgunitValue"}
    client.tag_resource(ResourceId=orgunit.id, Tags=[boto3_tag])

    spy = Mock()
    topics.tag.connect(spy)

    crawler = OrgCrawler(Session())
    crawler.crawl()

    lib_tag = Tag.from_boto3(boto3_tag)
    spy.assert_called_once_with(crawler, resource=orgunit, tag=lib_tag)


def test_publishes_tag_on_account() -> None:
    client = boto3.client("organizations")
    request = client.create_account(AccountName="Account1", Email="1@aws.com")["CreateAccountStatus"]
    account = Account.from_boto3(client.describe_account(AccountId=request["AccountId"])["Account"])
    boto3_tag: TagTypeDef = {"Key": "AccountTag", "Value": "AccountValue"}
    client.tag_resource(ResourceId=account.id, Tags=[boto3_tag])

    spy = Mock()
    topics.tag.connect(spy)

    crawler = OrgCrawler(Session())
    crawler.crawl()

    lib_tag = Tag.from_boto3(boto3_tag)
    spy.assert_called_once_with(crawler, resource=account, tag=lib_tag)


def test_when_resource_has_two_tags_publishes_twice() -> None:
    client = boto3.client("organizations")
    root = Root.from_boto3(client.list_roots()["Roots"][0])
    boto3_tag1: TagTypeDef = {"Key": "RootTag1", "Value": "RootValue1"}
    boto3_tag2: TagTypeDef = {"Key": "RootTag2", "Value": "RootValue2"}
    client.tag_resource(ResourceId=root.id, Tags=[boto3_tag1, boto3_tag2])

    spy = Mock()
    topics.tag.connect(spy)

    crawler = OrgCrawler(Session())
    crawler.crawl()

    lib_tag1 = Tag.from_boto3(boto3_tag1)
    lib_tag2 = Tag.from_boto3(boto3_tag2)
    spy.assert_any_call(crawler, resource=root, tag=lib_tag1)
    spy.assert_any_call(crawler, resource=root, tag=lib_tag2)


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
        OrgCrawler(Session()).crawl()
    assert type(exc.value.__cause__) == ClientError
