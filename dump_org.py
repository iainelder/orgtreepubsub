from typing import Any, TextIO
from boto3 import Session
import networkx as nx  # type: ignore[import]
import json
import sys
from org_graph import crawl_org_graph


def main() -> None:
    graph = crawl_org_graph(Session())
    cyto = nx.cytoscape_data(graph)
    dump_json(cyto)


def dump_json(data: Any, file: TextIO = sys.stdout) -> None:
    json.dump(data, fp=file, indent=4)
    file.write("\n")


if __name__ == "__main__":
    main()
