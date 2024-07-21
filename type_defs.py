# The Organizations data model say "Required: No" for properties that always exist,
# so the boto3 TypedDict sets NotRequired for the corresponding dict keys.
# pyright: reportTypedDictNotRequiredAccess=false

from dataclasses import dataclass
from datetime import datetime

from typing import Union, Literal, Self

from mypy_boto3_organizations.client import OrganizationsClient
from mypy_boto3_organizations.type_defs import (
    OrganizationTypeDef,
    RootTypeDef,
    OrganizationalUnitTypeDef,
    AccountTypeDef,
    TagTypeDef,
)

AccountJoinedMethod = Literal["CREATED", "INVITED"]
AccountStatus = Literal["ACTIVE", "PENDING_CLOSURE", "SUSPENDED"]

@dataclass
class Account:

    id: str
    arn: str
    email: str
    name: str
    status: AccountStatus
    joined_method:  AccountJoinedMethod
    joined_timestamp: datetime

    @classmethod
    def from_boto3(cls, account: AccountTypeDef) -> Self:
        return cls(
            id=account["Id"],
            arn=account["Arn"],
            email=account["Email"],
            name=account["Name"],
            status=account["Status"],
            joined_method=account["JoinedMethod"],
            joined_timestamp=account["JoinedTimestamp"],
        )

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
