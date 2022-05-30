from typing import Any
from pubsub import pub
from pubsub.core import Topic
import sys
import tkinter as tk
from tkinter import ttk
from org_graph import read_graphml, get_root
import networkx as nx  # ignore: type[import]

class Browser(ttk.Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        label = ttk.Label(self, text="Hello, world!")
        label.grid(column=0, row=0)
        tree = ttk.Treeview(self)
        tree.grid(column=0, row=1)
        tree.insert("", "end", iid="root", text="root")
        tree.insert("root", "end", iid="OU 1", text="OU 1")
        tree.insert("root", "end", iid="OU 2", text="OU 2")


    def load_graph(graph: nx.DiGraph) -> None:
        pass


def main() -> None:
    pub.subscribe(spy, pub.ALL_TOPICS)
    graph = read_graphml(sys.stdin.buffer)
    start_browser(graph)
    # visit_hierarchy(graph)


def spy(topic: Topic = pub.AUTO_TOPIC, **data: Any) -> None:
    print(f"{topic.getName()} {data}")


def start_browser(graph: nx.DiGraph) -> None:
    root = tk.Tk()
    browser = Browser(root, padding=10)
    browser.grid()
    root.mainloop()


def visit_hierarchy(graph: nx.DiGraph) -> None:
    id, data = get_root(graph)
    for u, v in nx.bfs_edges(graph, root):
        u_data = graph.nodes[u]
        v_data = graph.nodes[v]
        pub.sendMessage(v_data["type"], resource=v_data, parent=u_data)


if __name__ == "__main__":
    main()
