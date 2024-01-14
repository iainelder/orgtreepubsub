import pytest
from boto3 import Session
import boto3
from org_graph import snapshot_org, Account, OrgUnit


@pytest.fixture(autouse=True)
def new_org() -> None:
    boto3.client("organizations").create_organization(FeatureSet="ALL")


def test_new_org_has_mgmt_account_property() -> None:
    client = boto3.client("organizations")
    org_desc = client.describe_organization()["Organization"]
    mgmt_desc = client.describe_account(AccountId=org_desc["MasterAccountId"])["Account"]

    graph = snapshot_org(Session())
    assert graph.management_account == Account.from_boto3(mgmt_desc)


def test_new_org_has_organization_id_property() -> None:
    client = boto3.client("organizations")
    org_desc = client.describe_organization()["Organization"]

    graph = snapshot_org(Session())
    assert graph.organization_id == org_desc["Id"]


def test_new_org_has_root_property() -> None:
    client = boto3.client("organizations")
    root_desc = client.list_roots()["Roots"][0]

    graph = snapshot_org(Session())
    assert graph.root.id == root_desc["Id"]
    assert graph.root.arn == root_desc["Arn"]
    assert graph.root.name == root_desc["Name"]


def test_new_org_has_mgmt_account_via_account() -> None:
    client = boto3.client("organizations")
    org_desc = client.describe_organization()["Organization"]
    mgmt_desc = client.describe_account(AccountId=org_desc["MasterAccountId"])["Account"]

    graph = snapshot_org(Session())
    assert graph.account(id=org_desc["MasterAccountId"]) == Account.from_boto3(mgmt_desc)


def test_has_tagged_root() -> None:
    client = boto3.client("organizations")
    root = client.list_roots()["Roots"][0]
    client.tag_resource(ResourceId=root["Id"], Tags=[{"Key": "Key1", "Value": "Value1"}])

    graph = snapshot_org(Session())
    assert graph.root.tags["Key1"] == "Value1"


def test_has_orgunit() -> None:
    client = boto3.client("organizations")
    root = client.list_roots()["Roots"][0]
    orgunit = client.create_organizational_unit(ParentId=root["Id"], Name="OU1")["OrganizationalUnit"]

    graph = snapshot_org(Session())
    assert graph.orgunit(name="OU1") == OrgUnit.from_boto3(orgunit)


def test_has_tagged_orgunit() -> None:
    client = boto3.client("organizations")
    root = client.list_roots()["Roots"][0]
    client.create_organizational_unit(ParentId=root["Id"], Name="OU1", Tags=[{"Key": "Key1", "Value": "Value1"}])

    graph = snapshot_org(Session())
    assert graph.orgunit(name="OU1").tags["Key1"] == "Value1"
