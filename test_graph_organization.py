# pyright: reportTypedDictNotRequiredAccess=false, reportUnknownMemberType=false

import pytest
from boto3 import Session
import boto3
from org_graph import snapshot_org


@pytest.fixture(autouse=True)
def new_org() -> None:
    boto3.client("organizations").create_organization(FeatureSet="ALL")


def test_new_org_has_mgmt_account_property() -> None:
    client = boto3.client("organizations")
    org_desc = client.describe_organization()["Organization"]
    mgmt_desc = client.describe_account(AccountId=org_desc["MasterAccountId"])["Account"]

    graph = snapshot_org(Session())
    assert all([
        graph.management_account.id == mgmt_desc["Id"],
        graph.management_account.arn == mgmt_desc["Arn"],
        graph.management_account.name == mgmt_desc["Name"],
        graph.management_account.email == mgmt_desc["Email"],
        graph.management_account.joined_method == mgmt_desc["JoinedMethod"],
        graph.management_account.joined_timestamp == mgmt_desc["JoinedTimestamp"],
    ])


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
    account = graph.account(id=org_desc["MasterAccountId"])
    assert all([
        account.id == mgmt_desc["Id"],
        account.arn == mgmt_desc["Arn"],
        account.name == mgmt_desc["Name"],
        account.email == mgmt_desc["Email"],
        account.joined_method == mgmt_desc["JoinedMethod"],
        account.joined_timestamp == mgmt_desc["JoinedTimestamp"],
    ])


def test_has_tagged_root() -> None:
    client = boto3.client("organizations")
    root = client.list_roots()["Roots"][0]
    client.tag_resource(ResourceId=root["Id"], Tags=[{"Key": "Key1", "Value": "Value1"}])

    graph = snapshot_org(Session())
    assert graph.root.tags["Key1"] == "Value1"


def test_has_orgunit() -> None:
    client = boto3.client("organizations")
    root = client.list_roots()["Roots"][0]
    orgunit_desc = client.create_organizational_unit(ParentId=root["Id"], Name="OU1")["OrganizationalUnit"]

    graph = snapshot_org(Session())
    orgunit = graph.orgunit(name="OU1")
    assert all([
        orgunit.id == orgunit_desc["Id"],
        orgunit.arn == orgunit_desc["Arn"],
        orgunit.name == orgunit_desc["Name"],
    ])


def test_has_tagged_orgunit() -> None:
    client = boto3.client("organizations")
    root = client.list_roots()["Roots"][0]
    client.create_organizational_unit(ParentId=root["Id"], Name="OU1", Tags=[{"Key": "Key1", "Value": "Value1"}])

    graph = snapshot_org(Session())
    assert graph.orgunit(name="OU1").tags["Key1"] == "Value1"
