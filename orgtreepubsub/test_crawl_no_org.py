import pytest
from .type_defs import OrganizationDoesNotExistError
from .orgtreepubsub import OrgCrawler
from boto3.session import Session


def test_publish_organization_raises_error() -> None:
    with pytest.raises(OrganizationDoesNotExistError):
        crawler = OrgCrawler(Session())
        crawler.init = crawler.publish_organization
        crawler.crawl(max_workers=1)

# Don't bother checking that any of the other publish methods fail until the
# moto model behaves more like the real Organizations service.
@pytest.mark.xfail(reason="moto's organization model doesn't return an error.")
def test_publish_roots_raises_error() -> None:
    with pytest.raises(OrganizationDoesNotExistError):
        crawler = OrgCrawler(Session())
        crawler.init = crawler.publish_roots
        crawler.crawl(max_workers=1)
