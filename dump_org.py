from boto3 import Session
import networkx as nx  # type: ignore[import]
import sys
from org_graph import crawl_org_graph


def main() -> None:
    graph = crawl_org_graph(Session())
    delete_nonscalar_attributes(graph)
    # NetworkX writes GraphML in binary mode.
    nx.write_graphml(graph, sys.stdout.buffer, encoding="utf8")


def delete_nonscalar_attributes(graph):
    for attrs in graph.nodes.values():
        if attrs["type"] == "organization":
            del attrs["AvailablePolicyTypes"]
        if attrs["type"] == "root":
            del attrs["PolicyTypes"]
        if attrs["type"] == "account":
            del attrs["JoinedTimestamp"]


if __name__ == "__main__":
    main()
