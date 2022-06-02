from copy import deepcopy
import sys
from typing import BinaryIO
from pubsub import pub  # type: ignore[import]
import networkx as nx  # type: ignore[import]
from boto3 import Session
from orgtreepubsub import crawl_organization

from type_defs import Account, Org, OrgUnit, Root, Parent


def get_org_graph(session: Session) -> nx.Graph:

    graph = nx.DiGraph()

    pub.subscribe(add_organization, "organization", graph=graph)
    pub.subscribe(add_root, "root", graph=graph)
    pub.subscribe(add_organizational_unit, "organizational_unit", graph=graph)
    pub.subscribe(add_account, "account", graph=graph)

    crawl_organization(session)

    return graph


def add_organization(graph: nx.DiGraph, org: Org) -> None:
    org["type"] = "organization"
    graph.add_node(org["Id"], **org)


def add_root(graph: nx.DiGraph, resource: Root, org: Org) -> None:
    resource["type"] = "root"
    graph.add_node(resource["Id"], **resource)
    graph.add_edge(org["Id"], resource["Id"])


def add_organizational_unit(graph: nx.DiGraph, resource: OrgUnit, parent: Parent) -> None:
    resource["type"] = "organizational_unit"
    graph.add_node(resource["Id"], **resource)
    graph.add_edge(parent["Id"], resource["Id"])


def add_account(graph: nx.DiGraph, resource: Account, parent: Parent) -> None:
    resource["type"] = "account"
    graph.add_node(resource["Id"], **resource)
    graph.add_edge(parent["Id"], resource["Id"])


def get_root(graph: nx.DiGraph) -> str:
    """Return the ID of the organization Root resource"""
    return next(id for id, attrs in graph.nodes.items() if attrs["type"] == "root")


def read_graphml(file: BinaryIO) -> nx.DiGraph:
    return nx.read_graphml(file)


def write_graphml(graph: nx.Graph, file: BinaryIO=sys.stdout.buffer) -> None:
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
