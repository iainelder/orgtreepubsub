from datetime import datetime
from dataclasses import dataclass, field
from copy import deepcopy
import sys
from typing import Any, BinaryIO, Dict, Iterator, Union, cast
from pubsub import pub  # type: ignore[import]
import networkx as nx  # type: ignore[import]
from boto3 import Session
from orgtreepubsub import crawl_organization

from type_defs import Org, Parent, Resource, Tag
from mypy_boto3_organizations.type_defs import RootTypeDef, AccountTypeDef, OrganizationalUnitTypeDef

# Creating my own data classes instead of exposing the ones generated for mypy is a step in the right direction.
# But using them insidethe graph itself is awkward and complicated.
# TODO: Just use attributes on the nodes internally and construct data classes for a result of queries.
# That should also make it easier to query by tag.
# I need to bring back the "tag:" prefix to make a tag namespace.

@dataclass(frozen=True)
class Root:
    id: str
    arn: str
    name: str
    tags: Dict[str, str] = field(default_factory=dict)

    @staticmethod
    def from_boto3(root: RootTypeDef) -> "Root":
        return Root(id=root["Id"], arn=root["Arn"], name=root["Name"])

    def add_tag(self, tag: Tag) -> None:
        self.tags[tag["Key"]] = tag["Value"]


@dataclass(frozen=True)
class Account:
    id: str
    arn: str
    name: str
    email: str
    joined_timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)

    @staticmethod
    def from_boto3(account: AccountTypeDef) -> "Account":
        return Account(
            id=account["Id"],
            arn=account["Arn"],
            name=account["Name"],
            email=account["Email"],
            joined_timestamp=account["JoinedTimestamp"]
        )

    def add_tag(self, tag: Tag) -> None:
        self.tags[tag["Key"]] = tag["Value"]


@dataclass(frozen=True)
class OrgUnit:
    id: str
    arn: str
    name: str
    tags: Dict[str, str] = field(default_factory=dict)

    @staticmethod
    def from_boto3(account: OrganizationalUnitTypeDef) -> "OrgUnit":
        return OrgUnit(
            id=account["Id"],
            arn=account["Arn"],
            name=account["Name"],
        )

    def add_tag(self, tag: Tag) -> None:
        self.tags[tag["Key"]] = tag["Value"]


class OrgGraph:

    def __init__(self, graph: nx.DiGraph) -> None:
        """Don't use this initializer. Instead use `snapshot_org`."""
        self._graph = graph

    @property
    def management_account(self) -> Account:
        for account in nx.get_node_attributes(self._graph, "account").values():
            if account.id == self._management_account_id:
                return cast(Account, account)
        raise AssertionError("missed management account")

    @property
    def root(self) -> Root:
        for root in nx.get_node_attributes(self._graph, "root").values():
            return cast(Root, root)
        raise AssertionError("missed root")

    def _set_org_metadata(self, org: Org) -> None:
        self._management_account_id = org["MasterAccountId"]
        self.organization_id = org["Id"]

    def account(self, id: str) -> Account:
        for account in nx.get_node_attributes(self._graph, "account").values():
            if account.id == id:
                return cast(Account, account)
        raise ValueError(id)

    def orgunit(self, name: str) -> OrgUnit:
        for orgunit in nx.get_node_attributes(self._graph, "organizational_unit").values():
            if orgunit.name == name:
                return cast(OrgUnit, orgunit)
        raise ValueError(id)

    def add_root(self, resource: RootTypeDef, org: Org) -> None:
        self._graph.add_node(resource["Id"], root=Root.from_boto3(resource))
        self._graph.add_edge(org["Id"], resource["Id"])

    def add_organizational_unit(self, resource: OrganizationalUnitTypeDef, parent: Parent) -> None:
        self._graph.add_node(resource["Id"], organizational_unit=OrgUnit.from_boto3(resource))
        self._graph.add_edge(parent["Id"], resource["Id"])

    def add_account(self, resource: AccountTypeDef, parent: Parent) -> None:
        self._graph.add_node(resource["Id"], account=Account.from_boto3(resource))
        self._graph.add_edge(parent["Id"], resource["Id"])

    def add_tag(self, resource: Resource, tag: Tag) -> None:
        for resource_ in self._graph.nodes[resource["Id"]].values():
            resource_.add_tag(tag)

def snapshot_org(session: Session) -> OrgGraph:
    internal_graph = nx.DiGraph()
    org_model = OrgGraph(internal_graph)

    pub.subscribe(org_model._set_org_metadata, "organization")
    pub.subscribe(org_model.add_root, "root")
    pub.subscribe(org_model.add_organizational_unit, "organizational_unit")
    pub.subscribe(org_model.add_account, "account")
    pub.subscribe(org_model.add_tag, "tag")

    crawl_organization(session)

    return org_model


# ---
# Older impelementation below.
# ---


# NetworkX accepts a file handle for I/O. This is useful for writing to stdout.
# It also accepts a str path to a file and manages the file handle itself. This
# is convenient for reading.
File = Union[BinaryIO, str]




def get_org_graph(session: Session) -> nx.Graph:

    graph = nx.DiGraph()

    pub.subscribe(add_organization, "organization", graph=graph)
    pub.subscribe(add_root, "root", graph=graph)
    pub.subscribe(add_organizational_unit, "organizational_unit", graph=graph)
    pub.subscribe(add_account, "account", graph=graph)
    pub.subscribe(add_tag, "tag", graph=graph)

    crawl_organization(session)

    return graph


def add_organization(graph: nx.DiGraph, org: Org) -> None:
    graph.add_node(org["Id"], **org, type="organization")


def add_root(graph: nx.DiGraph, resource: RootTypeDef, org: Org) -> None:
    graph.add_node(resource["Id"], **resource, type="root")
    graph.add_edge(org["Id"], resource["Id"])


def add_organizational_unit(graph: nx.DiGraph, resource: OrganizationalUnitTypeDef, parent: Parent) -> None:
    graph.add_node(resource["Id"], **resource, type="organizational_unit")
    graph.add_edge(parent["Id"], resource["Id"])


def add_account(graph: nx.DiGraph, resource: AccountTypeDef, parent: Parent) -> None:
    graph.add_node(resource["Id"], **resource, type="account")
    graph.add_edge(parent["Id"], resource["Id"])


def add_tag(graph: nx.DiGraph, resource: Resource, tag: Tag) -> None:
    graph.nodes[resource["Id"]][f"tag:{tag['Key']}"] = tag["Value"]


def get_root(graph: nx.DiGraph) -> str:
    """Return the ID of the organization Root resource"""
    for id, attrs in graph.nodes.items():
        if attrs["type"] == "root":
            return cast(str, id)
    raise AssertionError("graph has no root node")


def get_org_metadata(graph: nx.DiGraph) -> str:
    """Return the ID of the organization Root resource"""
    for id, attrs in graph.nodes.items():
        if attrs["type"] == "organization":
            return cast(str, id)
    raise AssertionError("graph has no root node")


# TODO: This could be generalized to get the path from arbitrary nodes and to
# support any attribute as the component.
def get_path_from_root_with_name_components(graph: nx.DiGraph, target: str) -> str:
    root = get_root(graph)
    components = nx.shortest_path(graph, root, target)
    named_components = [graph.nodes[n]["Name"] for n in components]
    return f"/{'/'.join(named_components)}"


def generate_path_lookup_table(graph: nx.DiGraph) -> Dict[str, str]:
    root = get_root(graph)
    return {
        n: get_path_from_root_with_name_components(graph, n)
        for n in nx.descendants(graph, root)
    }


def iter_descendant_accounts(graph: nx.DiGraph, source: str) -> Iterator[str]:
    for desc in nx.descendants(graph, source):
        if graph.nodes[desc]["type"] == "account":
            yield desc


def count_descendant_accounts(graph: nx.DiGraph, source: str) -> int:
    return sum(1 for _ in iter_descendant_accounts(graph, source))


def read_graphml(file: File) -> nx.DiGraph:
    return nx.read_graphml(file)


def write_graphml(graph: nx.Graph, file: File = sys.stdout.buffer) -> None:
    """Write the organization graph to a file as GraphML.

    By default write to standard output.

    Nonscalar attributes, such as lists and datetimes, are omitted, because
    GraphML does not support them as data values.
    """
    graph_copy = deepcopy(graph)
    _delete_nonscalar_attributes(graph_copy)
    # NetworkX writes GraphML in binary mode.
    nx.write_graphml(graph_copy, file, encoding="utf8")


def _delete_nonscalar_attributes(graph: nx.Graph) -> None:
    """Delete nonscalar atrributes from the graph.

    GraphML does not support nonscalar attibutes as data values.
    """

    for attrs in graph.nodes.values():
        if attrs["type"] == "organization":
            del attrs["AvailablePolicyTypes"]
        if attrs["type"] == "root":
            del attrs["PolicyTypes"]
        if attrs["type"] == "account":
            del attrs["JoinedTimestamp"]


def save_org_graph(graph: nx.Graph, file: File = sys.stdout.buffer) -> None:
    """Save the org graph using pickle.
    """
    nx.write_gpickle(graph, file)


def load_org_graph(file: File) -> nx.Graph:
    return nx.read_gpickle(file)
