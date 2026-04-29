"""
This class lets the user define a maximum line number to show at a block.
"""

import tkinter as tk
from tkinter import ttk


class LineNumberToShowDialog:
    """This class lets the user define a maximum line number to show at a block."""

    def __init__(self, window, current_number_of_lines_to_show):
        self.window = tk.Toplevel(window)
        self.current_number_of_lines_to_show = current_number_of_lines_to_show
        self.window.grab_set()
        self.window.title("HSE:")

        header = ttk.Label(self.window, text="Enter number of lines to show (0 shows all):", width=40, anchor="center")
        frame1 = ttk.Frame(self.window)
        frame2 = ttk.Frame(self.window)
        header.grid(row=0, column=0, sticky="we")
        frame1.grid(row=1, column=0, sticky="we")
        frame2.grid(row=2, column=0, sticky="we")

        self.line_number_var = tk.IntVar()
        self.line_number_var.set(current_number_of_lines_to_show)
        self.line_number_entry = ttk.Entry(frame1, textvariable=self.line_number_var, width=10)
        self.line_number_entry.focus()
        self.line_number_entry.grid(row=0, column=1, pady=5)
        frame1.columnconfigure(0, weight=1)
        frame1.columnconfigure(2, weight=1)

        button1 = ttk.Button(frame2, text="OK", command=self.window.destroy, padding=5, default="active")
        button2 = ttk.Button(frame2, text="Cancel", command=self._restore_limit, padding=5)
        button1.grid(row=1, column=0)
        button2.grid(row=1, column=1)
        frame2.columnconfigure(0, weight=1)
        frame2.columnconfigure(1, weight=1)
        button1.focus_set()
        button1.bind("<Return>", lambda event: self.window.destroy())
        self.line_number_entry.bind("<Return>", lambda event: self.window.destroy())
        self.window.wait_window(self.window)  # Wait until the dialog is closed.

    def _restore_limit(self):
        self.line_number_var.set(self.current_number_of_lines_to_show)
        self.window.destroy()

    def get_number(self):
        """Returns the entered number of lines"""
        return self.line_number_var.get()
