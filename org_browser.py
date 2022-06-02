from typing import Any
from pubsub import pub
from pubsub.core import Topic
import sys
import tkinter as tk
from tkinter import ttk
from pandastable import Table
import pandas as pd
from org_graph import read_graphml, get_root
import networkx as nx  # ignore: type[import]
from type_defs import Account, Parent, OrgUnit, Root, Org

class Browser(ttk.Frame):

    tree: ttk.Treeview
    # table: ttk.Treeview
    table: Table

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_table_using_pandastable()


    def init_tree_using_treeview(self):
        tree_label = ttk.Label(self, text="Organizational Units")
        tree_label.grid(column=0, row=0)
        self.tree = ttk.Treeview(self)
        self.tree.grid(column=0, row=1)


    def init_table_using_pandastable(self):
        table_label = ttk.Label(self, text="Accounts")
        table_label.grid(column=1, row=0)

        columns = [
            "Id", "Name", "Email", "JoinedTimestamp", "Status", "JoinedMethod", "Arn"
        ]

        self.table = Table(self,
          dataframe=pd.DataFrame(columns=columns),
          showtoolbar=True,
          showstatusbar=True
        )

        self.table.grid(column=1, row=1)
        self.table.show()


    def init_table_using_treeview(self):
        self.table = ttk.Treeview(self)
        self.table.grid(column=1, row=1)

        columns = [
            "Id", "Name", "Email", "JoinedTimestamp", "Status", "JoinedMethod", "Arn"
        ]
        self.table["columns"] = list(columns)
        self.table["displaycolumns"] = "#all"

        for c in columns:
            self.table.heading(c, text=c)

        self.table["show"] ="headings"


    def insert_dummy_data(self):
        self.tree.insert("", "end", iid="root", text="root")
        self.tree.insert("root", "end", iid="OU 1", text="OU 1")
        self.tree.insert("root", "end", iid="OU 2", text="OU 2")

        val1 = [
            "111111111111", "Account 1", "email1@aws.com", "2022-05-31T12:00:00", "ACTIVE", "arn:123:blah"
        ]
        self.table.insert(
            "", "end", iid="111111111111", text="111111111111", values=val1
        )
        val2 = [
            "222222222222", "Account 2", "email2@aws.com", "2022-05-30T12:00:00", "ACTIVE", "arn:123:blah2"
        ]
        self.table.insert(
            "", "end", iid="222222222222", text="222222222222", values=val2
        )


    def add_account(self, resource: Account, parent: Parent):        
        row = [
            resource["Id"],
            resource["Name"],
            resource["Email"],
            "2022-05-31T12:00:00", # resource["JoinedTimestamp"],
            resource["Status"],
            resource["JoinedMethod"],
            resource["Arn"]
        ]                                                                                                                                                                                                                                                                       

        next_index = len(self.table.model.df.index)
        self.table.model.df.loc[next_index] = row
        self.table.redraw()


    def add_organizational_unit(self, resource: OrgUnit, parent: Parent):
        self.tree.insert(parent["Id"], "end", iid=resource["Id"], text=resource["Id"])


    def add_root(self, root_id: str): # TODO: sent Root object
        self.tree.insert("", "end", iid=root_id, text=root_id)


    def load_graph(self, graph: nx.DiGraph) -> None:
        pub.subscribe(self.add_account, "account")
        #pub.subscribe(self.add_organizational_unit, "organizational_unit")
        #pub.subscribe(self.add_root, "root")

        id = get_root(graph)
        pub.sendMessage("root", root_id=id)
        for u, v in nx.bfs_edges(graph, id):
            u_data = graph.nodes[u]
            v_data = graph.nodes[v]
            pub.sendMessage(v_data["type"], resource=v_data, parent=u_data)


def main() -> None:
    pub.subscribe(spy, pub.ALL_TOPICS)
    graph = read_graphml(sys.stdin.buffer)
    start_browser(graph)


def spy(topic: Topic = pub.AUTO_TOPIC, **data: Any) -> None:
    print(f"{topic.getName()} {data}")


def start_browser(graph: nx.DiGraph) -> None:
    root = tk.Tk()
    browser = Browser(root, padding=10)
    browser.grid()
    browser.load_graph(graph)
    root.mainloop()


if __name__ == "__main__":
    main()
