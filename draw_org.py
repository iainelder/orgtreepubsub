from boto3 import Session
import networkx as nx
import matplotlib.pyplot as plt  # type: ignore[import]
from org_graph import crawl_org_graph


def main() -> None:
    graph = crawl_org_graph(Session())
    draw(graph)


def draw(graph: nx.Graph) -> None:
    nx.draw_networkx(graph)
    plt.show()


if __name__ == "__main__":
    main()
