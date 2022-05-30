from pprint import pprint
from tkinter import *
from tkinter import ttk

root = Tk()
frame = ttk.Frame(root, padding=10)
frame.grid()
label = ttk.Label(frame, text="Hello, world!")
label.grid(column=0, row=0)
button = ttk.Button(frame, text="Quit", command=root.destroy)
button.grid(column=1, row=0)

pprint(frame.configure())
pprint(label.configure())
pprint(button.configure())

frame_attrs = set(dir(frame))
pprint(frame_attrs)

label_attrs = set(dir(label))
pprint(label_attrs - frame_attrs)

button_attrs = set(dir(button))
pprint(button_attrs - frame_attrs)

root.mainloop()
