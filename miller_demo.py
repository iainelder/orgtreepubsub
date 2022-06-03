from org_graph import read_graphml, get_root
from typing import Callable, List
import sys
import tkinter as tk
from tkinter import ttk

def main() -> None:
    org_tree = read_graphml("/home/isme/tmp/int_org.graphml")
    root = get_root(org_tree)

    def get_children(parent: str) -> List[str]:
        return list(org_tree[parent])

    app = MillerColumns(root, get_children)
    app.mainloop()


class MillerColumns(tk.Tk):

    def __init__(
        self,
        root: str,
        get_children: Callable[[str], List[str]]
    ) -> None:
        super().__init__()
        self.root = root
        self.get_children = get_children

        self.grid()

        self.grid_rowconfigure(0, weight=1)

        miller = self.place_miller(0, root)
        self.fill_miller(miller, get_children(root))

        self.bind_quit_events()
    
    def bind_quit_events(self) -> None:
        self.bind_all("<Alt-KeyPress-F4>", self.on_quit)
        self.bind_all("<Alt-KeyPress-q>", self.on_quit)
    
    def place_miller(self, index: int, name: str) -> ttk.Treeview:
        columns = ["Name"]

        miller = ttk.Treeview(
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

    def on_click_miller(self, event: "tk.Event[ttk.Treeview]") -> None:
        clicked_miller = event.widget
        grid_info = clicked_miller.grid_info()
        last_index = self.miller_count() - 1
        clicked_index = grid_info["column"]

        for i in range(last_index, clicked_index, -1):
            self.grid_slaves(row=0, column=i)[0].destroy()

        selected = clicked_miller.selection()
        if selected:
            parent = selected[0]
            children = self.get_children(parent)
            next_miller = self.append_miller(parent)
            self.fill_miller(next_miller, children)

    def append_miller(self, name: str) -> ttk.Treeview:
        next_index = self.miller_count()
        return self.place_miller(next_index, name)

    def miller_count(self) -> int:
        return len(self.grid_slaves())
    
    def fill_miller(self, miller: ttk.Treeview, items: List[str]) -> None:
        for item in items:
            miller.insert(parent="", index="end", iid=item, text=item, values=(item,))

    def on_quit(self, event: "tk.Event[tk.Misc]") -> None:
        sys.exit(0)


if __name__ == "__main__":
    main()
