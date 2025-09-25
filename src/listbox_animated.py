"""
This class extends the tkinter Listbox class by an aninmated selection following the mouse movements.
"""
import tkinter as tk

class ListboxAnimated(tk.Listbox):
    def __init__(self, master=None, **kw):
        tk.Listbox.__init__(self, master, **kw)
        self.bind('<Enter>' , self._set_focus_and_highlight_line)
        self.bind('<Motion>', self._highlight_line)

    def _set_focus_and_highlight_line(self, event):
        self.focus_set() # Needed to catch the escape key.
        self._highlight_line(event)

    def _highlight_line(self, event):
        self.selection_clear(0, tk.END)
        self.selection_set(self.nearest(event.y))
