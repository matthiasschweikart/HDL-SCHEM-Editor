""" Create text fields for internal declarations """
import tkinter as tk
from   tkinter import ttk
from   tkinter import messagebox

import custom_text
import vhdl_parsing

class NotebookInternalsTab():
    def __init__(self, schematic_window, notebook):
        self.window = schematic_window
        self.paned_window = ttk.PanedWindow(notebook, orient=tk.VERTICAL, takefocus=True)

        self.internals_packages_frame = ttk.Frame(notebook)
        self.internals_packages_frame.grid()
        self.internals_packages_frame.columnconfigure(0, weight=1)
        self.internals_packages_frame.rowconfigure   (0, weight=0)
        self.internals_packages_frame.rowconfigure   (1, weight=1)
        self.internals_packages_label  = ttk.Label             (self.internals_packages_frame, text="Packages:", padding=5)
        self.internals_packages_info   = ttk.Label             (self.internals_packages_frame, text="Undo/Redo: Ctrl-z/Ctrl-y/Z", padding=5)
        self.internals_packages_text   = custom_text.CustomText(self.internals_packages_frame, window=self.window, parser=vhdl_parsing.VhdlParser,
                                                                tag_position_list=vhdl_parsing.VhdlParser.tag_position_list, font=("Courier", 10),
                                                                text_name="internals_packages", height=3, width=10, undo=True, maxundo=-1)
        self.internals_packages_scroll = ttk.Scrollbar         (self.internals_packages_frame, orient=tk.VERTICAL, cursor='arrow', command=self.internals_packages_text.yview)
        self.internals_packages_text.config(yscrollcommand=self.internals_packages_scroll.set)
        self.internals_packages_label.grid              (row=0, column=0, sticky=tk.W) # "W" nötig, damit Text links bleibt
        self.internals_packages_info.grid               (row=0, column=0, sticky=tk.E)
        self.internals_packages_text.grid               (row=1, column=0, sticky=(tk.W,tk.E,tk.S,tk.N)) # "W,E" nötig, damit Text tatsächlich breiter wird
        self.internals_packages_scroll.grid             (row=1, column=1, sticky=(tk.W,tk.E,tk.S,tk.N)) # "W,E" nötig, damit Text tatsächlich breiter wird
        self.paned_window.add(self.internals_packages_frame, weight=1)

        self.architecture_first_declarations_frame = ttk.Frame(notebook)
        self.architecture_first_declarations_frame.grid()
        self.architecture_first_declarations_frame.columnconfigure(0, weight=1)
        self.architecture_first_declarations_frame.rowconfigure   (0, weight=0)
        self.architecture_first_declarations_frame.rowconfigure   (1, weight=1)
        self.architecture_first_declarations_label = ttk.Label             (self.architecture_first_declarations_frame, text="Architecture First Declarations:", padding=5)
        self.architecture_first_declarations_info  = ttk.Label             (self.architecture_first_declarations_frame, text="Undo/Redo: Ctrl-z/Ctrl-y/Z", padding=5)
        self.architecture_first_declarations_text  = custom_text.CustomText(self.architecture_first_declarations_frame, window=self.window, parser=vhdl_parsing.VhdlParser,
                                                                            tag_position_list=vhdl_parsing.VhdlParser.tag_position_list, font=("Courier", 10),
                                                                            text_name="architecture_first_declarations", height=3, width=10, undo=True, maxundo=-1)
        self.architecture_first_declarations_scroll= ttk.Scrollbar         (self.architecture_first_declarations_frame, orient=tk.VERTICAL, cursor='arrow',
                                                                            command=self.architecture_first_declarations_text.yview)
        self.architecture_first_declarations_text.config(yscrollcommand=self.architecture_first_declarations_scroll.set)
        self.architecture_first_declarations_label.grid (row=0, column=0, sticky=tk.W)
        self.architecture_first_declarations_info.grid  (row=0, column=0, sticky=tk.E)
        self.architecture_first_declarations_text.grid  (row=1, column=0, sticky=(tk.N,tk.W,tk.E,tk.S))
        self.architecture_first_declarations_scroll.grid(row=1, column=1, sticky=(tk.W,tk.E,tk.S,tk.N)) # "W,E" nötig, damit Text tatsächlich breiter wird
        self.paned_window.add(self.architecture_first_declarations_frame, weight=8)

        self.architecture_last_declarations_frame = ttk.Frame(notebook)
        self.architecture_last_declarations_frame.grid()
        self.architecture_last_declarations_frame.columnconfigure(0, weight=1)
        self.architecture_last_declarations_frame.rowconfigure   (0, weight=0)
        self.architecture_last_declarations_frame.rowconfigure   (1, weight=1)
        self.architecture_last_declarations_label  = ttk.Label             (self.architecture_last_declarations_frame, text="Architecture Last Declarations:", padding=5)
        self.architecture_last_declarations_info   = ttk.Label             (self.architecture_last_declarations_frame, text="Undo/Redo: Ctrl-z/Ctrl-y/Z", padding=5)
        self.architecture_last_declarations_text   = custom_text.CustomText(self.architecture_last_declarations_frame, window=self.window, parser=vhdl_parsing.VhdlParser,
                                                                            tag_position_list=vhdl_parsing.VhdlParser.tag_position_list, font=("Courier", 10),
                                                                            text_name="architecture_last_declarations", height=3, width=10, undo=True, maxundo=-1)
        self.architecture_last_declarations_scroll = ttk.Scrollbar         (self.architecture_last_declarations_frame, orient=tk.VERTICAL, cursor='arrow',
                                                                            command=self.architecture_last_declarations_text.yview)
        self.architecture_last_declarations_text.config(yscrollcommand=self.architecture_last_declarations_scroll.set)
        self.architecture_last_declarations_label.grid  (row=0, column=0, sticky=tk.W)
        self.architecture_last_declarations_info.grid   (row=0, column=0, sticky=tk.E)
        self.architecture_last_declarations_text.grid   (row=1, column=0, sticky=(tk.N,tk.W,tk.E,tk.S))
        self.architecture_last_declarations_scroll.grid (row=1, column=1, sticky=(tk.W,tk.E,tk.S,tk.N)) # "W,E" nötig, damit Text tatsächlich breiter wird
        self.paned_window.add(self.architecture_last_declarations_frame, weight=1)

        notebook.add(self.paned_window, sticky=tk.N+tk.E+tk.W+tk.S, text="Architecture Declarations")

    def update_internals_tab_from(self, new_dict):
        self.internals_packages_text.insert_text(new_dict["text_dictionary"]["internals_packages"], state_after_insert="normal")
        self.internals_packages_text.store_change_in_text_dictionary(signal_design_change=False)

        self.architecture_first_declarations_text.insert_text(new_dict["text_dictionary"]["architecture_first_declarations"], state_after_insert="normal")
        self.architecture_first_declarations_text.store_change_in_text_dictionary(signal_design_change=False)

        self.architecture_last_declarations_text.insert_text(new_dict["text_dictionary"]["architecture_last_declarations"], state_after_insert="normal")
        self.architecture_last_declarations_text.store_change_in_text_dictionary(signal_design_change=False)

    def find_string(self, search_string, replace, new_string):
        if self.window.design.get_language()=="VHDL":
            all_text_widgets = [self.internals_packages_text, self.architecture_first_declarations_text, self.architecture_last_declarations_text]
        else:
            all_text_widgets = [self.architecture_first_declarations_text]
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
                            self.window.notebook_top.show_tab("Architecture Declarations")
                        else:
                            self.window.notebook_top.show_tab("Internal Declarations")
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

    def clear(self):
        self.internals_packages_text             .delete("1.0", "end")
        self.architecture_first_declarations_text.delete("1.0", "end")
        self.architecture_last_declarations_text .delete("1.0", "end")
