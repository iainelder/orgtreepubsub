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
