"""This module contains the TextDialog class, which is used to display a text window to show information."""

import tkinter as tk

from gui import schematic_window


class TextDialog:
    """This class implements a text dialog, which is used to display a text window to show information."""

    def __init__(self, title, content, size, root):
        window = tk.Toplevel(root)
        window.title(title)
        window.geometry(size)
        window.columnconfigure(0, weight=1)
        window.rowconfigure(0, weight=1)

        text_widget = tk.Text(window, wrap=tk.WORD, font=(root.style_admin_ref.font_name, 10))

        open_window = next(iter(schematic_window.SchematicWindow.open_window_dict), None)
        mode = open_window.menu_bar.prefs_menu.entrycget(0, "label") if open_window else "Dark Mode"
        if mode == "Dark Mode":
            text_widget.configure(bg="white", fg="black")
        else:
            text_widget.configure(bg="black", fg="white")
        text_widget.grid(sticky="nsew")
        text_widget.insert(tk.END, content)
        text_widget.config(state=tk.DISABLED)  # Make the Text widget read-only
