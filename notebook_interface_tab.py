""" Interface tab for packages, ports, generics"""
import tkinter as tk
from   tkinter import ttk
from   tkinter import messagebox

import custom_text
import vhdl_parsing

class NotebookInterfaceTab():
    def __init__(self, schematic_window, notebook):
        self.window = schematic_window
        self.paned_window = ttk.PanedWindow(notebook, orient=tk.VERTICAL, takefocus=True)

        self.packages_frame = ttk.Frame(self.paned_window)
        self.packages_frame.grid()
        self.packages_frame.columnconfigure(0, weight=1)
        self.packages_frame.columnconfigure(1, weight=0)
        self.packages_frame.rowconfigure(0, weight=0)
        self.packages_frame.rowconfigure(1, weight=1)

        self.interface_packages_label  = ttk.Label             (self.packages_frame, text="Packages:", padding=5)
        self.interface_packages_info   = ttk.Label             (self.packages_frame, text="Undo/Redo: Ctrl-z/Ctrl-y/Z", padding=5)
        self.interface_packages_text   = custom_text.CustomText(self.packages_frame, window=self.window, parser=vhdl_parsing.VhdlParser,
                                                                tag_position_list=vhdl_parsing.VhdlParser.tag_position_list, font=("Courier", 10),
                                                                text_name="interface_packages", height=3, width=10, undo=True, maxundo=-1)
        self.interface_packages_scroll = ttk.Scrollbar         (self.packages_frame, orient=tk.VERTICAL, cursor='arrow', command=self.interface_packages_text.yview)
        self.interface_packages_text.config(yscrollcommand=self.interface_packages_scroll.set)
        self.interface_packages_text.insert_text("library ieee;\nuse ieee.std_logic_1164.all;", state_after_insert="normal")
        self.interface_packages_text.store_change_in_text_dictionary(signal_design_change=False)
        self.interface_packages_label.grid  (row=0, column=0, sticky=tk.W) # "W" nötig, damit Text links bleibt
        self.interface_packages_info.grid   (row=0, column=0, sticky=tk.E)
        self.interface_packages_text.grid   (row=1, column=0, sticky=(tk.W,tk.E,tk.S,tk.N)) # "W,E" nötig, damit Text tatsächlich breiter wird
        self.interface_packages_scroll.grid (row=1, column=1, sticky=(tk.W,tk.E,tk.S,tk.N)) # "W,E" nötig, damit Text tatsächlich breiter wird
        self.paned_window.add(self.packages_frame, weight=1)

        self.generics_frame = ttk.Frame(self.paned_window)
        self.generics_frame.grid()
        self.generics_frame.columnconfigure(0, weight=1)
        self.generics_frame.columnconfigure(1, weight=0)
        self.generics_frame.rowconfigure(0, weight=0)
        self.generics_frame.rowconfigure(1, weight=1)

        self.interface_generics_label = ttk.Label             (self.generics_frame, text="Generics:", padding=5)
        self.interface_generics_info  = ttk.Label             (self.generics_frame, text="Undo/Redo: Ctrl-z/Ctrl-y/Z", padding=5)
        self.interface_generics_text  = custom_text.CustomText(self.generics_frame, window=self.window, parser=vhdl_parsing.VhdlParser,
                                                               tag_position_list=vhdl_parsing.VhdlParser.tag_position_list, font=("Courier", 10),
                                                               text_name="interface_generics", height=3, width=10, undo=True, maxundo=-1)
        self.interface_generics_scroll= ttk.Scrollbar         (self.generics_frame, orient=tk.VERTICAL, cursor='arrow',
                                                               command=self.interface_generics_text.yview)
        self.interface_generics_text.config(yscrollcommand=self.interface_generics_scroll.set)
        self.interface_generics_label.grid  (row=0, column=0, sticky=tk.W) #(tk.N,tk.W,tk.E,tk.S))
        self.interface_generics_info.grid   (row=0, column=0, sticky=tk.E)
        self.interface_generics_text.grid   (row=1, column=0, sticky=(tk.N,tk.W,tk.E,tk.S))
        self.interface_generics_scroll.grid (row=1, column=1, sticky=(tk.W,tk.E,tk.S,tk.N)) # "W,E" nötig, damit Text tatsächlich breiter wird
        self.paned_window.add(self.generics_frame, weight=1)

        notebook.add(self.paned_window, sticky=tk.N+tk.E+tk.W+tk.S, text="Entity Declarations")

    def update_interface_tab_from(self, new_dict):
        self.interface_packages_text.insert_text(new_dict["text_dictionary"]["interface_packages"], state_after_insert="normal")
        self.interface_packages_text.store_change_in_text_dictionary(signal_design_change=False)
        self.interface_generics_text.insert_text(new_dict["text_dictionary"]["interface_generics"], state_after_insert="normal")
        self.interface_generics_text.store_change_in_text_dictionary(signal_design_change=False)

    def find_string(self, search_string, replace, new_string):
        if self.window.design.get_language()=="VHDL":
            all_text_widgets = [self.interface_packages_text, self.interface_generics_text]
        else:
            all_text_widgets = [self.interface_generics_text]
        number_of_matches = 0
        for text_widget in all_text_widgets:
            index = "1.0"
            while index!="":
                index = text_widget.search(search_string, index, nocase=1, stopindex=tk.END)
                if index!="":
                    number_of_matches += 1
                    if replace:
                        end_index = index + "+" + str(len(search_string)) + " chars"
                        text_widget.delete(index, end_index)
                        text_widget.insert(index, new_string)
                        index = index + "+" + str(len(new_string)) + " chars"
                        text_widget.store_change_in_text_dictionary(signal_design_change=True)
                    else:
                        if self.window.design.get_language()=="VHDL":
                            self.window.notebook_top.show_tab("Entity Declarations")
                        else:
                            self.window.notebook_top.show_tab("Parameters")
                        index2 = index + " + " + str(len(search_string)) + " chars"
                        text_widget.tag_add      ("selected", index, index2)
                        text_widget.tag_configure("selected", background="blue")
                        text_widget.see(index)
                        continue_search = messagebox.askyesno("Continue ...", "Find next?")
                        text_widget.tag_remove   ("selected", index, index2)
                        if not continue_search:
                            return -1
                        index = index2
        return number_of_matches

    def copy_all_information_from_tab_in_empty_design_data(self):
        self.interface_packages_text.store_change_in_text_dictionary(signal_design_change=False)
        self.interface_generics_text.store_change_in_text_dictionary(signal_design_change=False)
