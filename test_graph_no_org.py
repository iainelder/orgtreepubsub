import pytest
from org_graph import snapshot_org
from type_defs import OrganizationDoesNotExistError
from boto3.session import Session


def test_when_org_does_not_exist_raises_error() -> None:
    with pytest.raises(OrganizationDoesNotExistError):
        snapshot_org(Session())
