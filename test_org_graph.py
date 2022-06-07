from pytest import raises
from boto3 import Session
from org_graph import get_org_graph
from type_defs import OrganizationDoesNotExistError


def test_when_org_does_not_exist_raises_error(mock_session: Session) -> None:
    with raises(OrganizationDoesNotExistError):
        get_org_graph(mock_session)
