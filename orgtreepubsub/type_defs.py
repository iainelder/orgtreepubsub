# The Organizations data model say "Required: No" for properties that always exist,
# so the boto3 TypedDict sets NotRequired for the corresponding dict keys.
# pyright: reportTypedDictNotRequiredAccess=false

from dataclasses import dataclass
from datetime import datetime

from typing import Literal, Self

from mypy_boto3_organizations.type_defs import (
    OrganizationTypeDef,
    RootTypeDef,
    OrganizationalUnitTypeDef,
    AccountTypeDef,
    TagTypeDef,
    PolicyTypeSummaryTypeDef,
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


@dataclass
class OrgUnit:

    id: str
    arn: str
    name: str

    @classmethod
    def from_boto3(cls, account: OrganizationalUnitTypeDef) -> Self:
        return cls(
            id=account["Id"],
            arn=account["Arn"],
            name=account["Name"],
        )

PolicyType = Literal[
    "AISERVICES_OPT_OUT_POLICY", "BACKUP_POLICY", "SERVICE_CONTROL_POLICY", "TAG_POLICY"
]
PolicyStatus = Literal["ENABLED", "PENDING_DISABLE", "PENDING_ENABLE"]


@dataclass
class PolicyTypeSummary:

    type: PolicyType
    status: PolicyStatus

    @classmethod
    def from_boto3(cls, policy_type_summary: PolicyTypeSummaryTypeDef) -> Self:
        return cls(
            type=policy_type_summary["Type"],
            status=policy_type_summary["Status"],
        )


@dataclass
class Root:

    id: str
    arn: str
    name: str
    policy_types: list[PolicyTypeSummary]

    @classmethod
    def from_boto3(cls, root: RootTypeDef) -> Self:
        return cls(
            id=root["Id"],
            arn=root["Arn"],
            name=root["Name"],
            policy_types=[PolicyTypeSummary.from_boto3(p) for p in root["PolicyTypes"]]
        )

FeatureSet = Literal["ALL", "CONSOLIDATED_BILLING"]

@dataclass
class Organization:

    # The API Organization data type deprecated the AvailablePolicyTypes field.
    # https://docs.aws.amazon.com/organizations/latest/APIReference/API_Organization.html
    id: str
    arn: str
    feature_set: FeatureSet
    master_account_arn: str
    master_account_id: str
    master_account_email: str

    @classmethod
    def from_boto3(cls, org: OrganizationTypeDef) -> Self:
        return cls(
            id=org["Id"],
            arn=org["Arn"],
            feature_set=org["FeatureSet"],
            master_account_arn=org["MasterAccountArn"],
            master_account_id=org["MasterAccountId"],
            master_account_email=org["MasterAccountEmail"],
        )

Org = Organization

@dataclass
class Tag:

    key: str
    value: str

    @classmethod
    def from_boto3(cls, tag: TagTypeDef) -> Self:
        return cls(
            key=tag["Key"],
            value=tag["Value"],
        )


Child = OrgUnit|Account
Parent = Root|OrgUnit
Resource = Account|OrgUnit|Root


class OrganizationError(Exception):
    """Main exception class."""
    pass


class OrganizationDoesNotExistError(OrganizationError):
    """Raised when the host account is not in an organization."""
    pass
