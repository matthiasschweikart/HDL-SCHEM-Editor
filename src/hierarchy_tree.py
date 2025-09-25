"""
Class for hiding, showing and filling the treeview widget of the diagram_tab
When a SchematicWindow object is created, also a HierarchyTree object is created.

When a file is read in by the user at last the "generated HDL" tab is updated by update_hdl_tab_from.
This method also calls HdlGenerateHierarchy in order to fill the link-dictionary.
During HDL generation all sub-modules are also read from file, if they are not already opened.
Each file, which is read, calls its refresh-treeviews() method and so its sub-modules are stored in the treeview of the toplevel module.
At each time a sub-module removes an instance or adds an instance the object in the the toplevel module is updated.

When a change to the stack in design_data is done, then in design_data the "sorted_list_of_instance_dictionaries" is updated.
After this update, design_data calls refresh-treeviews() from here.
From there the method refresh_treeview_in_all_windows_by_top_module_window() is called.
Only the toplevel gets active and creates a new hierarchy dictionary.
When the dictionary is ready, then in all open windows insert_dict_into_treeview(top_dict) is called and
all tree views are updated.

See an example of the hierarchy tree at the end of this file.

"""
import tkinter as tk
from tkinter import ttk
import re
import symbol_instance
import extract_hierarchy

class HierarchyTree():
    def __init__(self, root, schematic_window, frame, column, row):
        self.root                      = root
        self.schematic_window          = schematic_window
        self.hierarchy_button_column   = column
        self.hierarchy_button_row      = row
        self.this_module_is_top_module = False
        self.column_name_of_column0    = "Instance Name"
        self.column_names              = ("#0", "Module-Name", "Library", "File-Name", "Architecture-Name")
        self.columns_properties        = []
        self.hierarchy_button          = ttk.Button(frame, text="Show hierarchy", command=self.__hide_show_button_was_pressed)
        self.compile_order_list        = {}

    def open_design_in_new_window(self, event, treeview_ref): # This method is bound to a doubleclick at each treeview item in notebook_diagram_tab.
        item_identifier = treeview_ref.identify_row(event.y)
        if item_identifier!="":
            item_dict = treeview_ref.item(item_identifier)
            filename_entry              = item_dict["values"][2]
            architecture_filename_entry = item_dict["values"][3]
            architecture_name           = item_dict["values"][4]
            if filename_entry.endswith(".hfe") or filename_entry.endswith(".hse"):
                filename = filename_entry
            else:
                filename = architecture_filename_entry
            symbol_instance.Symbol.open_source_code(self.root, self.schematic_window, filename, architecture_name)
        return "break" # prevents closing/opening the tree because of double-click

    def show_hierarchy_button(self):
        self.hierarchy_button.grid(row=self.hierarchy_button_row, column=self.hierarchy_button_column, sticky=tk.E)
    def hide_hierarchy_button(self):
        self.hierarchy_button.grid_forget()

    def __hide_show_button_was_pressed(self):
        if self.hierarchy_button.cget("text")=="Hide hierarchy":
            self.schematic_window.notebook_top.diagram_tab.hide_hierarchy_window()
            self.hierarchy_button.configure(text="Show hierarchy")
            self.columns_properties = []
            for col in self.column_names:
                self.columns_properties.append(self.schematic_window.notebook_top.diagram_tab.treeview.column(col))
        else:
            self.schematic_window.notebook_top.diagram_tab.show_hierarchy_window()
            for column_property in self.columns_properties:
                if column_property["id"]=='':
                    column_property["id"] = "#0"
                self.schematic_window.notebook_top.diagram_tab.treeview.column(column_property["id"], width=column_property["width"])
            self.hierarchy_button.configure(text="Hide hierarchy")

    # When design_data detects changes in the database or diagram_tab detects "Undo/Redo" in the schematic, then this method is called:
    def refresh_treeviews(self):
        self.this_module_is_top_module = self.__check_for_top_module()
        for open_window, _ in self.schematic_window.__class__.open_window_dict.items():
            open_window.hierarchytree.refresh_treeview_in_all_windows_by_top_module_window()

    def __check_for_top_module(self):
        for open_window, _ in self.schematic_window.__class__.open_window_dict.items():
            for instance_dict in open_window.design.get_sorted_list_of_instance_dictionaries():
                if instance_dict["module_name"]==self.schematic_window.design.get_module_name():
                    # This module is also found as an instance in a database, so it can't be the toplevel.
                    return False
        return True

    def refresh_treeview_in_all_windows_by_top_module_window(self):
        if self.this_module_is_top_module:
            library = self.schematic_window.design.get_module_library()
            if library=="":
                library = "work"
            entity_filename_for_generation, architecture_filename_for_generation = self.schematic_window.design.get_file_names()
            top_dict = {
                "configuration_library" : library, # This is the toplevel, so no configuration from a symbol is available
                "instance_name"         : " ",     # This is the toplevel, so no instance name is available.
                "module_name"           : self.schematic_window.design.get_module_name(),
                "language"              : self.schematic_window.design.get_language(), 
                "env_language"          : self.schematic_window.notebook_top.control_tab.language.get(),
                "filename"              : self.schematic_window.design.get_path_name(),
                "entity_filename"       : entity_filename_for_generation,
                "architecture_filename" : architecture_filename_for_generation,
                "additional_files"      : [],
                "architecture_name"     : self.schematic_window.design.get_architecture_name(),
                "sub_modules"           : []
            }
            self.__fill_sub_modules_into(top_dict)
            for open_window, _ in self.schematic_window.__class__.open_window_dict.items():
                open_window.hierarchytree.insert_dict_into_treeview(top_dict)
            #self.create_hdl_file_list()

    def __fill_sub_modules_into(self, top_dict):
        #print("sorted_list_of_instance_dictionaries =", self.schematic_window.design.get_sorted_list_of_instance_dictionaries())
        for instance_dict in self.schematic_window.design.get_sorted_list_of_instance_dictionaries():
            if instance_dict["module_name"]!=top_dict["module_name"]:
                sub_module_dict = self.get_sub_module_dict(instance_dict)
                if sub_module_dict is not None:
                    top_dict["sub_modules"].append(sub_module_dict)

    def get_sub_module_dict(self, instance_dict):
        if instance_dict["filename"].endswith(".hse") or instance_dict["filename"].endswith(".hfe"):
            entity_filename_for_generation, architecture_filename_for_generation = self.schematic_window.design.get_file_names_by_parameters(instance_dict["number_of_files"],
                                                                                                               instance_dict["language"],
                                                                                                               instance_dict["generate_path_value"],
                                                                                                               instance_dict["module_name"],
                                                                                                               instance_dict["architecture_name"])
        else: # VHDL, Verilog, SystemVerilog
            entity_filename_for_generation       = instance_dict["filename"]
            architecture_filename_for_generation = instance_dict["architecture_filename"]
        sub_module_dict = {}
        sub_module_dict["configuration_library"] = instance_dict["configuration_library"]
        sub_module_dict["instance_name"]         = instance_dict["instance_name"]
        sub_module_dict["module_name"]           = instance_dict["module_name"]
        sub_module_dict["language"]              = instance_dict["language"]
        sub_module_dict["env_language"]          = instance_dict["env_language"]
        sub_module_dict["filename"]              = instance_dict["filename"]
        sub_module_dict["entity_filename"]       = entity_filename_for_generation
        sub_module_dict["architecture_filename"] = architecture_filename_for_generation
        sub_module_dict["architecture_name"]     = instance_dict["architecture_name"]
        sub_module_dict["sub_modules"]           = []
        if instance_dict["filename"].endswith(".vhd") or instance_dict["filename"].endswith(".v") or instance_dict["filename"].endswith(".sv"):
            sub_module_dict["sub_modules"] = extract_hierarchy.ExtractHierarchy(instance_dict).get_list_of_sub_modules_dicts()
        else:
            for open_window, _ in self.schematic_window.__class__.open_window_dict.items():
                if open_window.design.get_module_name()==instance_dict["module_name"]:
                    for sub_instance_dict in open_window.design.get_sorted_list_of_instance_dictionaries():
                        if sub_instance_dict["module_name"]!=sub_module_dict["module_name"]:
                            sub_module_dict["sub_modules"].append(open_window.hierarchytree.get_sub_module_dict(sub_instance_dict))
        return sub_module_dict

    def insert_dict_into_treeview(self, topdict):
        self.compile_order_list = {}
        self.schematic_window.notebook_top.diagram_tab.treeview.delete(*self.schematic_window.notebook_top.diagram_tab.treeview.get_children())
        top = self.schematic_window.notebook_top.diagram_tab.treeview.insert("", 0, text="top-level", tags="tree_view_entry",
                                                                                    values=[topdict["module_name"],
                                                                                            topdict["configuration_library"],
                                                                                            topdict["filename"],
                                                                                            topdict["architecture_filename"],
                                                                                            topdict["architecture_name"]
                                                                                           ],
                                                                                    open=True)
        for mod_dict in topdict["sub_modules"]:
            self.fill_tree(top, mod_dict)
        self.compile_order_list[topdict["configuration_library"] + ':' + topdict["module_name"]] = {"library"               : topdict["configuration_library"],
                                                                                                    "entity_filename"       : topdict["entity_filename"],
                                                                                                    "architecture_filename" : topdict["architecture_filename"]}

    def fill_tree(self, parent_iid, mod_dict):
        if mod_dict["env_language"]=="VHDL":
            instance_name = re.sub(r"--.*", "", mod_dict["instance_name"])
        else:
            instance_name = re.sub(r"//.*", "", mod_dict["instance_name"])
        iid = self.schematic_window.notebook_top.diagram_tab.treeview.insert(parent_iid, "end", text=instance_name, tags="tree_view_entry",
                                                                                                values=[mod_dict["module_name"],
                                                                                                        mod_dict["configuration_library"],
                                                                                                        mod_dict["filename"],
                                                                                                        mod_dict["architecture_filename"],
                                                                                                        mod_dict["architecture_name"]
                                                                                                        ],
                                                                                                open=True)
        for sub_dict in mod_dict["sub_modules"]:
            self.fill_tree(iid, sub_dict)
        identifier = mod_dict["configuration_library"] + ':' + mod_dict["module_name"]
        if identifier not in self.compile_order_list:
            self.compile_order_list[identifier] = {"library"               : mod_dict["configuration_library"],
                                                   "entity_filename"       : mod_dict["entity_filename"],
                                                   "architecture_filename" : mod_dict["architecture_filename"]}

    # Not used:
    # def create_hdl_file_list(self):
    #     hdl_file_list = ""
    #     library = "work"
    #     for _, entry_dict in self.compile_order_list.items():
    #         if entry_dict["library"]!=library:
    #             library = entry_dict["library"]
    #             hdl_file_list += "lib: " + library + "\n"
    #         hdl_file_list += entry_dict["entity_filename"] + "\n"
    #         if entry_dict["architecture_filename"]!=entry_dict["entity_filename"]:
    #             hdl_file_list += entry_dict["architecture_filename"] + "\n"
    #     print("hdl_file_list =\n" + hdl_file_list)


# This is an example of a hierarchy dictionary created here:
# hierarchy-dict = {
# 'configuration_library': '',
# 'instance_name'        : ' ',
# 'module_name'          : 'testbench_division_srt_radix2',
# 'language'             : 'VHDL',
# 'env_language'         : 'VHDL',
# 'filename'             : 'testbench_division_srt_radix2_e.vhd',
# 'architecture_name'    : 'struct',
# 'sub_modules'          : [{'configuration_library': 'work',
#                            'instance_name'        : 'division_srt_radix2_inst',
#                            'module_name'          : 'division_srt_radix2',
#                            'language'             : 'VHDL',
#                            'env_language'         : 'VHDL',
#                            'filename'             : 'division_srt_radix2.hse',
#                            'architecture_name': 'struct',
#                            'sub_modules': [{'configuration_library': 'work',
#                                             'instance_name'        : 'division_srt_radix2_calc_shifts_inst -- 4',
#                                             'module_name'          : 'division_srt_radix2_calc_shifts',
#                                             'language'             : 'VHDL',
#                                             'env_language'         : 'VHDL',
#                                             'filename'             : 'division_srt_radix2_calc_shifts.hse',
#                                             'architecture_name'    : 'struct',
#                                             'sub_modules'          : []
#                                            },
#                                            {'configuration_library': 'work',
#                                             'instance_name'        : 'division_srt_radix2_core_inst -- 5',
#                                             'module_name'          : 'division_srt_radix2_core',
#                                             'language'             : 'VHDL',
#                                             'env_language'         : 'VHDL',
#                                             'filename'             : 'division_srt_radix2_core.hse',
#                                             'architecture_name'    : 'struct',
#                                             'sub_modules'          : [{'configuration_library' : 'work',
#                                                                        'instance_name'         : 'division_srt_radix2_control_inst -- 1',
#                                                                        'module_name'           : 'division_srt_radix2_control',
#                                                                        'language'              : 'VHDL',
#                                                                        'env_language'          : 'VHDL',
#                                                                        'filename'              : 'division_srt_radix2_control.hfe',
#                                                                        'architecture_name'     : 'fsm',
#                                                                        'sub_modules'           : []
#                                                                       },
#                                                                       {'configuration_library' : 'work',
#                                                                        'instance_name'         : 'division_srt_radix2_step_inst',
#                                                                        'module_name'           : 'division_srt_radix2_step',
#                                                                        'language'              : 'VHDL',
#                                                                        'env_language'          : 'VHDL',
#                                                                        'filename'              : 'division_srt_radix2_step.hse',
#                                                                        'architecture_name'     : 'struct',
#                                                                        'sub_modules'           : []
#                                                                       }
#                                                                      ]
#                                            },
#                                            {'configuration_library': 'work',
#                                             'instance_name'        : 'division_srt_radix2_norm_dvr_inst -- 2',
#                                             'module_name'          : 'division_srt_radix2_norm',
#                                             'language'             : 'VHDL',
#                                             'env_language'         : 'VHDL',
#                                             'filename'             : 'division_srt_radix2_norm.hse',
#                                             'architecture_name'    : 'struct',
#                                             'sub_modules'          : []
#                                            }
#                                           ]
#                           }
#                          ]
#                  }
#
