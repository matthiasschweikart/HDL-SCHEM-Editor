"""
class for the quick-access-buttons at the bottom of the window.
"""
import tkinter as tk
from tkinter import ttk
class QuickAccess():
    def __init__(self, schematic_window, column, row):
        self.schematic_window = schematic_window
        self.quick_access_frame = ttk.Frame(schematic_window, borderwidth=2, relief=tk.RAISED)
        self.quick_access_frame.grid(row=row, column=column, sticky=(tk.N,tk.W,tk.E,tk.S))
        self.quick_access_label         = ttk.Label(self.quick_access_frame, takefocus=False, text="Open modules:", borderwidth=5)
        self.quick_access_buttons_frame = ttk.Frame(self.quick_access_frame, borderwidth=0, relief='flat')
        self.quick_access_label.grid        (row=0, column=0)
        self.quick_access_buttons_frame.grid(row=0, column=1)
        self.quick_access_buttons_dict   = {} # dictionary with path_name as key and button reference as entry
        self.quick_access_buttons_column = 1

    def add_quick_access_button(self, window_of_module, file_name, module_name):
        if file_name not in self.quick_access_buttons_dict:
            self.quick_access_buttons_dict[file_name] = ttk.Button(self.quick_access_buttons_frame, takefocus=False, text=module_name, style="View.TButton")
            self.quick_access_buttons_dict[file_name].grid(row=0, column=self.quick_access_buttons_column)
            self.quick_access_buttons_dict[file_name].bind ('<Button-1>', lambda event : window_of_module.open_this_window())
            self.quick_access_buttons_column += 1

    def change_name_of_quick_access_button_in_all_windows_after_module_name_change(self, old_module_name, new_module_name):
        # Is called when the user changes the module_name in control-tab:
        #   path_name will be key in quick_access_buttons_dict of all open windows.
        # Is called when the user reads in a file (because the module_name will be updated).
        #   In this case no window will have the path_name in open-module-buttons.
        #   Instead the path_name of the old_module will be in open-module-buttons.
        path_name = self.schematic_window.design.get_path_name()
        for open_window, _ in self.schematic_window.__class__.open_window_dict.items():
            if path_name in open_window.quick_access_object.quick_access_buttons_dict:
                open_window.quick_access_object.quick_access_buttons_dict[path_name].configure(text=new_module_name)
            elif old_module_name in open_window.quick_access_object.quick_access_buttons_dict:
                # When a window is new, then the module_name "unnamed..." is used as path_name
                open_window.quick_access_object.quick_access_buttons_dict[path_name] = open_window.quick_access_object.quick_access_buttons_dict.pop(old_module_name)
                open_window.quick_access_object.quick_access_buttons_dict[path_name].configure(text=new_module_name)
            else:
                path_name_entry_to_replace = None
                for path_name_entry, button_reference in open_window.quick_access_object.quick_access_buttons_dict.items():
                    if button_reference.cget("text")==old_module_name:
                        path_name_entry_to_replace = path_name_entry
                if path_name_entry_to_replace is not None:
                    open_window.quick_access_object.quick_access_buttons_dict[path_name] = open_window.quick_access_object.quick_access_buttons_dict.pop(path_name_entry_to_replace)
                    open_window.quick_access_object.quick_access_buttons_dict[path_name].configure(text=new_module_name)

    def path_name_changed(self, old_path_name, path_name):
        if path_name!=old_path_name:
            for open_window, _ in self.schematic_window.__class__.open_window_dict.items():
                if old_path_name in open_window.quick_access_object.quick_access_buttons_dict:
                    open_window.quick_access_object.quick_access_buttons_dict[path_name] = open_window.quick_access_object.quick_access_buttons_dict.pop(old_path_name)

    def remove_quick_access_button(self, path_name): # called by close_this_window() from schematic_window.Schematic.Window
        for open_window in self.schematic_window.__class__.open_window_dict:
            if path_name in open_window.quick_access_object.quick_access_buttons_dict:
                open_window.quick_access_object.quick_access_buttons_dict[path_name].destroy()
                del open_window.quick_access_object.quick_access_buttons_dict[path_name]
