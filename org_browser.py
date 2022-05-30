from typing import Any
from pubsub import pub
from pubsub.core import Topic
import sys
from tkinter import ttk
from org_graph import read_graphml
import networkx as nx  # ignore: type[import]

class Browser(ttk.Frame):

    def __init__(self):
        pass

    def load_graph(graph: nx.DiGraph) -> None:
        pass


def main() -> None:
    pub.subscribe(spy, pub.ALL_TOPICS)
    graph = read_graphml(sys.stdin.buffer)
    # start_browser(graph)
    visit_hierarchy(graph)

def spy(topic: Topic = pub.AUTO_TOPIC, **data: Any) -> None:
    print(f"{topic.getName()} {data}")


def start_browser(graph: nx.DiGraph) -> None:
    frame = Browser()
    frame.mainloop()


def visit_hierarchy(graph: nx.DiGraph) -> None:
    # Get the Root
    root = ...
    for u, v in nx.bfs_edges(graph, root):
        u_data = graph.nodes[u]
        v_data = graph.nodes[v]
        pub.sendMessage(v["type"], v_data, parent=u_data)


if __name__ == "__main__":
    main()
