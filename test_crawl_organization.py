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


def test_when_org_is_new_crawl_publishes_no_orgunit(mock_session: Session) -> None:
    client = mock_session.client("organizations")
    client.create_organization(FeatureSet="ALL")

    spy = Mock()
    pub.subscribe(spy, "organizational_unit")
    
    crawl_organization(mock_session)

    spy.assert_not_called()


def test_when_org_is_new_crawl_publishes_no_tag(mock_session: Session) -> None:
    client = mock_session.client("organizations")
    client.create_organization(FeatureSet="ALL")

    spy = Mock()
    pub.subscribe(spy, "tag")
    
    crawl_organization(mock_session)

    spy.assert_not_called()


def test_when_org_has_empty_orgunit_crawl_publishes_orgunit_as_resource(mock_session: Session) -> None:
    client = mock_session.client("organizations")
    client.create_organization(FeatureSet="ALL")
    root = client.list_roots()["Roots"][0]
    orgunit = client.create_organizational_unit(ParentId=root["Id"], Name="OU1")["OrganizationalUnit"]

    spy = Mock()
    pub.subscribe(spy, "organizational_unit")
    
    crawl_organization(mock_session)

    spy.assert_called_once_with(parent=root, resource=orgunit)


def test_when_org_has_empty_orgunit_crawl_publishes_orgunit_as_parent(mock_session: Session) -> None:
    client = mock_session.client("organizations")
    client.create_organization(FeatureSet="ALL")
    root = client.list_roots()["Roots"][0]
    orgunit = client.create_organizational_unit(ParentId=root["Id"], Name="OU1")["OrganizationalUnit"]

    spy = Mock()
    pub.subscribe(spy, "parent")
    
    crawl_organization(mock_session)

    spy.assert_any_call(parent=orgunit)


def test_when_orgunit_parents_account_crawl_publishes_account_as_resource(mock_session: Session) -> None:
    client = mock_session.client("organizations")
    client.create_organization(FeatureSet="ALL")
    root = client.list_roots()["Roots"][0]
    orgunit = client.create_organizational_unit(ParentId=root["Id"], Name="OU1")["OrganizationalUnit"]
    child_request = client.create_account(AccountName="Account1", Email="1@aws.com")["CreateAccountStatus"]
    child_account = client.describe_account(AccountId=child_request["AccountId"])["Account"]
    client.move_account(AccountId=child_account["Id"], SourceParentId=root["Id"], DestinationParentId=orgunit["Id"])

    spy = Mock()
    pub.subscribe(spy, "account")

    crawl_organization(mock_session)

    spy.assert_any_call(parent=orgunit, resource=child_account)


def test_when_orgunit_parents_orgunit_crawl_publishes_child_orgunit_as_resource(mock_session: Session) -> None:
    client = mock_session.client("organizations")
    client.create_organization(FeatureSet="ALL")
    root = client.list_roots()["Roots"][0]
    parent_orgunit = client.create_organizational_unit(ParentId=root["Id"], Name="OU1")["OrganizationalUnit"]
    child_orgunit = client.create_organizational_unit(ParentId=parent_orgunit["Id"], Name="OU2")["OrganizationalUnit"]

    spy = Mock()
    pub.subscribe(spy, "organizational_unit")

    crawl_organization(mock_session)

    spy.assert_any_call(parent=parent_orgunit, resource=child_orgunit)


def test_when_orgunit_parents_orgunit_crawl_publishes_child_orgunit_as_parent(mock_session: Session) -> None:
    client = mock_session.client("organizations")
    client.create_organization(FeatureSet="ALL")
    root = client.list_roots()["Roots"][0]
    parent_orgunit = client.create_organizational_unit(ParentId=root["Id"], Name="OU1")["OrganizationalUnit"]
    child_orgunit = client.create_organizational_unit(ParentId=parent_orgunit["Id"], Name="OU2")["OrganizationalUnit"]

    spy = Mock()
    pub.subscribe(spy, "parent")

    crawl_organization(mock_session)

    spy.assert_any_call(parent=child_orgunit)


def test_when_root_has_tag_crawl_publishes_tag(mock_session: Session) -> None:
    client = mock_session.client("organizations")
    client.create_organization(FeatureSet="ALL")
    root = client.list_roots()["Roots"][0]
    tag = {"Key": "RootTag", "Value": "RootValue"}
    client.tag_resource(ResourceId=root["Id"], Tags=[tag])

    spy = Mock()
    pub.subscribe(spy, "tag")

    crawl_organization(mock_session)

    spy.assert_called_once_with(resource=root, tag=tag)


def test_when_orgunit_has_tag_crawl_publishes_tag(mock_session: Session) -> None:
    client = mock_session.client("organizations")
    client.create_organization(FeatureSet="ALL")
    root = client.list_roots()["Roots"][0]
    orgunit = client.create_organizational_unit(ParentId=root["Id"], Name="OU1")["OrganizationalUnit"]
    tag = {"Key": "OrgunitTag", "Value": "OrgunitValue"}
    client.tag_resource(ResourceId=orgunit["Id"], Tags=[tag])

    spy = Mock()
    pub.subscribe(spy, "tag")

    crawl_organization(mock_session)

    spy.assert_called_once_with(resource=orgunit, tag=tag)


def test_when_account_has_tag_crawl_publishes_tag(mock_session: Session) -> None:
    client = mock_session.client("organizations")
    client.create_organization(FeatureSet="ALL")
    request = client.create_account(AccountName="Account1", Email="1@aws.com")["CreateAccountStatus"]
    account = client.describe_account(AccountId=request["AccountId"])["Account"]
    tag = {"Key": "AccountTag", "Value": "AccountValue"}
    client.tag_resource(ResourceId=account["Id"], Tags=[tag])

    spy = Mock()
    pub.subscribe(spy, "tag")

    crawl_organization(mock_session)

    spy.assert_called_once_with(resource=account, tag=tag)


def test_when_resource_has_two_tags_crawl_publishes_twice(mock_session: Session) -> None:
    client = mock_session.client("organizations")
    client.create_organization(FeatureSet="ALL")
    root = client.list_roots()["Roots"][0]
    tag1 = {"Key": "RootTag1", "Value": "RootValue1"}
    tag2 = {"Key": "RootTag2", "Value": "RootValue2"}
    client.tag_resource(ResourceId=root["Id"], Tags=[tag1, tag2])

    spy = Mock()
    pub.subscribe(spy, "tag")

    crawl_organization(mock_session)

    spy.assert_any_call(resource=root, tag=tag1)
    spy.assert_any_call(resource=root, tag=tag2)
