from boto3 import Session
import networkx as nx  # type: ignore[import]
import sys
from org_graph import crawl_org_graph


def main() -> None:
    graph = crawl_org_graph(Session())
    # NetworkX writes GraphML in binary mode.
    nx.write_graphml(graph, sys.stdout.buffer, encoding="utf8")


if __name__ == "__main__":
    main()
