from copy import deepcopy
import sys
from typing import Any, BinaryIO, Dict, Iterator, Union, cast
from pubsub import pub  # type: ignore[import]
import networkx as nx  # type: ignore[import]
from boto3 import Session
from orgtreepubsub import crawl_organization

from type_defs import Account, Org, OrgUnit, Root, Parent, Resource, Tag

class OrgGraph:

    management_account_id: str

    def __init__(self, graph: nx.DiGraph) -> None:
        """Don't use this initializer. Instead use `snapshot_org`."""
        self._graph = graph

    @property
    def management_account(self) -> Account:
        # The graph data is a copy of the description dict with an extra type key
        # for the resource type.
        data: Dict[str, Any] = self._graph.nodes[self._management_account_id]
        account = cast(Account, {k: v for k, v in data.items() if k != "type"})
        return account

    @property
    def root(self) -> Root:
        data: Dict[str, Any] = self._graph.nodes[self._root_id]
        root = cast(Root, {k: v for k, v in data.items() if k != "type"})
        return root

    def _set_org_metadata(self, org: Org) -> None:
        self._management_account_id = org["MasterAccountId"]
        self.organization_id = org["Id"]

    def _set_root_metadata(self, org: Org, resource: Root) -> None:
        self._root_id = resource["Id"]

    def ac(self, account_id: str) -> Account:
        data: Dict[str, Any] = self._graph.nodes[account_id]
        if data["type"] != "account":
            raise AssertionError(f"{account_id=} is {data['type']=}, not account")
        account = cast(Account, {k: v for k, v in data.items() if k != "type"})
        return account


def snapshot_org(session: Session) -> OrgGraph:
    internal_graph = nx.DiGraph()
    org_model = OrgGraph(internal_graph)

    pub.subscribe(org_model._set_org_metadata, "organization")
    pub.subscribe(add_root, "root", graph=internal_graph)
    pub.subscribe(org_model._set_root_metadata, "root")
    pub.subscribe(add_organizational_unit, "organizational_unit", graph=internal_graph)
    pub.subscribe(add_account, "account", graph=internal_graph)

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


def add_root(graph: nx.DiGraph, resource: Root, org: Org) -> None:
    graph.add_node(resource["Id"], **resource, type="root")
    graph.add_edge(org["Id"], resource["Id"])


def add_organizational_unit(graph: nx.DiGraph, resource: OrgUnit, parent: Parent) -> None:
    graph.add_node(resource["Id"], **resource, type="organizational_unit")
    graph.add_edge(parent["Id"], resource["Id"])


def add_account(graph: nx.DiGraph, resource: Account, parent: Parent) -> None:
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
def get_path_from_root_with_name_components(graph: nx.DiGraph, target: str):
    root = get_root(graph)
    components = nx.shortest_path(graph, root, target)
    named_components = [graph.nodes[n]["Name"] for n in components]
    return f"/{'/'.join(named_components)}"


def generate_path_lookup_table(graph: nx.DiGraph):
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
    NetworkX does not support them as data values.
    """
    graph_copy = deepcopy(graph)
    _delete_nonscalar_attributes(graph_copy)
    # NetworkX writes GraphML in binary mode.
    nx.write_graphml(graph_copy, file, encoding="utf8")


def _delete_nonscalar_attributes(graph: nx.Graph) -> None:
    """Delete nonscalar atrributes from the graph.

    NetworkX does not support nonscalar attibutes as data values.
    """

    for attrs in graph.nodes.values():
        if attrs["type"] == "organization":
            del attrs["AvailablePolicyTypes"]
        if attrs["type"] == "root":
            del attrs["PolicyTypes"]
        if attrs["type"] == "account":
            del attrs["JoinedTimestamp"]
