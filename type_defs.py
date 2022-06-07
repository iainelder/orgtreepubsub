from typing import Union

from mypy_boto3_organizations.client import OrganizationsClient
from mypy_boto3_organizations.type_defs import (
    OrganizationTypeDef,
    RootTypeDef,
    OrganizationalUnitTypeDef,
    AccountTypeDef,
    TagTypeDef,
)

Account = AccountTypeDef
Org = OrganizationTypeDef
OrgUnit = OrganizationalUnitTypeDef
Root = RootTypeDef
Tag = TagTypeDef

Parent = Union[Root, OrgUnit]
Resource = Union[Account, OrgUnit, Root]

OrgClient = OrganizationsClient


class OrganizationError(Exception):
    """Main exception class."""
    pass


class OrganizationDoesNotExistError(OrganizationError):
    """Raised when the host account is not in an organization."""
    pass
