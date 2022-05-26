from pubsub import pub  # type: ignore[import]
import networkx as nx
from boto3 import Session
from orgtreepubsub import crawl_organization

from type_defs import Account, Org, OrgUnit, Root, Parent


def crawl_org_graph(session: Session) -> nx.Graph:

    graph = nx.Graph()

    pub.subscribe(add_root, "root", graph=graph)
    pub.subscribe(add_organizational_unit, "organizational_unit", graph=graph)
    pub.subscribe(add_account, "account", graph=graph)

    crawl_organization(session)

    return graph


def add_root(graph: nx.Graph, resource: Root, org: Org):
    graph.add_edge(resource["Id"], org["Id"])


def add_organizational_unit(graph: nx.Graph, resource: OrgUnit, parent: Parent):
    graph.add_edge(resource["Id"], parent["Id"])


def add_account(graph: nx.Graph, resource: Account, parent: Parent):
    graph.add_edge(resource["Id"], parent["Id"])
