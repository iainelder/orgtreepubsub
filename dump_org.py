from copy import deepcopy
from typing import BinaryIO
from boto3 import Session
import networkx as nx  # type: ignore[import]
import sys
from org_graph import get_org_graph


def main() -> None:
    "Write the organization graph to standard output as GraphML."
    org = get_org_graph(Session())
    write_graphml(org)


def write_graphml(graph: nx.Graph, file: BinaryIO=sys.stdout.buffer) -> None:
    """Write the organization graph to a file as GraphML.

    By default write to standard output.

    Nonscalar attributes, such as lists and datetimes, are omitted, because
    NetworkX does not support them as data values.
    """
    graph_copy = deepcopy(graph)
    delete_nonscalar_attributes(graph_copy)
    # NetworkX writes GraphML in binary mode.
    nx.write_graphml(graph_copy, file, encoding="utf8")


def delete_nonscalar_attributes(graph: nx.Graph) -> None:
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


if __name__ == "__main__":
    main()
