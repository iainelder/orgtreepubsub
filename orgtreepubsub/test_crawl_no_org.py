import pytest
from .type_defs import OrganizationDoesNotExistError
from .orgtreepubsub import OrgCrawler
from boto3.session import Session


def test_raises_error() -> None:
    with pytest.raises(OrganizationDoesNotExistError):
        crawler = OrgCrawler.top_down_tree_and_tags(Session())
        crawler.crawl()
