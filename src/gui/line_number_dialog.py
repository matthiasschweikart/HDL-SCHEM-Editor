"""
This class lets the user define a line number to jump to.
"""

import tkinter as tk
from tkinter import ttk


class LineNumberDialog:
    """This class lets the user define a line number to jump to."""

    def __init__(self, root, window):
        self.toplevel = tk.Toplevel(root)
        self.toplevel.title("HFE:")
        self.window = window
        header = ttk.Label(
            self.toplevel, text="Enter line number to jump to:", width=35, anchor="center", style="My.TLabel"
        )
        frame1 = ttk.Frame(self.toplevel, style="My.TFrame")
        frame2 = ttk.Frame(self.toplevel, style="My.TFrame")
        header.grid(row=0, column=0, sticky="we")
        frame1.grid(row=1, column=0, sticky="we")
        frame2.grid(row=2, column=0, sticky="we")

        line_number = tk.IntVar()
        self.line_number_entry = ttk.Entry(frame1, textvariable=line_number, width=10, style="My.TEntry")
        self.line_number_entry.focus_set()
        self.line_number_entry.grid(row=0, column=1, pady=5)
        frame1.columnconfigure(0, weight=1)
        frame1.columnconfigure(2, weight=1)

        self.file_var = tk.IntVar()
        if self.window.design.get_language() == "VHDL" and self.window.design.get_number_of_files() == 2:
            self.file_var.set(2)
            radio1 = ttk.Radiobutton(
                frame2,
                takefocus=False,
                variable=self.file_var,
                text="in Architecture",
                value=2,
                style="My.TRadiobutton",
            )
            radio2 = ttk.Radiobutton(
                frame2, takefocus=False, variable=self.file_var, text="in Entity", value=1, style="My.TRadiobutton"
            )
            radio1.grid(row=0, column=0)
            radio2.grid(row=0, column=1)
        else:
            self.file_var.set(1)
        button1 = ttk.Button(frame2, text="OK", command=self._jump, padding=5, style="My.TButton")
        button2 = ttk.Button(frame2, text="Cancel", command=self.toplevel.destroy, padding=5, style="My.TButton")
        button1.grid(row=1, column=0)
        button2.grid(row=1, column=1)
        frame2.columnconfigure(0, weight=1)
        frame2.columnconfigure(1, weight=1)
        self.line_number_entry.bind("<Return>", lambda e: self._jump())

    def _jump(self):
        self.window.notebook_top.hdl_tab.hdl_frame_text.tag_remove("goto-line", "1.0", tk.END)
        line_number = self.line_number_entry.get().strip()
        if not line_number.isdigit():
            return
        if self.file_var.get() == 1:
            self.window.notebook_top.hdl_tab.hdl_frame_text.see(f"{line_number}.0")
            self.window.notebook_top.hdl_tab.hdl_frame_text.tag_add(
                "goto-line", f"{line_number}.0", f"{line_number}.0 lineend"
            )
        else:
            self.window.notebook_top.hdl_tab.hdl_frame_text.see(
                f"{int(line_number) + self.window.notebook_top.hdl_tab.last_line_number_of_file1}.0"
            )
            self.window.notebook_top.hdl_tab.hdl_frame_text.tag_add(
                "goto-line",
                f"{int(line_number) + self.window.notebook_top.hdl_tab.last_line_number_of_file1}.0",
                f"{int(line_number) + self.window.notebook_top.hdl_tab.last_line_number_of_file1}.0 lineend",
            )
        self.toplevel.destroy()
