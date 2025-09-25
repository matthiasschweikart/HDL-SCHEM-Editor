""" This is the schematic entry window (Toplevel). """
import tkinter as tk
from   tkinter import ttk
from   tkinter import messagebox
import os
from   os.path import exists
import json
import sys
from pathlib import Path

import menu_bar
import notebook_top

import wire_insertion
import signal_name
import interface_input
import interface_output
import interface_inout
import block_insertion
import symbol_reading
import symbol_insertion
import symbol_instance
import hdl_generate
import design_data
import design_data_selector
import generate_frame
import file_read
import notebook_diagram_tab
import quick_access
import hierarchy_tree

class SchematicWindow(tk.Toplevel):
    window_id              = 0
    number_of_open_windows = 0
    open_window_dict = {}
    def __init__(self, root, wire_class, signal_name_class, input_class, output_class, inout_class,
                 block_class, symbol_reading_class, symbol_insertion_class, symbol_instance_class,
                 hdl_generate_class, design_data_class, generate_frame_class,
                 visible, working_directory):
        super().__init__()
        self.root = root
        self.geometry("1400x800")
        if not visible:
            self.withdraw()
        self.protocol("WM_DELETE_WINDOW", self.close_this_window)
        self.closing_in_process = False

        # # Set the application icon
        # try:
        #     icon_path = self.__get_resource_path("hse_icon.ico")
        #     if icon_path.exists():
        #         self.iconbitmap(icon_path)
        #     else:
        #         print(f"Warning: Icon file not found at {icon_path}")
        # except Exception as e:
        #     print(f"Warning: Could not set application icon: {e}")

        self.__build_window(wire_class, signal_name_class, input_class, output_class, inout_class, block_class, symbol_reading_class,
                           symbol_insertion_class, symbol_instance_class, generate_frame_class, hdl_generate_class, design_data_class, working_directory)
        unnamed_name = "unnamed" + str(self.window_id + 1)
        self.design.set_path_name(unnamed_name)
        self.bind("<FocusIn>"  , lambda event: self.menu_bar.create_binding_for_menu_accelerators())
        self.update_idletasks() # was introduced, because sometimes it seemed like the virtual event FocusIn did not reach the correct window.
        self.event_generate("<FocusIn>", when="now")
        self.__add_quick_access_button_for_each_already_open_module_to_this_window()
        SchematicWindow.number_of_open_windows += 1
        SchematicWindow.window_id              += 1
        SchematicWindow.open_window_dict[self] = unnamed_name # when a file is read or written, then the value is replaced by the file name
        if visible:
            self.__add_quick_access_button_for_this_module_to_all_open_modules(unnamed_name, unnamed_name)
        self.__store_module_name_in_design_data(unnamed_name)
        self.window_width  = 0
        self.window_height = 0
        self.bind("<Configure>", self.__check_for_window_resize)

    def __get_resource_path(self, resource_name: str) -> Path:
        """Get the path to a resource file, handling both development and PyInstaller environments."""
        base_path = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).parent.parent
        return base_path / "rsc" / resource_name

    def __check_for_window_resize(self, event):
        if event.widget==self and (event.width!=self.window_width or event.height!=self.window_height):
            self.window_width  = event.width
            self.window_height = event.height
            self.update_idletasks()
            self.notebook_top.diagram_tab.adjust_scroll_region_at_zoom(1.0)
            self.notebook_top.diagram_tab.grid_drawer.draw_grid()

    def __build_window(self, wire_class, signal_name_class, input_class, output_class, inout_class, block_class, symbol_reading_class,
                       symbol_insertion_class, symbol_instance_class, generate_frame_class, hdl_generate_class, design_data_class, working_directory):
        self.columnconfigure(0, weight=1) # The window has only 1 column.
        row_for_menubar      = 0
        row_for_notebook     = 1
        row_for_quick_access = 2
        self.rowconfigure(row_for_menubar , weight=0)
        self.rowconfigure(row_for_notebook, weight=1)
        last_line_frame = ttk.Frame(self, relief=tk.RAISED, borderwidth=4)
        last_line_frame.grid(row=row_for_quick_access, column=0, sticky=(tk.W, tk.S, tk.E, tk.N))
        last_line_frame.columnconfigure(0, weight=1)
        last_line_frame.columnconfigure(1, weight=0)
        self.design              = design_data_selector.DesignDataSelector (self.root, window=self)
        self.hierarchytree       = hierarchy_tree.HierarchyTree(self.root, schematic_window=self, frame=last_line_frame, column=1, row=0)
        self.notebook_top        = notebook_top.NotebookTop(self.root, schematic_window=self, design=self.design, column=0, row=row_for_notebook,
                                                            wire_class=wire_class, signal_name_class=signal_name_class, input_class=input_class,
                                                            output_class=output_class, inout_class=inout_class,
                                                            block_class=block_class, symbol_reading_class=symbol_reading_class,
                                                            symbol_insertion_class=symbol_insertion_class,
                                                            symbol_instance_class=symbol_instance_class,
                                                            generate_frame_class=generate_frame_class, working_directory=working_directory)
        self.menu_bar            = menu_bar.MenuBar        (schematic_window=self, design=self.design, root=self.root, column=0, row=row_for_menubar,
                                                            window_class=SchematicWindow,
                                                            wire_class=wire_class, signal_name_class=signal_name_class, input_class=input_class,
                                                            output_class=output_class, inout_class=inout_class, block_class=block_class, symbol_reading_class=symbol_reading_class,
                                                            hdl_tab=self.notebook_top.hdl_tab, log_tab=self.notebook_top.log_tab,
                                                            symbol_insertion_class=symbol_insertion_class, symbol_instance_class=symbol_instance_class,
                                                            hdl_generate_class=hdl_generate_class, design_data_class=design_data_class,
                                                            generate_frame_class=generate_frame_class, working_directory=working_directory)
        self.quick_access_object = quick_access.QuickAccess(schematic_window=self, frame=last_line_frame, column=0, row=0)

    def open_this_window(self):
        if self.state()=="withdrawn": # This window is only open for the creation of the link-dictionary.
            self.__add_quick_access_button_for_this_module_to_all_open_modules(self.design.get_path_name(), self.design.get_module_name())
        self.deiconify() # needed for "withdrawn" windows and windows which the user iconified
        self.after_idle(self.lift_window) # Sometimes using the link from log-tab to schematic showed full-view instead of a small area, this here might help.

    def lift_window(self):
        self.lift()
        self.attributes("-topmost", True)
        self.after(2000, self.attributes,"-topmost", False )

    def __add_quick_access_button_for_each_already_open_module_to_this_window(self):
        for open_window in SchematicWindow.open_window_dict:
            if (open_window!=notebook_diagram_tab.NotebookDiagramTab.clipboard_window and
                open_window.state()!="withdrawn"):
                self.quick_access_object.add_quick_access_button(open_window, open_window.design.get_path_name(),
                                                                     open_window.design.get_module_name())

    def __add_quick_access_button_for_this_module_to_all_open_modules(self, path_name, module_name):
        for open_window in SchematicWindow.open_window_dict:
            open_window.quick_access_object.add_quick_access_button(self, path_name, module_name)
            if open_window==self:
                self.quick_access_object.quick_access_buttons_dict[path_name].config(style="Quick_Access.TButton")

    def __store_module_name_in_design_data(self, unnamed_name):
        # As now all buttons exist, the module_name can be set.
        self.notebook_top.control_tab.module_name.set(unnamed_name) # Changes the name in design_data by a "trace", but adds '*' to window_title.
        self.design.update_window_title(written=True)               # removes '*' from window_title

    def close_this_window(self):
        if self.__abort_closing():
            return
        self.withdraw()
        self.quick_access_object.remove_quick_access_button(self.design.get_path_name())
        if self.__get_number_of_withdrawn_windows()==SchematicWindow.number_of_open_windows:
            self.__write_rc_file()
            self.root.quit()

    def __write_rc_file(self):
        config_dictionary = {}
        config_dictionary["schematic_background"] = self.notebook_top.diagram_tab.canvas.cget("bg")
        config_dictionary["working_directory"   ] = self.design.get_working_directory()
        try:
            with open(Path.home()/".hdl-schem-editor.rc", 'w', encoding="utf-8") as fileobject:
                fileobject.write(json.dumps(config_dictionary, indent=4, default=str))
                print("Created configuration file " + str(Path.home()) + "/.hdl-schem-editor.rc")
        except Exception as e:
            print("HDL-SCHEM-Editor-Warning: Could not write to file " + str(Path.home()) + '/.hdl-schem-editor.rc.', e)

    def close_all_windows(self):
        local_copy_of_open_window_dict = dict(SchematicWindow.open_window_dict)
        for window in local_copy_of_open_window_dict:
            if window.state()!="withdrawn":
                window.close_this_window()

    def iconify_all_windows(self):
        for window in SchematicWindow.open_window_dict:
            if window.state()!="withdrawn": # The unvisible windows shall not be iconified, because they will get visible as icon then.
                window.iconify()

    def __abort_closing(self):
        if self.title().endswith("*"):
            path_name = self.design.get_path_name()
            self.closing_in_process = True
            discard = messagebox.askokcancel("HDL-Schem-Editor:", "There are unsaved changes in " + path_name + ", do you want to discard them?", default="cancel")
            self.closing_in_process = False
            if not discard:
                return True
            # The window will only be withdrawn, the changes must be removed for the case when HDL-SCHEM-Editor keeps running.
            self.__remove_back_up_file(path_name) # must be removed before the file is read, otherwise there would pop up a window asking to read the tmp-file.
            self.__restore_to_version_before_changes(path_name)
        return False

    def __restore_to_version_before_changes(self, path_name):
        self.title("") # Remove the '*' so that file read ignores the changes.
        if exists(path_name): # Needed, because the changed file may never have been saved.
            file_read.FileRead(self, path_name, self.design.get_architecture_name(), fill_link_dictionary=True)

    def __remove_back_up_file(self, path_name):
        if os.path.isfile(path_name + ".tmp"):
            os.remove(path_name + ".tmp")

    def __get_number_of_withdrawn_windows(self):
        number_of_withdrawn_windows = 0
        for open_window in SchematicWindow.open_window_dict:
            if open_window.state()=="withdrawn":
                number_of_withdrawn_windows += 1
        return number_of_withdrawn_windows

    def update_schematic_window_from(self, new_dict, fill_link_dictionary):
        self.notebook_top.update_notebook_top_from(new_dict, fill_link_dictionary)

    @classmethod
    def open_subwindow(cls, root, filename, architecture_name):
        sub_window = SchematicWindow(root, wire_insertion.Wire, signal_name.SignalName,
                            interface_input.Input, interface_output.Output, interface_inout.Inout,
                            block_insertion.Block,
                            symbol_reading.SymbolReading, symbol_insertion.SymbolInsertion, symbol_instance.Symbol, hdl_generate.GenerateHDL,
                            design_data.DesignData, generate_frame.GenerateFrame,
                            visible=False, working_directory="")
        file_read.FileRead(sub_window, filename, architecture_name, fill_link_dictionary=False)
        return sub_window

    @classmethod
    def open_clipboard_window(cls, root):
        sub_window = SchematicWindow(root, wire_insertion.Wire, signal_name.SignalName,
                            interface_input.Input, interface_output.Output, interface_inout.Inout,
                            block_insertion.Block,
                            symbol_reading.SymbolReading, symbol_insertion.SymbolInsertion, symbol_instance.Symbol, hdl_generate.GenerateHDL,
                            design_data.DesignData, generate_frame.GenerateFrame,
                            visible=False, working_directory="")
        return sub_window
