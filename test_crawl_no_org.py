import pytest
from type_defs import OrganizationDoesNotExistError
from orgtreepubsub import crawl_organization
from boto3.session import Session


def test_raises_error() -> None:
    with pytest.raises(OrganizationDoesNotExistError):
        crawl_organization(Session())
