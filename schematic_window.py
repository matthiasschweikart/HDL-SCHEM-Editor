""" This is the schematic entry window (Toplevel). """
import tkinter as tk
from   tkinter import messagebox

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

class SchematicWindow(tk.Toplevel):
    window_id              = 0
    number_of_open_windows = 0
    open_window_dict = {}
    def __init__(self, root, wire_class, signal_name_class, input_class, output_class, inout_class,
                 block_class, symbol_reading_class, symbol_insertion_class, symbol_instance_class,
                 hdl_generate_class, design_data_class, generate_frame_class,
                 visible=True):
        super().__init__()
        self.root = root
        if visible is False:
            self.withdraw()
        self.protocol("WM_DELETE_WINDOW", self.close_this_window)
        self.closing_in_process = False
        self.__draw_window(wire_class, signal_name_class, input_class, output_class, inout_class, block_class, symbol_reading_class,
                           symbol_insertion_class, symbol_instance_class, generate_frame_class, hdl_generate_class, design_data_class)
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

    def __check_for_window_resize(self, event):
        if event.widget==self and (event.width!=self.window_width or event.height!=self.window_height):
            self.window_width  = event.width
            self.window_height = event.height
            self.update_idletasks()
            self.notebook_top.diagram_tab.adjust_scroll_region_at_zoom(1.0)
            self.notebook_top.diagram_tab.grid_drawer.draw_grid()

    def __draw_window(self, wire_class, signal_name_class, input_class, output_class, inout_class, block_class, symbol_reading_class,
                      symbol_insertion_class, symbol_instance_class, generate_frame_class, hdl_generate_class, design_data_class):
        self.columnconfigure(0, weight=1) # The window has only 1 column.
        row_for_menubar      = 0
        row_for_notebook     = 1
        row_for_quick_access = 2
        self.rowconfigure(row_for_menubar , weight=0)
        self.rowconfigure(row_for_notebook, weight=1)
        self.design              = design_data_selector.DesignDataSelector (self.root, window=self)
        self.notebook_top        = notebook_top.NotebookTop(self.root, schematic_window=self, design=self.design, column=0, row=row_for_notebook,
                                                            wire_class=wire_class, signal_name_class=signal_name_class, input_class=input_class,
                                                            output_class=output_class, inout_class=inout_class,
                                                            block_class=block_class, symbol_reading_class=symbol_reading_class,
                                                            symbol_insertion_class=symbol_insertion_class,
                                                            symbol_instance_class=symbol_instance_class,
                                                            generate_frame_class=generate_frame_class)
        self.menu_bar            = menu_bar.MenuBar        (schematic_window=self, design=self.design, root=self.root, column=0, row=row_for_menubar,
                                                            window_class=SchematicWindow,
                                                            wire_class=wire_class, signal_name_class=signal_name_class, input_class=input_class,
                                                            output_class=output_class, inout_class=inout_class, block_class=block_class, symbol_reading_class=symbol_reading_class,
                                                            hdl_tab=self.notebook_top.hdl_tab, log_tab=self.notebook_top.log_tab,
                                                            symbol_insertion_class=symbol_insertion_class, symbol_instance_class=symbol_instance_class,
                                                            hdl_generate_class=hdl_generate_class, design_data_class=design_data_class,
                                                            generate_frame_class=generate_frame_class)
        self.quick_access_object = quick_access.QuickAccess(schematic_window=self, column=0, row=row_for_quick_access)

    def open_this_window(self):
        if self.state()=="withdrawn": # This window is only open for the creation of the link-dictionary.
            self.__add_quick_access_button_for_this_module_to_all_open_modules(self.design.get_path_name(), self.design.get_module_name())
            self.deiconify()
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
            self.root.quit()

    def close_all_windows(self):
        local_copy_of_open_window_dict = dict(SchematicWindow.open_window_dict)
        for window in local_copy_of_open_window_dict:
            if window.state()!="withdrawn":
                window.close_this_window()

    def __abort_closing(self):
        if self.title().endswith("*"):
            path_name = self.design.get_path_name()
            if self.closing_in_process:
                return True # Prevent from opening a next messagebox.
            self.closing_in_process = True
            discard = messagebox.askokcancel("HDL-Schem-Editor:", "There are unsaved changes in " + path_name + ", do you want to discard them?", default="cancel")
            self.closing_in_process = False
            if discard is False:
                return True
        return False

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
                            visible=False)
        file_read.FileRead(sub_window, filename, architecture_name, fill_link_dictionary=False)
        return sub_window

    @classmethod
    def open_clipboard_window(cls, root):
        sub_window = SchematicWindow(root, wire_insertion.Wire, signal_name.SignalName,
                            interface_input.Input, interface_output.Output, interface_inout.Inout,
                            block_insertion.Block,
                            symbol_reading.SymbolReading, symbol_insertion.SymbolInsertion, symbol_instance.Symbol, hdl_generate.GenerateHDL,
                            design_data.DesignData, generate_frame.GenerateFrame,
                            visible=False)
        return sub_window
