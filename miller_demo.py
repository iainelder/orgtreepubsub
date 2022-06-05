from itertools import chain
from org_graph import read_graphml, get_root
from typing import Iterator, List, Optional, Tuple
import tkinter as tk
import networkx as nx  # type: ignore[import]
from tkinter import ttk


def main() -> None:
    app = MillerApp()
    app.mainloop()


class PathSelection:

    _root: str
    _org: nx.DiGraph
    _components: List[str]

    def __init__(self, org: nx.DiGraph) -> None:
        self._org = org
        self._root = get_root(org)
        self._components = [self._root]

    @property
    def components(self) -> List[str]:
        return self._components

    def get_children(self, parent: Optional[str]) -> List[str]:
        if parent is None:
            return [self._root]
        return list(self._org[parent])

    def update_selection(self, depth: int, node: str) -> None:
        if len(self._components) > depth and self._components[depth] == node:
            return

        previous_component = self._components[depth - 1]
        children_of_previous_component = self.get_children(previous_component)
        if node not in children_of_previous_component:
            raise ValueError(f"{node} is not a child of {previous_component}")

        self._components[depth:] = [node]

    NavIterator = Iterator[Tuple[int, Optional[str], Optional[str], List[str]]]

    def iter_navegable_nodes(self) -> NavIterator:
        selected_ancestors = chain([None], self._components)
        selected_descendants = chain(self._components, [None])
        nav_iterator = enumerate(zip(selected_ancestors, selected_descendants))

        for depth, (parent, selected_child) in nav_iterator:
            children = self.get_children(parent)
            yield depth, parent, selected_child, children

class MillerController:

    def __init__(self, model: PathSelection, view: "MillerView"):
        self.model = model
        self.view = view

    def update_selection(self, depth: int, node: str) -> None:
        self.model.update_selection(depth, node)
        self.show_path_in_view()

    def show_path_in_view(self) -> None:
        nav_iterator = self.model.iter_navegable_nodes()
        for depth, parent, selected_child, children in nav_iterator:
            self.view.show_column(depth)
            self.view.set_column_name(depth, parent if parent is not None else "")
            self.view.fill_column(depth, children)

            if selected_child is None:
                self.view.clear_column_selection(depth)
            else:
                self.view.set_column_selection(depth, selected_child)


class MillerColumn(ttk.Treeview):

    def __init__(self, parent: "MillerView") -> None:
        super().__init__(
            parent,
            columns=["Name"],
            displaycolumns="#all",
            show=["headings"]
        )

        self.bind("<ButtonRelease>", parent.on_click_column)

    def fill(self, items: List[str]) -> None:
        for c in self.get_children():
            self.delete(c)

        for item in items:
            self.insert(parent="", index="end", iid=item, text=item, values=(item,))

    def first_selection(self) -> Optional[str]:
        selection = self.selection()
        if not selection:
            return None
        return selection[0]


class MillerView(ttk.Frame):

    controller: MillerController
    columns: List[MillerColumn]

    def __init__(self, parent: tk.Misc, max_depth: int):
        super().__init__(parent)

        self.grid()
        self.grid_rowconfigure(0, weight=1)

        self.columns = []
        for i in range(max_depth):
            self.add_column()
            self.show_column(i)
            self.grid_columnconfigure(i, weight=1)

    def set_controller(self, controller: MillerController) -> None:
        self.controller = controller

    def add_column(self) -> None:
        self.columns.append(MillerColumn(self))

    def set_column_name(self, depth: int, name: str) -> None:
        self.columns[depth].heading("Name", text=name)
    
    def clear_column_selection(self, depth: int) -> None:
        self.columns[depth].selection_clear()
    
    def set_column_selection(self, depth: int, iid: str) -> None:
        self.columns[depth].selection_set(iid)
    
    def fill_column(self, depth: int, children: List[str]) -> None:
        self.columns[depth].fill(children)
    
    def show_column(self, depth: int) -> None:
        self.columns[depth].grid(column=depth, row=0, sticky="NSEW")
        self.grid_columnconfigure(depth, weight=1)

    def hide_column(self, depth: int) -> None:
        self.columns[depth].grid_forget()

    def max_depth(self) -> int:
        return len(self.columns)
    
    def on_click_column(self, event: "tk.Event[MillerColumn]") -> None:
        if not self.controller:
            return
        column = event.widget
        depth = self.columns.index(column)
        selection = column.first_selection()
        if selection is not None:
            self.controller.update_selection(depth, selection)


class MillerApp(tk.Tk):

    def __init__(self) -> None:
        super().__init__()
        self.bind_quit_events()

        self.grid()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.view = MillerView(self, 5)
        self.view.grid(column=0, row=0, sticky="NSEW")

        org_tree = read_graphml("/home/isme/tmp/int_org.graphml")
        self.model = PathSelection(org=org_tree)

        self.controller = MillerController(self.model, self.view)
        self.view.set_controller(self.controller)
        self.controller.show_path_in_view()

    def bind_quit_events(self) -> None:
        self.bind_all("<Alt-KeyPress-F4>", self.on_quit)
        self.bind_all("<Alt-KeyPress-q>", self.on_quit)

    def on_quit(self, event: "tk.Event[tk.Misc]") -> None:
        self.destroy()


if __name__ == "__main__":
    main()
