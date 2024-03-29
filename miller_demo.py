from collections import namedtuple
from itertools import chain
from org_graph import (
    count_descendant_accounts,
    iter_descendant_accounts,
    read_graphml,
    get_root,
)
from typing import Dict, Iterable, List, Optional, Tuple, cast
import tkinter as tk
import networkx as nx  # type: ignore[import]
from tkinter import ttk


AccountRow = namedtuple(
    "AccountRow", ["Id", "Name", "Email", "Arn", "Status", "JoinedMethod"]
)


def main() -> None:
    app = BrowserApp()
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
        if depth > len(self._components):
            raise ValueError(f"Can't set {depth=} when {len(self._components)=}")

        if depth < len(self._components) and self._components[depth] == node:
            return

        previous_component = self._components[depth - 1]
        children_of_previous_component = self.get_children(previous_component)
        if node not in children_of_previous_component:
            raise ValueError(f"{node} is not a child of {previous_component}")

        self._components[depth:] = [node]

    NavIterable = Iterable[Tuple[int, Optional[str], Optional[str], List[str]]]

    def iter_navegable_nodes(self) -> NavIterable:
        selected_ancestors = chain([None], self._components)
        selected_descendants = chain(self._components, [None])
        nav_iterator = enumerate(zip(selected_ancestors, selected_descendants))

        for depth, (parent, selected_child) in nav_iterator:
            children = self.get_children(parent)
            yield depth, parent, selected_child, children


class BrowserController:

    def __init__(
        self,
        path: PathSelection,
        org: nx.DiGraph,
        miller_view: "MillerView",
        account_table_view: "AccountTableView",
        resource_detail_view: "ResourceDetailView",
    ):
        self.org = org
        self.path = path
        self.miller_view = miller_view
        self.account_table_view = account_table_view
        self.resource_detail_view = resource_detail_view

    def update_selection(self, depth: int, node: str) -> None:
        self.path.update_selection(depth, node)
        self.show_path_in_view()
        self.show_descendant_accounts_in_table()

    def show_path_in_view(self) -> None:
        self.miller_view.clear_all_columns()
        # TODO: Remove this if it doesn't look good.
        # self.miller_view.hide_all_columns()
        nav_iterator = self.path.iter_navegable_nodes()
        for depth, parent, selected_child, children in nav_iterator:

            # TODO: Don't test the node value to format it correctly.
            # iter_navegable_nodes should return all the node data. Then here it
            # should test the node type to generate an appropriate item for each
            # node. Call clear_column and append_column here instead of
            # fill_column. Allow controller to call MillerColumn methods
            # directly.
            def format_count(node: str) -> str:
                if node.startswith("ou-") or node.startswith("r-"):
                    return str(count_descendant_accounts(self.org, node))
                return ""

            descendants_per_child = [format_count(p) for p in children]
            names_per_child = [self.org.nodes[p]["Name"] for p in children]

            self.miller_view.show_column(depth)
            self.miller_view.fill_column(
                depth,
                children,
                names_per_child,
                descendants_per_child
            )

            # TODO: Remove this definitely if I stick with the account count
            # column.
            # if parent is None:
            #     self.miller_view.set_column_name(depth, "")
            # else:
            #     self.miller_view.set_column_name(depth, parent)

            if selected_child is None:
                self.miller_view.clear_column_selection(depth)
            else:
                self.miller_view.set_column_selection(depth, selected_child)

    def show_descendant_accounts_in_table(self) -> None:
        account_ids = iter_descendant_accounts(self.org, self.path.components[-1])
        account_datas = (self.org.nodes[id] for id in account_ids)
        rows = (
            AccountRow(**{k: v for k, v in data.items() if k in AccountRow._fields})
            for data in account_datas

        )
        self.account_table_view.fill(rows)

    def update_resource_detail_view(self, selection: str) -> None:
        self.resource_detail_view.clear()
        if selection is None:
            return
        detail = cast(Dict[str, str], self.org.nodes[selection])
        for key, value in detail.items():
            self.resource_detail_view.add_detail(key, value)


class MillerColumn(ttk.Treeview):

    def __init__(self, parent: "MillerView") -> None:
        super().__init__(
            parent,
            columns=["Name", "Accounts"],
            displaycolumns="#all",
            show=["headings"]
        )

        self.heading("Name", text="Name")
        self.heading("Accounts", text="#")

        self.column("Name", width=160, stretch=True)
        self.column("Accounts", width=40, stretch=False)

        # TODO: Replace ButtonRelease with TreeviewSelect. Fix the infinite loop
        # that it causes. The call sequence that might trigger it:
        #
        # * MillerView.on_click_column
        # * BrowserController.update_selection
        # * BrowserController.show_path_in_view
        # * MillerView.clear_column_selection
        self.bind("<<TreeviewSelect>>", parent.on_click_column)

    def clear(self) -> None:
        for c in self.get_children():
            self.delete(c)

    def fill(
        self,
        items: List[str],
        names: List[str],
        descendants_per_child: List[str],
    ) -> None:
        self.clear()
        for item, name, descendants in zip(items, names, descendants_per_child):
            self.insert(
                parent="",
                index="end",
                iid=item,
                text=name,
                values=(name, descendants),
            )

    def first_selection(self) -> Optional[str]:
        selection = self.selection()
        if not selection:
            return None
        return selection[0]


class MillerView(ttk.Frame):

    controller: BrowserController
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

    def set_controller(self, controller: BrowserController) -> None:
        self.controller = controller

    def add_column(self) -> None:
        self.columns.append(MillerColumn(self))

    def set_column_name(self, depth: int, name: str) -> None:
        self.columns[depth].heading("Name", text=name)

    def clear_column_selection(self, depth: int) -> None:
        self.columns[depth].selection_clear()

    def set_column_selection(self, depth: int, iid: str) -> None:
        self.columns[depth].selection_set(iid)

    def fill_column(
        self,
        depth: int,
        children: List[str],
        names: List[str],
        descendants_per_child: List[str]
    ) -> None:
        self.columns[depth].fill(children, names, descendants_per_child)

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

    def clear_all_columns(self) -> None:
        for column in self.columns:
            column.clear()

    def hide_all_columns(self) -> None:
        for index in range(len(self.columns)):
            self.hide_column(index)


class AccountTableView(ttk.Frame):

    controller: BrowserController
    table: ttk.Treeview

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)

        columns = AccountRow._fields
        self.table = ttk.Treeview(
            self,
            columns=columns,
            displaycolumns="#all",
            show=["headings"],
        )

        for c in AccountRow._fields:
            self.table.heading(c, text=c)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.table.grid(column=0, row=0, sticky="NSEW")

        self.table.bind("<<TreeviewSelect>>", self.on_click)  # type: ignore[arg-type]

    def set_controller(self, controller: BrowserController) -> None:
        self.controller = controller

    def clear(self) -> None:
        for r in self.table.get_children():
            self.table.delete(r)

    def fill(self, accounts: Iterable[AccountRow]) -> None:
        self.clear()
        for account in accounts:
            self.table.insert(
                parent="",
                index="end",
                iid=account.Id,
                text=account.Id,
                values=account,
            )

    def first_selection(self) -> Optional[str]:
        selection = self.table.selection()
        if not selection:
            return None
        return selection[0]

    def on_click(self, event: "tk.Event[AccountTableView]") -> None:
        if not self.controller:
            return
        selection = self.first_selection()
        self.controller.update_resource_detail_view(selection)  # type: ignore[arg-type]


class ResourceDetailView(ttk.Frame):

    resource_name: ttk.Label
    tag_table: ttk.Treeview

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)

        self.resource_name = ttk.Label(self, text="Account 111111111111")

        columns = ["Key", "Value"]
        self.tag_table = ttk.Treeview(
            self,
            columns=columns,
            displaycolumns="#all",
            show=["headings"],
        )

        for c in columns:
            self.tag_table.heading(c, text=c)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.resource_name.grid(column=0, row=0, sticky="NSEW")
        self.tag_table.grid(column=0, row=1, sticky="NSEW")

    def clear(self) -> None:
        for r in self.tag_table.get_children():
            self.tag_table.delete(r)

    def add_detail(self, key: str, value: str) -> None:
        self.tag_table.insert(parent="", index="end", iid=key, values=(key, value))


class BrowserApp(tk.Tk):

    def __init__(self) -> None:
        super().__init__()
        self.bind_quit_events()

        self.grid()

        self.grid_rowconfigure(0, weight=1)
        self.miller_view = MillerView(self, 7)
        self.miller_view.grid(column=0, row=0, sticky="NSEW")

        self.grid_rowconfigure(1, weight=1)
        self.table_view = AccountTableView(self)
        self.table_view.grid(column=0, row=1, sticky="NSEW")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1, minsize=300)
        self.tag_table = ResourceDetailView(self)
        self.tag_table.grid(column=1, row=0, rowspan=2, sticky="NSEW")

        self.org_tree = read_graphml("/home/isme/tmp/int_org.graphml")
        self.path = PathSelection(org=self.org_tree)

        self.controller = BrowserController(
            self.path, self.org_tree, self.miller_view, self.table_view, self.tag_table
        )

        self.miller_view.set_controller(self.controller)
        self.table_view.set_controller(self.controller)

        self.controller.show_path_in_view()
        self.controller.show_descendant_accounts_in_table()

    def bind_quit_events(self) -> None:
        self.bind_all("<Alt-KeyPress-F4>", self.on_quit)
        self.bind_all("<Alt-KeyPress-q>", self.on_quit)

    def on_quit(self, event: "tk.Event[tk.Misc]") -> None:
        self.destroy()


if __name__ == "__main__":
    main()
