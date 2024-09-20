"""
This class opens a window, where the user can modify:
Library name, which can be used for a VHDL-configuration-specification.
Sort of VHDL-configuration-specification: None, embedded configuration, entity-specification
File-name(s) of the source-file(s) of the instance.
Additional directories, where files are located which belong to the instance.
"""
import tkinter as tk
from   tkinter import messagebox
from   tkinter import ttk
from   tkinter.filedialog import askopenfilename
import re

class SymbolProperties():
    def __init__(self, symbol):
        self.property_window = tk.Toplevel()
        self.property_window.title("Instance properties window")
        self.property_window.resizable(True, False)
        self.symbol          = symbol
        if self.symbol.symbol_definition["language"]=="VHDL":
            instance_name = self.symbol.symbol_definition["instance_name"]["name"]
            instance_name = re.sub(r"\s*--.*", "", instance_name)
            configuration_label  = ttk.Label(self.property_window,
                                                text="VHDL Configuration for " + instance_name + ':', padding=5, style="My.TLabel")
        else:
            configuration_label  = ttk.Label(self.property_window,
                                                text="Symbolic library name into which " +
                                                self.symbol.symbol_definition["entity_name"]["name"] +
                                                ' will be compiled (information for hdl-file-list only):',
                                                padding=5, style="My.TLabel")
        configuration_frame  = tk.Frame (self.property_window)
        source_label         = ttk.Label(self.property_window, text="Source of " + self.symbol.symbol_definition["entity_name"]["name"] + ':', padding=5, style="My.TLabel")
        source_frame         = tk.Frame (self.property_window)
        appearance_label     = ttk.Label(self.property_window, text="Appearance:", padding=5, style="My.TLabel")
        appearance_frame     = tk.Frame (self.property_window)
        button_frame         = tk.Frame (self.property_window)

        self.property_window.columnconfigure(0, weight=1)
        configuration_label.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.S, tk.N))
        configuration_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.S, tk.N))
        source_label.grid       (row=2, column=0, sticky=(tk.W, tk.E))
        source_frame.grid       (row=3, column=0, sticky=(tk.W, tk.E, tk.S, tk.N))
        appearance_label.grid   (row=4, column=0, sticky=(tk.W, tk.E))
        appearance_frame.grid   (row=5, column=0, sticky=(tk.W, tk.E, tk.S, tk.N))
        button_frame.grid       (row=6, column=0, sticky=(tk.W, tk.E))

        if self.symbol.symbol_definition["language"]=="VHDL":
            self.old_library_name = self.symbol.symbol_definition["configuration"]["library"]
            self.library_name = tk.StringVar()
            self.library_name.set(self.old_library_name)
            config_lib_label = ttk.Label      (configuration_frame, text="VHDL Library Name for instance:", padding=5)
            config_lib_entry = ttk.Entry      (configuration_frame, width=23, textvariable=self.library_name)
            config_statement = ttk.Label      (configuration_frame, text="Configuration Statement:", padding=5)
            self.old_configuration = self.symbol.symbol_definition["configuration"]["config_statement"]
            self.config_var  = tk.StringVar() # Must be a attribute (self.), only then set() works.
            self.config_var.set(self.old_configuration)
            config_button1   = ttk.Radiobutton(configuration_frame, takefocus=False, variable=self.config_var, value="None"       , padding=5, text="None")
            config_button2   = ttk.Radiobutton(configuration_frame, takefocus=False, variable=self.config_var, value="Embedded"   , padding=5, text="Embedded")
            config_button3   = ttk.Radiobutton(configuration_frame, takefocus=False, variable=self.config_var, value="At Instance", padding=5, text="At Instance")
            self.old_architecture = self.symbol.symbol_definition["architecture_name"]
            self.arch_var = tk.StringVar() # Must be an attribute (self.), only then set() works.
            self.arch_var.set(self.old_architecture)
            config_arch_label = ttk.Label(configuration_frame, text="VHDL Architecture Name for instance:", padding=5)
            if "architecture_list" in self.symbol.symbol_definition:
                combobox_list = self.symbol.symbol_definition["architecture_list"]
            else:
                combobox_list = [] # Old designs do not have an "architecture_list"
            config_arch_entry = ttk.Combobox(configuration_frame, textvariable=self.arch_var, values=combobox_list)
            config_arch_entry.selection_clear()
            config_arch_entry.bind("<<ComboboxSelected>>", lambda event : config_arch_entry.selection_clear())
            config_arch_empty1= ttk.Label(configuration_frame, text="", padding=5)
            config_arch_empty2= ttk.Label(configuration_frame, text="", padding=5)
            config_arch_empty3= ttk.Label(configuration_frame, text="", padding=5)
            config_arch_empty4= ttk.Label(configuration_frame, text="", padding=5)
            configuration_frame.columnconfigure(5, weight=1)
            config_lib_label.grid  (row=0, column=0, sticky=(tk.W, tk.E))
            config_lib_entry.grid  (row=0, column=1, sticky=(tk.W, tk.E, tk.S, tk.N))
            config_statement.grid  (row=0, column=2, sticky=(tk.W, tk.E))
            config_button1.grid    (row=0, column=3, sticky=(tk.W, tk.E))
            config_button2.grid    (row=0, column=4, sticky=(tk.W, tk.E))
            config_button3.grid    (row=0, column=5, sticky=(tk.W, tk.E))
            config_arch_label.grid (row=1, column=0, sticky=(tk.W, tk.E))
            config_arch_entry.grid (row=1, column=1, sticky=(tk.W, tk.E, tk.S, tk.N))
            config_arch_empty1.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.S, tk.N))
            config_arch_empty2.grid(row=1, column=3, sticky=(tk.W, tk.E))
            config_arch_empty3.grid(row=1, column=4, sticky=(tk.W, tk.E))
            config_arch_empty4.grid(row=1, column=5, sticky=(tk.W, tk.E))
        else:
            self.old_library_name = self.symbol.symbol_definition["configuration"]["library"]
            self.library_name = tk.StringVar()
            self.library_name.set(self.old_library_name)
            config_lib_label = ttk.Label      (configuration_frame, text="Verilog Library Name:", padding=5)
            config_lib_entry = ttk.Entry      (configuration_frame, width=23, textvariable=self.library_name)
            config_statement = ttk.Label      (configuration_frame, text="", padding=5)
            self.old_configuration = self.symbol.symbol_definition["configuration"]["config_statement"]
            self.config_var  = tk.StringVar() # Must be a attribute (self.), only then set() works.
            self.config_var.set(self.old_configuration)
            self.old_architecture = self.symbol.symbol_definition["architecture_name"] # Not used for verilog
            self.arch_var = tk.StringVar() # Not used for verilog.
            configuration_frame.columnconfigure(2, weight=1)
            config_lib_label.grid  (row=0, column=0, sticky=(tk.W, tk.E))
            config_lib_entry.grid  (row=0, column=1, sticky=(tk.W, tk.E, tk.S, tk.N))
            config_statement.grid  (row=0, column=2, sticky=(tk.W, tk.E))
        self.old_file_name              = self.symbol.symbol_definition["filename"]
        self.old_architecture_file_name = self.symbol.symbol_definition["architecture_filename"]
        if self.old_architecture_file_name!="":
            self.old_source_file_values = self.old_file_name + ", " + self.old_architecture_file_name
        else:
            self.old_source_file_values = self.old_file_name
        self.source_file_values = tk.StringVar()
        self.source_file_values.set(self.old_source_file_values)
        self.old_additional_files = self.symbol.symbol_definition["additional_files"] # List of file-names
        old_additional_files_string = ""
        for old_additional_file in self.old_additional_files:
            old_additional_files_string += old_additional_file + ', '
        if old_additional_files_string!="":
            old_additional_files_string = old_additional_files_string[:-2] # remove last ', '
        self.additional_source_files = tk.StringVar()
        self.additional_source_files.set(old_additional_files_string)
        source_file_label      = ttk.Label (source_frame, text="Source File-Names:", padding=5)
        source_file_entry      = ttk.Entry (source_frame, textvariable=self.source_file_values, width=80)
        source_file_button     = ttk.Button(source_frame, text="Add ...",  command=self.__set_path)
        source_path_label      = ttk.Label (source_frame, text="Additional Sources:", padding=5)
        source_additional_entry= ttk.Entry (source_frame, textvariable=self.additional_source_files, width=80)
        source_path_button     = ttk.Button(source_frame, text="Add ...",  command=self.__add_path)
        source_frame.rowconfigure   (1, weight=1)
        source_frame.columnconfigure(1, weight=1)
        source_file_label.grid      (row=0, column=0, sticky=(tk.W, tk.E))
        source_file_entry.grid      (row=0, column=1, sticky=(tk.W, tk.E, tk.S, tk.N))
        source_file_button.grid     (row=0, column=2, sticky=tk.W)
        source_path_label.grid      (row=1, column=0, sticky=(tk.W, tk.E, tk.S, tk.N))
        source_additional_entry.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.S, tk.N))
        source_path_button.grid     (row=1, column=2, sticky=(tk.W, tk.E, tk.S, tk.N))

        appearance_range_label = ttk.Label (appearance_frame, text="Port range visibility:", padding=5)
        self.old_port_range_visibility = self.symbol.symbol_definition["port_range_visibility"]
        self.appearance_var    = tk.StringVar()
        self.appearance_var.set(self.old_port_range_visibility)
        appearance_button1     = ttk.Radiobutton(appearance_frame, takefocus=False, variable=self.appearance_var, value="Show", padding=5, text="Show")
        appearance_button2     = ttk.Radiobutton(appearance_frame, takefocus=False, variable=self.appearance_var, value="Hide", padding=5, text="Hide")
        appearance_frame.columnconfigure(2, weight=1)
        appearance_range_label.grid (row=0, column=0, sticky=(tk.W, tk.E))
        appearance_button1.grid     (row=0, column=1, sticky=(tk.W, tk.E))
        appearance_button2.grid     (row=0, column=2, sticky=(tk.W, tk.E))

        button_save   = ttk.Button(button_frame, text="Store" , command=self.__save, padding=5)
        button_cancel = ttk.Button(button_frame, text="Cancel", command=self.__close_window, padding=5)
        button_free   = ttk.Label (button_frame, text="")
        button_frame.columnconfigure(2, weight=1)
        button_save.grid        (row=0, column=0, sticky=tk.W)
        button_cancel.grid      (row=0, column=1, sticky=tk.W)
        button_free.grid        (row=0, column=2, sticky=(tk.W, tk.E, tk.S, tk.N))

    def __set_path(self):
        path = askopenfilename()
        if path!="":
            old_entry = self.source_file_values.get()
            if old_entry=="":
                self.source_file_values.set(path)
            else:
                self.source_file_values.set(old_entry + ", " + path)

    def __add_path(self):
        path = askopenfilename()
        if path!="":
            old_entry = self.additional_source_files.get()
            if old_entry=="":
                self.additional_source_files.set(path)
            else:
                self.additional_source_files.set(old_entry + ', ' + path)

    def __save(self):
        new_configuration = self.config_var        .get()
        new_library_name  = self.library_name      .get()
        new_architecture  = self.arch_var          .get()
        new_file_names    = self.source_file_values.get()
        new_file_names_list = new_file_names.split(',')
        new_file_names_list = [entry.strip() for entry in new_file_names_list]
        new_file_name = new_file_names_list[0]
        if len(new_file_names_list)>1:
            new_architecture_file_name = new_file_names_list[1]
        else:
            new_architecture_file_name = ""
        instance_language = self.__get_language(new_file_name)
        if instance_language=="unknown":
            messagebox.showerror("Error in HDL-SCHEM-Editor", "The file " + new_file_name + " must be a VHDL-, Verilog-, Systemverilog-, HDL-SCHEM-Editor-, HDL-FSM-Editor- File")
            return
        new_additional_source_files_string = self.additional_source_files.get().strip()
        if new_additional_source_files_string=="":
            new_additional_source_file_list = []
        else:
            new_additional_source_file_list = new_additional_source_files_string.split(',')
            new_additional_source_file_list = [entry.strip() for entry in new_additional_source_file_list]
        new_port_range_visibility   = self.appearance_var.get()
        update_list = {}
        if new_library_name!=self.old_library_name:
            update_list["library"              ] = new_library_name
        if new_architecture!=self.old_architecture:
            update_list["architecture_name"    ] = new_architecture
        if new_configuration!=self.old_configuration:
            update_list["config_statement"     ] = new_configuration
        if new_file_name!=self.old_file_name:
            update_list["filename"             ] = new_file_name
        if new_architecture_file_name!=self.old_architecture_file_name:
            update_list["architecture_filename"] = new_architecture_file_name
        if new_additional_source_file_list!=self.old_additional_files:
            update_list["additional_files"] = new_additional_source_file_list
        if new_port_range_visibility!=self.old_port_range_visibility:
            update_list["port_range_visibility" ] = new_port_range_visibility
        self.symbol.update(update_list, store_in_design_and_stack=True)
        self.__close_window()

    def __get_language(self, filename):
        if   filename.endswith(".vhd"):
            return "VHDL"
        elif filename.endswith(".v"):
            return "Verilog"
        elif filename.endswith(".sv"):
            return "SystemVerilog"
        elif filename.endswith(".hse"):
            return "schematic"
        elif filename.endswith(".hfe"):
            return "fsm"
        else:
            return "unknown"

    def __close_window(self):
        self.property_window.destroy()
