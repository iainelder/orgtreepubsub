from org_graph import read_graphml, get_root
from typing import Any, Callable, List, Optional, cast
import tkinter as tk
from tkinter import ttk

def main() -> None:
    org_tree = read_graphml("/home/isme/tmp/int_org.graphml")
    root = get_root(org_tree)

    def get_children(parent: str) -> List[str]:
        return list(org_tree[parent])

    app = MillerApp(root, get_children)
    app.mainloop()


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
