"""
Class for hiding, showing and filling the treeview widget of the diagram_tab

When a file is read in by the user at last the "generated HDL" tab is updated by update_hdl_tab_from.
This method also generates HDL through the hierarchy in order to fill the link-dictionary.
During HDL generation all sub-modules are also read from file, if they are not already opened.
Each file, which is read, stores its sub-modules in this object here.
At each time a sub-module removes an instance or adds an instance the object here is updated.


"""
import tkinter as tk
from tkinter import ttk
import re
import symbol_instance

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
        self.hierarchy_button          = ttk.Button(frame, text="Hide hierarchy", command=self.__hide_show_button_was_pressed)

    def open_source(self, event):
        item_dict = self.schematic_window.notebook_top.diagram_tab.treeview.item(self.schematic_window.notebook_top.diagram_tab.treeview.identify_row(event.y))
        filename          = item_dict["values"][2]
        architecture_name = item_dict["values"][3]
        symbol_instance.Symbol.open_source_code(self.root, self.schematic_window, filename, architecture_name)

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

    # When design_data detects changes in the database or diagram_tab detects "Undo/Redo" in the schematic,
    # and there are added or removed instances, then this method is called:
    def check_new_instance_list(self):
        self.this_module_is_top_module = self.__check_for_top_module()
        if not self.this_module_is_top_module:
            for open_window, _ in self.schematic_window.__class__.open_window_dict.items():
                open_window.hierarchytree.refresh_treeview_in_all_windows_by_top_module_window()
        else:
            self.__refresh_treeview_in_all_windows_by_this_window()

    def __check_for_top_module(self):
        for open_window, _ in self.schematic_window.__class__.open_window_dict.items():
            for instance_dict in open_window.design.get_sorted_list_of_instance_dictionaries():
                if instance_dict["module_name"]==self.schematic_window.design.get_module_name():
                    return False
        return True

    def refresh_treeview_in_all_windows_by_top_module_window(self):
        if self.this_module_is_top_module:
            self.__refresh_treeview_in_all_windows_by_this_window()

    def __refresh_treeview_in_all_windows_by_this_window(self):
        hierarchy_dict = {
            "configuration_library" : self.schematic_window.design.get_module_library(), # This is the toplevel, no configuration is available
            "instance_name"         : " ",                                               # This is the toplevel, so no instance name is available.
            "module_name"           : self.schematic_window.design.get_module_name(),
            "language"              : self.schematic_window.design.get_language(), 
            "env_language"          : self.schematic_window.notebook_top.control_tab.language.get(),
            "filename"              : self.schematic_window.design.get_file_names()[0],
            "architecture_name"     : self.schematic_window.design.get_architecture_name(),
            "sub_modules"           : []
        }
        self.__fill_sub_modules_into(hierarchy_dict)
        for open_window, _ in self.schematic_window.__class__.open_window_dict.items():
            open_window.hierarchytree.insert_dict_into_treeview(hierarchy_dict)

    def __fill_sub_modules_into(self, hierarchy_dict):
        for instance_dict in self.schematic_window.design.get_sorted_list_of_instance_dictionaries():
            sub_module_dict = self.get_sub_module_dict(instance_dict)
            if sub_module_dict is not None:
                hierarchy_dict["sub_modules"].append(sub_module_dict)

    def get_sub_module_dict(self, instance_dict):
        sub_module_dict = {}
        sub_module_dict["configuration_library"] = instance_dict["configuration_library"]
        sub_module_dict["instance_name"]         = instance_dict["instance_name"]
        sub_module_dict["module_name"]           = instance_dict["module_name"]
        sub_module_dict["language"]              = instance_dict["language"]
        sub_module_dict["env_language"]          = instance_dict["env_language"]
        sub_module_dict["filename"]              = instance_dict["filename"]
        sub_module_dict["architecture_name"]     = instance_dict["architecture_name"]
        sub_module_dict["sub_modules"]           = []
        for open_window, _ in self.schematic_window.__class__.open_window_dict.items():
            if open_window.design.get_module_name()==instance_dict["module_name"]:
                for sub_instance_dict in open_window.design.get_sorted_list_of_instance_dictionaries():
                    sub_module_dict["sub_modules"].append(open_window.hierarchytree.get_sub_module_dict(sub_instance_dict))
        return sub_module_dict

    def insert_dict_into_treeview(self, topdict):
        self.schematic_window.notebook_top.diagram_tab.treeview.delete(*self.schematic_window.notebook_top.diagram_tab.treeview.get_children())
        top = self.schematic_window.notebook_top.diagram_tab.treeview.insert("", 0, text="top-level", tags="open_source",
                                                                                    values=[topdict["module_name"],
                                                                                            topdict["configuration_library"],
                                                                                            topdict["filename"],
                                                                                            topdict["architecture_name"]
                                                                                           ],
                                                                                    open=True)
        for mod_dict in topdict["sub_modules"]:
            self.fill_tree(top, mod_dict)

    def fill_tree(self, parent_iid, mod_dict):
        if mod_dict["env_language"]=="VHDL":
            instance_name = re.sub(r"--.*", "", mod_dict["instance_name"])
        else:
            instance_name = re.sub(r"//.*", "", mod_dict["instance_name"])
        iid = self.schematic_window.notebook_top.diagram_tab.treeview.insert(parent_iid, "end", text=instance_name, tags="open_source",
                                                                                                values=[mod_dict["module_name"],
                                                                                                        mod_dict["configuration_library"],
                                                                                                        mod_dict["filename"],
                                                                                                        mod_dict["architecture_name"]
                                                                                                        ],
                                                                                                open=True)
        for sub_dict in mod_dict["sub_modules"]:
            self.fill_tree(iid, sub_dict)
