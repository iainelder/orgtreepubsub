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
    assert graph.management_account == mgmt_desc


def test_new_org_has_organization_id_property() -> None:
    client = boto3.client("organizations")
    org_desc = client.describe_organization()["Organization"]

    graph = snapshot_org(Session())
    assert graph.organization_id == org_desc["Id"]


def test_new_org_has_root_property() -> None:
    client = boto3.client("organizations")
    root_desc = client.list_roots()["Roots"][0]

    graph = snapshot_org(Session())
    assert graph.root == root_desc


def test_new_org_has_mgmt_account_via_ac() -> None:
    client = boto3.client("organizations")
    org_desc = client.describe_organization()["Organization"]
    mgmt_desc = client.describe_account(AccountId=org_desc["MasterAccountId"])["Account"]

    graph = snapshot_org(Session())
    assert graph.ac(org_desc["MasterAccountId"]) == mgmt_desc
