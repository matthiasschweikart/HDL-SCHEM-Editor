"""This module contains the TextDialog class, which is used to display a text window to show information."""

import tkinter as tk


class TextDialog:
    """This class implements a text dialog, which is used to display a text window to show information."""

    def __init__(self, title, content, size, root):
        window = tk.Toplevel(root)
        window.title(title)
        window.geometry(size)
        window.columnconfigure(0, weight=1)
        window.rowconfigure(0, weight=1)

        text_widget = tk.Text(window, wrap=tk.WORD, font=("Arial", 10))
        text_widget.grid(sticky="nsew")
        text_widget.insert(tk.END, content)
        text_widget.config(state=tk.DISABLED)  # Make the Text widget read-only
