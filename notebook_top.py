""" This class describes the complete notebook of the schematic window """
import tkinter as tk
from   tkinter import ttk
import notebook_control_tab
import notebook_interface_tab
import notebook_internals_tab
import notebook_diagram_tab
import notebook_hdl_tab
import notebook_log_tab

class NotebookTop():
    def __init__(self, root, schematic_window, design, column, row,
                 wire_class, signal_name_class, input_class, output_class, inout_class,
                 block_class, symbol_reading_class, symbol_insertion_class, symbol_instance_class, generate_frame_class):
        self.window   = schematic_window
        self.notebook = ttk.Notebook(self.window, padding=5)
        self.notebook.columnconfigure(0, weight=1)
        self.notebook.grid(row=row, column=column, sticky=(tk.N,tk.W,tk.E,tk.S))
        self.control_tab   = notebook_control_tab.NotebookControlTab    (self.window, self.notebook)
        self.interface_tab = notebook_interface_tab.NotebookInterfaceTab(self.window, self.notebook)
        self.internals_tab = notebook_internals_tab.NotebookInternalsTab(self.window, self.notebook)
        self.diagram_tab   = notebook_diagram_tab.NotebookDiagramTab    (root, self.window, self.notebook,
                                                                         design, wire_class, signal_name_class, input_class, output_class,
                                                                         inout_class, block_class, symbol_reading_class,
                                                                         symbol_insertion_class, symbol_instance_class, generate_frame_class)
        self.hdl_tab       = notebook_hdl_tab.NotebookHdlTab            (root, self.window, self.notebook)
        self.log_tab       = notebook_log_tab.NotebookLogTab            (self.window, self.notebook)
        self.notebook.bind("<<NotebookTabChanged>>", lambda event: self.__notebook_tab_changed())

    def update_notebook_top_from(self, new_dict, fill_link_dictionary):
        self.control_tab  .update_control_tab_from  (new_dict)
        self.interface_tab.update_interface_tab_from(new_dict)
        self.internals_tab.update_internals_tab_from(new_dict)
        self.diagram_tab  .update_diagram_tab_from  (new_dict, push_design_to_stack=True)
        self.hdl_tab      .update_hdl_tab_from      (new_dict, fill_link_dictionary)
        self.log_tab      .update_hdl_log_from      (new_dict)

    def show_tab(self, name):
        tab_ids = self.window.notebook_top.notebook.tabs()
        for tab_id in tab_ids:
            if self.window.notebook_top.notebook.tab(tab_id, option="text")==name:
                self.window.notebook_top.notebook.select(tab_id)
                self.__notebook_tab_changed()

    def __notebook_tab_changed(self):
        visible_tab_id = self.notebook.select()
        if self.notebook.tab(visible_tab_id, option="text")=="Diagram":
            self.diagram_tab.diagram_tab_is_shown()
        else:
            self.diagram_tab.diagram_tab_is_hidden()
