""" Configures the schematic editor """
import os
import re
import tkinter as tk
from   tkinter import ttk
from   tkinter import messagebox
from   tkinter.filedialog import askdirectory
from   tkinter.filedialog import askopenfilename

import vhdl_parsing
import verilog_parsing
import edit_ext

class NotebookControlTab():
    def __init__(self, schematic_window, notebook, working_dir):
        self.window                     = schematic_window
        self.notebook                   = notebook
        self.vhdl_compile_cmd1          = "ghdl -a $file3; ghdl -e $name; ghdl -r $name"
        self.vhdl_compile_cmd2          = "ghdl -a $file1 $file2; ghdl -e $name; ghdl -r $name"
        self.vhdl_compile_hierarchy     = "compile.bat $name $hdl-file-list"
        self.verilog_compile_cmd        = "iverilog -o $name $file; vvp $name"
        self.system_verilog_compile_cmd = "iverilog -g2012 -o $name $file; vvp $name"

        self.trace_module_name_id      = None
        self.trace_language_id         = None
        self.trace_number_of_files_id1 = None
        self.trace_number_of_files_id2 = None
        self.trace_compile_cmd_id      = None
        self.trace_compile_cmd_id_hier = None
        self.trace_edit_cmd_id         = None
        self.trace_hfe_cmd_id          = None

        self.control_frame = ttk.Frame(notebook, takefocus=False) #, relief="raised")
        self.control_frame.grid()
        self.control_frame.columnconfigure(0, weight=0)
        self.control_frame.columnconfigure(1, weight=1)
        self.control_frame.columnconfigure(2, weight=0)

        self.module_name = tk.StringVar()
        self.module_name_label  = ttk.Label (self.control_frame, text="Module-Name:", padding=5)
        self.module_name_entry  = ttk.Entry (self.control_frame, textvariable=self.module_name, takefocus=False)
        self.module_name_label.grid (row=0, column=0, sticky=tk.W)
        self.module_name_entry.grid (row=0, column=1, sticky=(tk.W,tk.E))
        self.module_name_entry.select_clear()

        self.language = tk.StringVar()
        self.language_label    = ttk.Label   (self.control_frame, text="Language:", padding=5)
        self.language_combobox = ttk.Combobox(self.control_frame, textvariable=self.language, values=("VHDL", "Verilog", "SystemVerilog"), state="readonly")
        self.language_combobox.bind("<<ComboboxSelected>>", lambda event : self.__switch_language_mode(schematic_window, check=True))
        self.language_label.grid   (row=1, column=0, sticky=tk.W)
        self.language_combobox.grid(row=1, column=1, sticky=tk.W)

        self.generate_path_value  = tk.StringVar(value="")
        self.generate_path_label  = ttk.Label (self.control_frame, text="Path for generated HDL:", padding=5)
        self.generate_path_entry  = ttk.Entry (self.control_frame, textvariable=self.generate_path_value)
        self.generate_path_button = ttk.Button(self.control_frame, text="Select ...",  command=self.set_path)
        self.generate_path_label.grid (row=2, column=0, sticky=tk.W)
        self.generate_path_entry.grid (row=2, column=1, sticky=(tk.W,tk.E))
        self.generate_path_button.grid(row=2, column=2, sticky=tk.E)

        self.number_of_files = tk.IntVar()
        self.number_of_files.set(2)
        self.include_timestamp_in_hdl = tk.BooleanVar(value=True)
        self.select_file_number_label = ttk.Label(self.control_frame, text="Select for generation:", padding=5)
        self.select_file_number_frame = ttk.Frame(self.control_frame)
        self.select_file_number_label.grid(row=3, column=0, sticky=tk.W)
        self.select_file_number_frame.grid(row=3, column=1, sticky=tk.W)
        self.include_timestamp_in_hdl_checkbox = ttk.Checkbutton(self.select_file_number_frame, variable=self.include_timestamp_in_hdl, width=40,
                                                                 text="Include timestamp in generated HDL files")
        self.select_file_number_radio_button1  = ttk.Radiobutton(self.select_file_number_frame, takefocus=False, variable=self.number_of_files, text="1 file" , value=1)
        self.select_file_number_radio_button2  = ttk.Radiobutton(self.select_file_number_frame, takefocus=False, variable=self.number_of_files, text="2 files", value=2)
        self.include_timestamp_in_hdl_checkbox.grid(row=0, column=0, sticky=tk.W)
        self.select_file_number_radio_button1.grid (row=0, column=1, sticky=tk.W)
        self.select_file_number_radio_button2.grid (row=0, column=2, sticky=tk.W)

        self.compile_cmd = tk.StringVar()
        self.compile_cmd_label  = ttk.Label (self.control_frame, text="Compile command\nfor single module:", padding=5)
        self.compile_cmd_entry  = ttk.Entry (self.control_frame, textvariable=self.compile_cmd)
        self.compile_cmd_label.grid (row=6, column=0, sticky=tk.W)
        self.compile_cmd_entry.grid (row=6, column=1, sticky=(tk.W,tk.E))

        self.compile_cmd_docu  = ttk.Label (self.control_frame,
                                text="Variables for compile command:\n" +
                                     "$file1\t\t= Entity-File\n" +
                                     "$file2\t\t= Architecture-File\n" +
                                     "$file3\t\t= File with Entity and Architecture\n" +
                                     "$name\t\t= Module Name",
                                padding=0)
        self.compile_cmd_docu.grid (row=7, column=1, sticky=tk.W)

        self.compile_hierarchy_cmd = tk.StringVar()
        self.compile_hierarchy_cmd_label  = ttk.Label (self.control_frame, text="Compile through\nhierarchy command:", padding=5)
        self.compile_hierarchy_cmd_entry  = ttk.Entry (self.control_frame, textvariable=self.compile_hierarchy_cmd)
        self.compile_hierarchy_cmd_label.grid (row=8, column=0, sticky=tk.W)
        self.compile_hierarchy_cmd_entry.grid (row=8, column=1, sticky=(tk.W,tk.E))

        self.compile_hierarchy_cmd_docu  = ttk.Label (self.control_frame,
                                text="Variables for compile through hierarchy command:\n" +
                                     "$name\t\t= Module Name\n" +
                                     "$hdl-file-list\t= Name of the hdl-file-list generated by HDL-SCHEM-Editor",
                                padding=0)
        self.compile_hierarchy_cmd_docu.grid (row=9, column=1, sticky=tk.W)

        self.edit_cmd = tk.StringVar()
        self.edit_cmd_label  = ttk.Label (self.control_frame, text="Edit command (Ctrl+e):", padding=5)
        self.edit_cmd_entry  = ttk.Entry (self.control_frame, textvariable=self.edit_cmd)
        self.edit_cmd_label.grid (row=10, column=0, sticky=tk.W)
        self.edit_cmd_entry.grid (row=10, column=1, sticky=(tk.W,tk.E))

        self.hfe_cmd = tk.StringVar()
        self.hfe_cmd_label  = ttk.Label (self.control_frame, text="HDL-FSM-Editor command:", padding=5)
        self.hfe_cmd_entry  = ttk.Entry (self.control_frame, textvariable=self.hfe_cmd)
        self.hfe_cmd_label.grid (row=11, column=0, sticky=tk.W)
        self.hfe_cmd_entry.grid (row=11, column=1, sticky=(tk.W,tk.E))

        self.module_library = tk.StringVar()
        self.module_library_label  = ttk.Label (self.control_frame,
                                                text="Symbolic library for the module:\n(used at hdl-file-list generation)",
                                                padding=5)
        self.module_library_entry  = ttk.Entry (self.control_frame, textvariable=self.module_library)
        self.module_library_label.grid (row=12, column=0, sticky=tk.W)
        self.module_library_entry.grid (row=12, column=1, sticky=(tk.W,tk.E))

        self.additional_sources = tk.StringVar()
        self.additional_sources_label  = ttk.Label (self.control_frame,
                                                text="Additional sources for the module:\n(used at hdl-file-list generation\n for hierarchical compile)\n(edit with Ctrl+e)",
                                                padding=5)
        self.additional_sources_entry  = ttk.Entry (self.control_frame, textvariable=self.additional_sources)
        self.additional_sources_entry.bind("<Control-e>", lambda event: self.__edit_ext())
        self.additional_sources_add    = ttk.Button(self.control_frame, text="Add ...", command=self.__add_path)
        self.additional_sources_label.grid (row=13, column=0, sticky=tk.W)
        self.additional_sources_entry.grid (row=13, column=1, sticky=(tk.W,tk.E))
        self.additional_sources_add  .grid (row=13, column=2, sticky=tk.E)

        self.working_directory = tk.StringVar()
        self.working_directory_label  = ttk.Label (self.control_frame,
                                                text="Working directory:",
                                                padding=5)
        self.working_directory_entry  = ttk.Entry (self.control_frame, textvariable=self.working_directory)
        self.working_directory_add    = ttk.Button(self.control_frame, text="Select ...", command=self.__select_working_directory)
        self.working_directory_label.grid (row=14, column=0, sticky=tk.W)
        self.working_directory_entry.grid (row=14, column=1, sticky=(tk.W,tk.E))
        self.working_directory_add  .grid (row=14, column=2, sticky=tk.E)

        self.signal_design_change = False # Must be defined before the first call of __add_traces().
        self.__add_traces()
        self.language             .set("VHDL")
        self.compile_cmd          .set(self.vhdl_compile_cmd2)
        self.compile_hierarchy_cmd.set(self.vhdl_compile_hierarchy)
        self.edit_cmd             .set("C:/Program Files/Notepad++/notepad++.exe -nosession -multiInst")
        self.hfe_cmd              .set("hdl_fsm_editor.exe")
        self.working_directory    .set(working_dir)
        #print("notebook_control: working-dir wurde gesetzt:", working_dir)
        self.signal_design_change = True
        self.old_module_name_saved = None

        notebook.add(self.control_frame, sticky=tk.N+tk.E+tk.W+tk.S, text="Control")

    def __edit_ext(self):
        cursor_index            = self.additional_sources_entry.index(tk.INSERT)
        additional_sources_list = self.additional_sources.get().split(',')
        string_length = 0
        for additional_source_file_name in additional_sources_list:
            string_length += len(additional_source_file_name)
            if cursor_index<=string_length:
                edit_ext.EditExt(self.window.design, additional_source_file_name.strip())
                break

    def __add_path(self):
        old_entry = self.additional_sources.get()
        if old_entry!="":
            old_entries = old_entry.split(',')
            path = askopenfilename(initialdir=os.path.dirname(old_entries[0]))
        else:
            path = askopenfilename()
        if path!="":
            if old_entry=="":
                self.additional_sources.set(path)
            else:
                self.additional_sources.set(old_entry + ', ' + path)

    def __select_working_directory(self):
        path = askdirectory(title="Select a folder as working directory:", initialdir=self.working_directory.get())
        if path!="":
            self.working_directory.set(path)

    def set_path(self):
        path = askdirectory(title="Select a folder for storing HDL:", initialdir=self.generate_path_value.get())
        if path!="":
            self.generate_path_value.set(path)

    def __adapt_compile_cmd(self):
        if self.number_of_files.get()==1:
            self.compile_cmd.set(self.vhdl_compile_cmd1)
        else:
            self.compile_cmd.set(self.vhdl_compile_cmd2)

    def __switch_language_mode(self, schematic_window, check):
        self.__configure_parsers()
        self.new_language = self.language.get()
        if check and schematic_window.design.get_numbers_of_wires()!=0:
            messagebox.showerror("Warning", "There are already wire/signal definitions present in your design. You must convert them manually.")
        if self.new_language=="VHDL":
            # enable 2 files mode
            self.number_of_files.set(2)
            self.select_file_number_radio_button1.grid (row=0, column=2, sticky=tk.E)
            self.select_file_number_radio_button2.grid (row=0, column=3, sticky=tk.E)
            # Modify compile command:
            self.compile_cmd.set(self.vhdl_compile_cmd2)
            self.compile_cmd_docu.config(text=
                "Variables for compile command:\n$file1\t= Entity-File\n$file2\t= Architecture-File\n$file3\t= File with Entity and Architecture\n$name\t= Entity Name")
            self.notebook.tab(1, text="Entity Declarations")
            self.window.notebook_top.interface_tab.paned_window.insert(0, self.window.notebook_top.interface_tab.packages_frame, weight=1)
            self.window.notebook_top.interface_tab.interface_generics_label.config(text="Generics:")
            self.window.notebook_top.interface_tab.interface_packages_text.insert_text("library ieee;\nuse ieee.std_logic_1164.all;", state_after_insert="normal")
            self.window.notebook_top.interface_tab.interface_packages_text.store_change_in_text_dictionary(signal_design_change=False)
            self.notebook.tab(2, text="Architecture Declarations")
            self.window.notebook_top.internals_tab.paned_window.insert(0, self.window.notebook_top.internals_tab.internals_packages_frame, weight=1)
            self.window.notebook_top.internals_tab.paned_window.add(self.window.notebook_top.internals_tab.architecture_last_declarations_frame, weight=1)
            self.window.notebook_top.internals_tab.architecture_first_declarations_label.config(text="Architecture First Declarations:")
            self.window.notebook_top.diagram_tab.architecture_frame.grid(row=0, column=0, sticky=(tk.W,tk.E,tk.N))
        else: # "Verilog" or "SystemVerilog"
            # Control: disable 2 files mode
            self.number_of_files.set(1)
            self.select_file_number_radio_button1.grid_forget()
            self.select_file_number_radio_button2.grid_forget()
            # Modify compile command:
            if self.new_language=="Verilog":
                self.compile_cmd.set(self.verilog_compile_cmd)
            else:
                self.compile_cmd.set(self.system_verilog_compile_cmd)
            self.compile_cmd_docu.config(text="Variables for compile command:\n$file\t= Module-File\n$name\t= Module Name")
            self.notebook.tab(1, text="Parameters")
            self.window.notebook_top.interface_tab.paned_window.forget(self.window.notebook_top.interface_tab.packages_frame)
            self.window.notebook_top.interface_tab.interface_generics_label.config(text="Parameters:")
            self.notebook.tab(2, text="Internal Declarations")
            self.window.notebook_top.internals_tab.paned_window.forget(self.window.notebook_top.internals_tab.internals_packages_frame)
            self.window.notebook_top.internals_tab.paned_window.forget(self.window.notebook_top.internals_tab.architecture_last_declarations_frame)
            self.window.notebook_top.internals_tab.internals_packages_text.delete("1.0", tk.END)
            self.window.notebook_top.internals_tab.architecture_last_declarations_text.delete("1.0", tk.END)
            self.window.notebook_top.internals_tab.architecture_first_declarations_label.config(text="Internal Declarations:")
            self.window.notebook_top.diagram_tab.architecture_frame.grid_forget()

    def update_control_tab_from(self, new_dict):
        self.signal_design_change = False
        self.module_name.set             (new_dict["module_name"])
        self.generate_path_value.set     (new_dict["generate_path_value"])
        if new_dict["language"]!=self.language.get():
            self.language.set            (new_dict["language"])
            self.__switch_language_mode(self.window, check=False)
        else:
            self.__configure_parsers()
        self.number_of_files.set         (new_dict["number_of_files"])         # must be set before compile_cmd, because the trace of number_of_files modifies the compile_cmd.
        if "include_timestamp_in_hdl" in new_dict:
            self.include_timestamp_in_hdl.set(new_dict["include_timestamp_in_hdl"])
        self.edit_cmd.set                (new_dict["edit_cmd"])
        self.hfe_cmd.set                 (new_dict["hfe_cmd"])
        self.module_library.set          (new_dict["module_library"])
        self.additional_sources.set      (new_dict["additional_sources"])
        if "working_directory" in new_dict:
            self.working_directory.set   (new_dict["working_directory"])
        else:
            self.working_directory.set   ("")
        self.compile_cmd.set             (new_dict["compile_cmd"])             # must be set after number_of_files, because the trace of number_of_files modifies the compile_cmd.
        self.compile_hierarchy_cmd.set   (new_dict["compile_hierarchy_cmd"])
        self.signal_design_change = True

    def __add_traces(self):
        self.trace_module_name_id         = self.module_name.trace_add(
            'write', lambda *args: self.__store_new_module_name())
        self.trace_language_id            = self.language.trace_add(
            'write', lambda *args: self.window.design.store_new_language(self.language, self.signal_design_change))
        self.trace_generate_path_value_id = self.generate_path_value.trace_add(
            'write', lambda *args: self.window.design.store_generate_path_value(self.generate_path_value, self.signal_design_change))
        self.trace_number_of_files_id1    = self.number_of_files.trace_add(
            'write', lambda *args: self.window.design.store_number_of_files(self.number_of_files, self.signal_design_change))
        self.trace_number_of_files_id2    = self.number_of_files.trace_add(
            'write', lambda *args: self.__adapt_compile_cmd())
        self.trace_compile_cmd_id         = self.compile_cmd.trace_add(
            'write', lambda *args: self.window.design.store_compile_cmd(self.compile_cmd, self.signal_design_change))
        self.trace_compile_cmd_id_hier    = self.compile_hierarchy_cmd.trace_add(
            'write', lambda *args: self.window.design.store_compile_hierarchy_cmd(self.compile_hierarchy_cmd, self.signal_design_change))
        self.trace_edit_cmd_id            = self.edit_cmd.trace_add(
            'write', lambda *args: self.window.design.store_new_edit_command(self.edit_cmd, self.signal_design_change))
        self.trace_hfe_cmd_id             = self.hfe_cmd.trace_add(
            'write', lambda *args: self.window.design.store_new_hfe_command(self.hfe_cmd, self.signal_design_change))
        self.trace_module_library_id      = self.module_library.trace_add(
            'write', lambda *args: self.window.design.store_module_library(self.module_library, self.signal_design_change))
        self.trace_additional_sources_id  = self.additional_sources.trace_add(
            'write', lambda *args: self.window.design.store_additional_sources(self.additional_sources, self.signal_design_change))
        self.trace_working_directory_id  = self.working_directory.trace_add(
            'write', lambda *args: self.window.design.store_working_directory(self.working_directory, self.signal_design_change))
        self.trace_include_timestamp_in_hdl_id = self.include_timestamp_in_hdl.trace_add(
            "write", lambda *args: self.window.design.store_include_timestamp_in_hdl(self.include_timestamp_in_hdl, self.signal_design_change))

    def __store_new_module_name(self):
        # Remember the old name for the situation when editing the module-name-field causes temporarily an empty string as result:
        old_module_name = self.window.design.get_module_name()
        if old_module_name=="":
            old_module_name = self.old_module_name_saved
        else:
            self.old_module_name_saved = old_module_name
        # Store the changed name:
        self.window.design.store_new_module_name(self.module_name, self.signal_design_change) # self.module_name is a StringVar
        # Change the name of the quick_access-button:
        new_module_name = self.window.design.get_module_name()
        if (old_module_name is not None and # No name change when the window is created.
            new_module_name!=""):           # No name change when the new name is an empty string.
            #self.window.notebook_top.diagram_tab.change_name_of_open_module_button_in_all_windows_after_module_name_change(old_module_name, new_module_name)
            self.window.quick_access_object.change_name_of_quick_access_button_in_all_windows_after_module_name_change(old_module_name, new_module_name)

    def copy_all_information_from_tab_in_empty_design_data(self):
        signal_design_change = False
        self.window.design.store_new_module_name      (self.module_name          , signal_design_change)
        self.window.design.store_new_language         (self.language             , signal_design_change)
        self.window.design.store_generate_path_value  (self.generate_path_value  , signal_design_change)
        self.window.design.store_number_of_files      (self.number_of_files      , signal_design_change)
        self.window.design.store_compile_cmd          (self.compile_cmd          , signal_design_change)
        self.window.design.store_compile_hierarchy_cmd(self.compile_hierarchy_cmd, signal_design_change)
        self.window.design.store_new_edit_command     (self.edit_cmd             , signal_design_change)
        self.window.design.store_new_hfe_command      (self.hfe_cmd              , signal_design_change)
        self.window.design.store_module_library       (self.module_library       , signal_design_change)
        self.window.design.store_additional_sources   (self.additional_sources   , signal_design_change)
        self.window.design.store_working_directory    (self.working_directory    , signal_design_change)

    def __configure_parsers(self):
        vhdl_custom_text_list = (
            self.window.notebook_top.interface_tab.interface_packages_text,
            self.window.notebook_top.interface_tab.interface_generics_text,
            self.window.notebook_top.internals_tab.internals_packages_text,
            self.window.notebook_top.internals_tab.architecture_first_declarations_text,
            self.window.notebook_top.internals_tab.architecture_last_declarations_text,
            self.window.notebook_top.hdl_tab.hdl_frame_text)
        verilog_custom_text_list = (
            self.window.notebook_top.interface_tab.interface_generics_text,
            self.window.notebook_top.internals_tab.architecture_first_declarations_text,
            self.window.notebook_top.hdl_tab.hdl_frame_text)
        if self.language.get()=="VHDL":
            for customtext in vhdl_custom_text_list:
                customtext.set_parser(vhdl_parsing.VhdlParser)
                customtext.set_taglist(vhdl_parsing.VhdlParser.tag_position_list)
        else:
            for customtext in verilog_custom_text_list:
                customtext.set_parser(verilog_parsing.VerilogParser)
                customtext.set_taglist(verilog_parsing.VerilogParser.tag_position_list)

    def highlight_item(self, *_):
        self.module_name_entry.select_range(0, tk.END)

    def find_string(self, search_string, replace, new_string) -> int:
        number_of_all_hits = 0
        entry_widget_infos = self._get_entry_widget_info()
        for entry_widget_info in entry_widget_infos:
            number_of_hits = self._search_in_entry_widget(entry_widget_info, search_string, replace, new_string)
            if number_of_hits==-1:
                return -1
            number_of_all_hits += number_of_hits
        return number_of_all_hits

    def _get_entry_widget_info(self) -> list:
        entry_widgets = [
            {"stringvar": self.module_name, "entry": self.module_name_entry},
            {"stringvar": self.generate_path_value, "entry": self.generate_path_entry},
            {"stringvar": self.compile_cmd, "entry": self.compile_cmd_entry},
            {"stringvar": self.compile_hierarchy_cmd, "entry": self.compile_hierarchy_cmd_entry},
            {"stringvar": self.edit_cmd, "entry": self.edit_cmd_entry},
            {"stringvar": self.module_library, "entry": self.module_library_entry},
            {"stringvar": self.additional_sources, "entry": self.additional_sources_entry},
            {"stringvar": self.working_directory, "entry": self.working_directory_entry},
        ]
        return entry_widgets

    def _search_in_entry_widget(self, entry_widget_info, search_string, replace, new_string) -> int:
        value = entry_widget_info["stringvar"].get()
        number_of_hits = 0
        start = 0
        while True:
            hit_begin = value.find(search_string, start, len(value))
            if hit_begin == -1:
                break
            if replace:
                # All hits are replaced in 1 action:
                search_pattern_escaped = re.escape(search_string)
                replace_pattern_escaped = re.escape(new_string)
                number_of_hits += len(re.findall(search_pattern_escaped, value, flags=re.IGNORECASE))
                value = re.sub(search_pattern_escaped, replace_pattern_escaped, value, flags=re.IGNORECASE)
                entry_widget_info["stringvar"].set(value)
                start = len(value)  # The search-pattern cannot be found again in the next loop.
            else:
                number_of_hits += 1
                self.window.notebook_top.show_tab("Control")
                entry_widget_info["entry"].select_range(hit_begin, hit_begin + len(search_string))
                if not messagebox.askyesno("Continue", "Find next"):
                    return -1
                start = hit_begin + len(search_string)
            if start == hit_begin:
                messagebox.showinfo(
                    "HDL-SCHEM-Editor",
                    "Search in entry field of Control-tab is aborted as for unknown reason no progress happens.",
                )
                return -1
        return number_of_hits
