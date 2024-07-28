# The tests use boto3 TypedDict access. See type_defs.py for why to suppress.
# pyright: reportTypedDictNotRequiredAccess=false

from typing import Any
from boto3 import Session
import boto3
from mypy_boto3_organizations import OrganizationsClient
from mypy_boto3_organizations.type_defs import TagTypeDef
from .type_defs import Account, OrgUnit, Root, Org, Tag, OrganizationError
from .orgtreepubsub import OrgCrawler
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
    crawler = OrgCrawler(Session())
    crawler.init = crawler.publish_organization
    crawler.on_organization.connect(spy)

    crawler.crawl()

    client: OrganizationsClient = boto3.client("organizations")
    org = Org.from_boto3(client.describe_organization()["Organization"])
    spy.assert_called_once_with(crawler, org=org)


def test_in_new_org_publishes_root_resource() -> None:
    spy = Mock()
    crawler = OrgCrawler(Session())
    crawler.init = crawler.publish_roots
    crawler.on_root.connect(spy)

    crawler.crawl()

    client: OrganizationsClient = boto3.client("organizations")
    root = Root.from_boto3(client.list_roots()["Roots"][0])
    spy.assert_called_once_with(crawler, resource=root)


def test_in_new_org_publishes_mgmt_account_resource() -> None:
    spy = Mock()
    crawler = OrgCrawler(Session())
    crawler.init = crawler.publish_roots
    crawler.on_root.connect(OrgCrawler.publish_accounts_under_resource)
    crawler.on_account.connect(spy)

    crawler.crawl()

    client: OrganizationsClient = boto3.client("organizations")
    mgmt_account = Account.from_boto3(client.list_accounts()["Accounts"][0])
    spy.assert_called_once_with(crawler, resource=mgmt_account)


def test_in_new_org_publishes_mgmt_account_parentage() -> None:
    spy = Mock()
    crawler = OrgCrawler(Session())
    crawler.init = crawler.publish_roots
    crawler.on_root.connect(OrgCrawler.publish_accounts_under_resource)
    crawler.on_parentage.connect(spy)

    crawler.crawl()

    client: OrganizationsClient = boto3.client("organizations")
    root = Root.from_boto3(client.list_roots()["Roots"][0])
    mgmt_account = Account.from_boto3(client.list_accounts()["Accounts"][0])
    spy.assert_any_call(crawler, parent=root, child=mgmt_account)


def test_publishes_empty_orgunit_resource() -> None:
    client: OrganizationsClient = boto3.client("organizations")
    root = Root.from_boto3(client.list_roots()["Roots"][0])
    orgunit = OrgUnit.from_boto3(
        client.create_organizational_unit(ParentId=root.id, Name="OU1")["OrganizationalUnit"]
    )

    spy = Mock()
    crawler = OrgCrawler(Session())
    crawler.init = crawler.publish_roots
    crawler.on_root.connect(OrgCrawler.publish_orgunits_under_resource)
    crawler.on_orgunit.connect(spy)

    crawler.crawl()

    spy.assert_called_once_with(crawler, resource=orgunit)


def test_publishes_empty_orgunit_parentage() -> None:
    client: OrganizationsClient = boto3.client("organizations")
    root = Root.from_boto3(client.list_roots()["Roots"][0])
    orgunit = OrgUnit.from_boto3(
        client.create_organizational_unit(ParentId=root.id, Name="OU1")["OrganizationalUnit"]
    )

    spy = Mock()
    crawler = OrgCrawler(Session())
    crawler.init = crawler.publish_roots
    crawler.on_root.connect(OrgCrawler.publish_orgunits_under_resource)
    crawler.on_parentage.connect(spy)

    crawler.crawl()

    spy.assert_any_call(crawler, parent=root, child=orgunit)


def test_when_orgunit_contains_account_crawl_publishes_account_resource() -> None:
    client: OrganizationsClient = boto3.client("organizations")
    root = client.list_roots()["Roots"][0]
    orgunit = OrgUnit.from_boto3(
        client.create_organizational_unit(ParentId=root["Id"], Name="OU1")["OrganizationalUnit"]
    )
    child_request = client.create_account(AccountName="Account1", Email="1@aws.com")["CreateAccountStatus"]
    child_account = Account.from_boto3(client.describe_account(AccountId=child_request["AccountId"])["Account"])
    client.move_account(AccountId=child_account.id, SourceParentId=root["Id"], DestinationParentId=orgunit.id)

    spy = Mock()
    crawler = OrgCrawler(Session())
    crawler.init = crawler.publish_roots
    crawler.on_root.connect(OrgCrawler.publish_orgunits_under_resource)
    crawler.on_orgunit.connect(OrgCrawler.publish_accounts_under_resource)
    crawler.on_account.connect(spy)

    crawler.crawl()

    spy.assert_any_call(crawler, resource=child_account)


def test_when_orgunit_contains_orgunit_crawl_publishes_child_orgunit_resource() -> None:
    client: OrganizationsClient = boto3.client("organizations")
    root = client.list_roots()["Roots"][0]
    parent_orgunit = OrgUnit.from_boto3(
        client.create_organizational_unit(ParentId=root["Id"], Name="OU1")["OrganizationalUnit"]
    )
    child_orgunit = OrgUnit.from_boto3(
        client.create_organizational_unit(ParentId=parent_orgunit.id, Name="OU2")["OrganizationalUnit"]
    )

    spy = Mock()
    crawler = OrgCrawler(Session())
    crawler.init = crawler.publish_roots
    crawler.on_root.connect(OrgCrawler.publish_orgunits_under_resource)
    crawler.on_orgunit.connect(OrgCrawler.publish_orgunits_under_resource)
    crawler.on_orgunit.connect(spy)

    crawler.crawl()

    spy.assert_any_call(crawler, resource=child_orgunit)


def test_when_orgunit_contains_orgunit_crawl_publishes_child_orgunit_parentage() -> None:
    client: OrganizationsClient = boto3.client("organizations")
    root = client.list_roots()["Roots"][0]
    parent_orgunit = OrgUnit.from_boto3(
        client.create_organizational_unit(ParentId=root["Id"], Name="OU1")["OrganizationalUnit"]
    )
    child_orgunit = OrgUnit.from_boto3(
        client.create_organizational_unit(ParentId=parent_orgunit.id, Name="OU2")["OrganizationalUnit"]
    )

    spy = Mock()
    crawler = OrgCrawler(Session())
    crawler.init = crawler.publish_roots
    crawler.on_root.connect(OrgCrawler.publish_orgunits_under_resource)
    crawler.on_orgunit.connect(OrgCrawler.publish_orgunits_under_resource)
    crawler.on_parentage.connect(spy)

    crawler.crawl()

    spy.assert_any_call(crawler, parent=parent_orgunit, child=child_orgunit)


def test_publishes_tag_on_root() -> None:
    client: OrganizationsClient = boto3.client("organizations")
    root = Root.from_boto3(client.list_roots()["Roots"][0])
    boto3_tag: TagTypeDef = {"Key": "RootTag", "Value": "RootValue"}
    client.tag_resource(ResourceId=root.id, Tags=[boto3_tag])
    lib_tag = Tag.from_boto3(boto3_tag)

    spy = Mock()
    crawler = OrgCrawler(Session())
    crawler.init = crawler.publish_roots
    crawler.on_root.connect(OrgCrawler.publish_tags)
    crawler.on_tag.connect(spy)

    crawler.crawl()

    spy.assert_called_once_with(crawler, resource=root, tag=lib_tag)


def test_publishes_tag_on_orgunit() -> None:
    client: OrganizationsClient = boto3.client("organizations")
    root = client.list_roots()["Roots"][0]
    orgunit = OrgUnit.from_boto3(
        client.create_organizational_unit(ParentId=root["Id"], Name="OU1")["OrganizationalUnit"]
    )
    boto3_tag: TagTypeDef = {"Key": "OrgunitTag", "Value": "OrgunitValue"}
    client.tag_resource(ResourceId=orgunit.id, Tags=[boto3_tag])

    spy = Mock()
    crawler = OrgCrawler(Session())
    crawler.init = crawler.publish_roots
    crawler.on_root.connect(OrgCrawler.publish_orgunits_under_resource)
    crawler.on_orgunit.connect(OrgCrawler.publish_tags)
    crawler.on_tag.connect(spy)

    crawler.crawl()

    lib_tag = Tag.from_boto3(boto3_tag)
    spy.assert_called_once_with(crawler, resource=orgunit, tag=lib_tag)


def test_publishes_tag_on_account() -> None:
    client: OrganizationsClient = boto3.client("organizations")
    request = client.create_account(AccountName="Account1", Email="1@aws.com")["CreateAccountStatus"]
    account = Account.from_boto3(client.describe_account(AccountId=request["AccountId"])["Account"])
    boto3_tag: TagTypeDef = {"Key": "AccountTag", "Value": "AccountValue"}
    client.tag_resource(ResourceId=account.id, Tags=[boto3_tag])

    spy = Mock()
    crawler = OrgCrawler(Session())
    crawler.init = crawler.publish_roots
    crawler.on_root.connect(OrgCrawler.publish_accounts_under_resource)
    crawler.on_account.connect(OrgCrawler.publish_tags)
    crawler.on_tag.connect(spy)

    crawler.crawl()

    lib_tag = Tag.from_boto3(boto3_tag)
    spy.assert_called_once_with(crawler, resource=account, tag=lib_tag)


def test_when_resource_has_two_tags_publishes_twice() -> None:
    client: OrganizationsClient = boto3.client("organizations")
    root = Root.from_boto3(client.list_roots()["Roots"][0])
    boto3_tag1: TagTypeDef = {"Key": "RootTag1", "Value": "RootValue1"}
    boto3_tag2: TagTypeDef = {"Key": "RootTag2", "Value": "RootValue2"}
    client.tag_resource(ResourceId=root.id, Tags=[boto3_tag1, boto3_tag2])

    spy = Mock()
    crawler = OrgCrawler(Session())
    crawler.init = crawler.publish_roots
    crawler.on_root.connect(OrgCrawler.publish_tags)
    crawler.on_tag.connect(spy)

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

    crawler = OrgCrawler(Session())
    crawler.init = crawler.publish_roots

    with raises(OrganizationError) as exc:
        crawler.crawl()
    assert type(exc.value.__cause__) == ClientError


def test_crawler_events_are_isolated() -> None:

    spy1 = Mock()
    crawler1 = OrgCrawler(Session())
    crawler1.init = crawler1.publish_organization
    crawler1.on_organization.connect(spy1)

    spy2 = Mock()
    crawler2 = OrgCrawler(Session())
    crawler2.init = crawler2.publish_organization
    crawler2.on_organization.connect(spy2)

    crawler1.crawl()

    assert spy1.called
    assert not spy2.called
