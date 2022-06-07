from pubsub import pub
from boto3 import Session
from botocore.exceptions import ClientError
from orgtreepubsub import crawl_organization
from pytest import raises
from unittest.mock import Mock


def test_when_org_does_not_exist_crawl_raises_error(mock_session: Session) -> None:
    with raises(ClientError) as err:
        crawl_organization(mock_session)
    assert err.value.response['Error']['Code'] == "AWSOrganizationsNotInUseException"


def test_when_org_is_new_crawl_publishes_organization(mock_session: Session) -> None:
    client = mock_session.client("organizations")
    client.create_organization(FeatureSet="ALL")

    spy = Mock()
    pub.subscribe(spy, "organization")
    
    crawl_organization(mock_session)

    org = client.describe_organization()["Organization"]
    spy.assert_called_once_with(org=org)


def test_when_org_is_new_crawl_publishes_root_as_resource(mock_session: Session) -> None:
    client = mock_session.client("organizations")
    client.create_organization(FeatureSet="ALL")

    spy = Mock()
    pub.subscribe(spy, "root")
    
    crawl_organization(mock_session)

    org = client.describe_organization()["Organization"]
    root = client.list_roots()["Roots"][0]
    spy.assert_called_once_with(org=org, resource=root)


def test_when_org_is_new_crawl_publishes_root_as_parent(mock_session: Session) -> None:
    client = mock_session.client("organizations")
    client.create_organization(FeatureSet="ALL")

    spy = Mock()
    pub.subscribe(spy, "parent")
    
    crawl_organization(mock_session)

    root = client.list_roots()["Roots"][0]
    spy.assert_called_once_with(parent=root)


def test_when_org_is_new_crawl_publishes_mgmt_account(mock_session: Session) -> None:
    client = mock_session.client("organizations")
    client.create_organization(FeatureSet="ALL")

    spy = Mock()
    pub.subscribe(spy, "account")
    
    crawl_organization(mock_session)

    root = client.list_roots()["Roots"][0]
    mgmt_account = client.list_accounts()["Accounts"][0]
    spy.assert_called_once_with(parent=root, resource=mgmt_account)
