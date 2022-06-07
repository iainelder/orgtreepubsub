import pytest
from typing import Iterator
from boto3 import Session
from moto import mock_sts, mock_organizations  # type: ignore[import]


@pytest.fixture()
def mock_session() -> Iterator[Session]:
    """Returns a session with mock AWS services."""
    with mock_sts(), mock_organizations():
        yield Session()
