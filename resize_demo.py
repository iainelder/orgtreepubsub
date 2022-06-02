from itertools import product
import tkinter as tk
from tkinter import ttk


def main() -> None:
    app = Checkerboard(size=3, words="C O W A B U N G A")
    app.mainloop()


# Thanks to this question for the training inspiration.
# "Trying to resize widgets when the window is resized."
# https://stackoverflow.com/questions/24644339/python-tkinter-resize-widgets-evenly-in-a-window
class Checkerboard(tk.Tk):

    def __init__(self, size: int = 2, words = "HOW DO YOU DO") -> None:
        super().__init__()
        self.grid()

        self.colors = ["black", "white"]

        self.words = words.split()

        for w, rc in enumerate(product(range(size), range(size))):
            (r, c) = rc
            self.place_tile(c, r, self.words[w])

        for c in range(size):
            self.grid_columnconfigure(c, weight=1)

        for r in range(size):
            self.grid_rowconfigure(r, weight=1)

    def place_tile(self, column: int, row: int, word: str) -> None:
        tile_color = self.tile_color(column, row)
        text_color = self.opposite_color(tile_color)
        label = ttk.Label(
            self,
            anchor="center",
            text=word,
            background=tile_color,
            foreground=text_color,
            padding=2
        )
        label.grid(column=column, row=row, sticky="NSEW")

    def tile_color(self, column: int, row: int) -> str:
        return self.colors[(column % 2 + row % 2) % 2]

    def opposite_color(self, color: str) -> str:
        index = self.colors.index(color)
        return self.colors[(index + 1) % 2]


if __name__ == "__main__":
    main()
