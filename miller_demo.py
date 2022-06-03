from itertools import zip_longest
from org_graph import read_graphml, get_root
from typing import Any, Callable, List, Optional, cast
import tkinter as tk
import networkx as nx  # ignore: type[import]
from networkx.utils import pairwise
from tkinter import ttk
from type_defs import Org

def main() -> None:
    org_tree = read_graphml("/home/isme/tmp/int_org.graphml")
    root = get_root(org_tree)

    def get_children(parent: str) -> List[str]:
        return list(org_tree[parent])

    app = MillerApp(root, get_children)
    app.mainloop()


class OrgPath:

    _org: Org
    _path: List[str]

    def __init__(self, org: Org) -> None:
        root = get_root(org)
        self.path = [root]
    
    @property
    def path(self) -> List[str]:
        return self._path
    
    @path.setter
    def path(self, value: List[str]) -> None:
        if not nx.is_simple_path(self._org, value):
            raise ValueError(f"Invalid org path: {value}")


class MillerController:

    def __init__(
        self,
        path: OrgPath,
        org: Org,
        get_children: Callable[[str], List[str]],
        view: "MillerView"
    ):
        self.org_path = path
        self.org = org
        self.get_children = get_children
        self.view = view

    def update_path(self, selected_path: List[str]) -> None:
        new_path = self.longest_common_path(selected_path, self.model.path)
        self.model.path = new_path
        self.show_path_in_view()

    def longest_common_path(p1: List[str], p2: List[str]) -> List[str]:
        for n1, n2 in zip(p1, p2):
            if n1 != n2:
                return
            yield n1

    def show_path_in_view(self):
        first_hidden = len(self.org_path.path)
        for i in range(first_hidden, self.view.max_depth()):
            self.view.hide_column(i)
        
        # replace pairwise with parent_and_selected_child iterator. selected_child will be None at the end.
        for i, node in enumerate(pairwise(self.org_path.path)):
            children = self.get_children(node)
            self.view.show_column(i)
            self.view.set_column_name(i, node)
            self.view.fill_column(children)
    


class MillerColumn(ttk.Treeview):

    ancestor_of_visible_children: Optional[str]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.ancestor_of_visible_children = None

    def fill(self, items: List[str]) -> None:
        for c in self.get_children():
            self.delete(c)

        for item in items:
            self.insert(parent="", index="end", iid=item, text=item, values=(item,))

    def depth(self) -> int:
        return self.grid_info()["column"]
    
    def first_selection(self) -> str:
        selection = self.selection()
        if not selection:
            return None
        return selection[0]


class MillerView(ttk.Frame):

    controller: MillerController
    columns: List[MillerColumn]

    def __init__(self, parent: tk.Widget, max_depth: int):
        super().__init__(parent)
        self.grid()

        self.columns = []
        for i in range(max_depth):
            self.add_column()
    
    def set_controller(self, controller: MillerController):
        self.controller = controller

    def add_column(self) -> None:
        miller = MillerColumn(
            self,
            columns=["Name"],
            displaycolumns="#all",
            show=["headings"]
        )

        miller.bind("<ButtonRelease>", self.on_click_column)

        self.columns.append(miller)

    def set_column_name(self, depth: int, name: str):
        self.columns[depth].heading("Name", text=name)
    
    def fill_column(self, depth: int, children: str):
        self.columns[depth].fill(children)
    
    def show_column(self, depth: int):
        self.columns[depth].grid(column=depth, row=0, sticky="NSEW")
        self.grid_columnconfigure(depth, weight=1)

    def hide_column(self, depth: int):
        self.columns[depth].grid_forget()

    def max_depth(self) -> int:
        return len(self.columns)
    
    def on_click_column(self, event: "tk.Event[MillerColumn]") -> None:
        if not self.controller:
            return
        path_selection = [c.first_selection() for c in self.columns]
        self.controller.update_path(path_selection)


class MillerApp(tk.Tk):

    levels: List[MillerColumn]

    def __init__(
        self,
        root: str,
        get_children: Callable[[str], List[str]]
    ) -> None:
        super().__init__()
        self.levels = []
        self.root = root
        self.get_children = get_children

        self.grid()

        self.grid_rowconfigure(0, weight=1)

        self.show_miller(0, root)

        self.bind_quit_events()
    
    def bind_quit_events(self) -> None:
        self.bind_all("<Alt-KeyPress-F4>", self.on_quit)
        self.bind_all("<Alt-KeyPress-q>", self.on_quit)

    def show_miller(self, depth: int, name: str):
        if depth >= len(self.levels):
            self.levels.append(self.place_miller(depth, name))
        miller = self.levels[depth]
        miller.grid(column=depth, row=0, sticky="NSEW")
        miller.fill(self.get_children(name))

    def place_miller(self, index: int, name: str) -> MillerColumn:
        columns = ["Name"]

        miller = MillerColumn(
            self,
            columns=columns,
            displaycolumns="#all",
            show=["headings"]
        )

        for c in columns:
            miller.heading(c, text=name)
        
        miller.grid(column=index, row=0, sticky="NSEW")

        self.grid_columnconfigure(index, weight=1)

        miller.bind("<ButtonRelease>", self.on_click_miller)
        
        return miller

    def on_click_miller(self, event: "tk.Event[MillerColumn]") -> None:
        clicked_miller = event.widget
        selection = clicked_miller.selection()

        if not selection:
            return

        selected_item = selection[0]

        if selected_item == clicked_miller.ancestor_of_visible_children:
            return

        clicked_depth = clicked_miller.depth()
        visible_depth = self.visible_depth()

        if clicked_depth + 1 < visible_depth:
            self.hide_millers_deeper_than(clicked_depth + 1)

        self.show_miller(clicked_depth + 1, selected_item)

        clicked_miller.ancestor_of_visible_children = selected_item

        print(self.grid_slaves())

    def visible_depth(self) -> int:
        return len(self.grid_slaves())

    def visible_millers(self) -> List[MillerColumn]:
        return cast(MillerColumn, self.grid_slaves(row=0))

    def hide_millers_deeper_than(self, threshold: int) -> None:
        for miller in self.visible_millers():
            if miller.depth() > threshold:
                miller.grid_remove()

    def on_quit(self, event: "tk.Event[tk.Misc]") -> None:
        self.destroy()


if __name__ == "__main__":
    main()
