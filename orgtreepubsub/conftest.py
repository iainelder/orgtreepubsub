import pytest
from moto import mock_organizations, mock_sts  # type: ignore[import]
from typing import Iterable


@pytest.fixture(autouse=True)
def mock_all_aws_services() -> Iterable[None]:
    """Mock all services for AWS sessions."""
    with mock_organizations(), mock_sts():
        yield
