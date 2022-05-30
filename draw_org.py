import networkx as nx  # type: ignore[import]
import matplotlib.pyplot as plt  # type: ignore[import]
from org_browser import read_graphml
import sys
import matplotlib.pyplot as plt
import networkx as nx
from networkx.drawing.nx_pydot import graphviz_layout

def main() -> None:
    graph = read_graphml(sys.stdin.buffer)
    draw(graph)


def draw(graph: nx.Graph) -> None:
    # https://stackoverflow.com/questions/57512155/how-to-draw-a-tree-more-beautifully-in-networkx
    pos = graphviz_layout(graph, prog="twopi")
    nx.draw(graph, pos)
    plt.show()


if __name__ == "__main__":
    main()
