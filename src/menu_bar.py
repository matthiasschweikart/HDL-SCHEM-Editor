""" Create the menu bar of the schematic editor window """
import tkinter as tk
from   tkinter import ttk
from   tkinter import messagebox

import constants
import file_write
import file_read
import find_replace
import hdl_compile
import hdl_generate
import hdl_generate_through_hierarchy
import convert_hdl

class MenuBar():
    def __init__(self, schematic_window, design, root, column, row,
                 window_class, wire_class, signal_name_class, input_class, output_class, inout_class, block_class,
                 symbol_reading_class, hdl_tab, log_tab, symbol_insertion_class, symbol_instance_class, hdl_generate_class,
                 design_data_class, generate_frame_class, working_directory):
        self.window                   = schematic_window
        self.design                   = design
        self.root                     = root
        self.window_class             = window_class
        self.wire_class               = wire_class
        self.signal_name_class        = signal_name_class
        self.input_class              = input_class
        self.output_class             = output_class
        self.inout_class              = inout_class
        self.block_class              = block_class
        self.hdl_generate_class       = hdl_generate_class
        self.design_data_class        = design_data_class
        self.generate_frame_class     = generate_frame_class
        self.symbol_insertion_class   = symbol_insertion_class
        self.symbol_instance_class    = symbol_instance_class
        self.symbol_reading_class     = symbol_reading_class
        self.working_directory        = working_directory
        self.hdl_tab                  = hdl_tab
        self.log_tab                  = log_tab
        self.generation_failed        = False # This attribute is set by the hdl_generate_class, but not used by class MenuBar.
        self.menue_frame = ttk.Frame(self.window, borderwidth=2, relief=tk.RAISED)
        self.menue_frame.grid(row=row, column=column, sticky=(tk.N,tk.W,tk.E,tk.S))

        self.file_menu_button = ttk.Menubutton(self.menue_frame, text="File", style="TMenubutton")
        self.file_menu = tk.Menu(self.file_menu_button)
        self.file_menu_button.configure(menu=self.file_menu)
        self.file_menu.add_command(label="New",      accelerator="Ctrl+n"    , command=lambda : window_class(root, wire_class, signal_name_class,
                                                                                                          input_class, output_class, inout_class,
                                                                                                          block_class, symbol_reading_class, symbol_insertion_class,
                                                                                                          symbol_instance_class, hdl_generate_class,
                                                                                                          design_data_class, generate_frame_class,
                                                                                                          visible=True, working_directory=self.working_directory))
        self.file_menu.add_command(label="Open ...", accelerator="Ctrl+o"    , command=lambda : file_read.FileRead  (self.window, fill_link_dictionary=True))
        self.file_menu.add_command(label="Save",     accelerator="Ctrl+s"    , command=lambda : file_write.FileWrite(self.window, design, "save"))
        self.file_menu.add_command(label="Save as ..."                       , command=lambda : file_write.FileWrite(self.window, design, "save_as"))
        self.file_menu.add_command(label="Convert VHDL into HSE design .."   , command=lambda : convert_hdl.ConvertHdl(self.window, "VHDL"))
        self.file_menu.add_command(label="Convert Verilog into HSE design ..", command=lambda : convert_hdl.ConvertHdl(self.window, "Verilog"))
        self.file_menu.add_command(label="Print"                             , command=self.__print)
        self.file_menu.add_command(label="Iconify all windows"               , command=self.window.iconify_all_windows)
        self.file_menu.add_command(label="Exit window"                       , command=self.window.close_this_window)
        self.file_menu.add_command(label="Exit all windows"                  , command=self.window.close_all_windows)

        self.hdl_menu_button = ttk.Menubutton(self.menue_frame, text="HDL")
        self.hdl_menu = tk.Menu(self.hdl_menu_button)
        self.hdl_menu_button.configure(menu=self.hdl_menu)
        self.hdl_menu.add_command(label="Generate single Module"          , accelerator="Ctrl+g", command=self.__generate_single_module)
        self.hdl_menu.add_command(label="Generate through Hierarchy"      , accelerator="Ctrl+G", command=self.__generate_through_hierarchy)
        self.hdl_menu.add_command(label="Force Generate through Hierarchy",                       command=self.__force_generate_through_hierarchy)
        self.hdl_menu.add_command(label="Compile single Module"           , accelerator="Ctrl+p", command=lambda : hdl_compile.CompileHDL(self.window, self.window.notebook_top,
                                                                                                                    self.window.notebook_top.log_tab, design,
                                                                                                                    compile_through_hierarchy=False, flipflop_stat=False))
        self.hdl_menu.add_command(label="Compile through Hierarchy"       , accelerator="Ctrl+P", command=lambda : hdl_compile.CompileHDL(self.window, self.window.notebook_top,
                                                                                                                    self.window.notebook_top.log_tab, design,
                                                                                                                    compile_through_hierarchy=True, flipflop_stat=False))
        self.hdl_menu.add_command(label="Compile through Hierarchy with flipflop statistic"     ,command=lambda : hdl_compile.CompileHDL(self.window, self.window.notebook_top,
                                                                                                                    self.window.notebook_top.log_tab, design,
                                                                                                                    compile_through_hierarchy=True, flipflop_stat=True))

        self.tool_title = ttk.Label(self.menue_frame, text="HDL-SCHEM-Editor", font=("Arial", 15))

        # self.edit_menu_button = ttk.Menubutton(self.menue_frame, text="Edit")
        # self.edit_menu = tk.Menu(self.edit_menu_button)
        # self.edit_menu_button.configure(menu=self.edit_menu)
        # self.edit_menu.add_command(label="Change path ...", command=lambda : change_path.ChangePath())

        self.search_frame        = ttk.Frame(self.menue_frame, borderwidth=2)#, relief=RAISED)

        self.search_string_var   = tk.StringVar()
        self.search_string_var.set("")
        self.search_string_entry = ttk.Entry (self.search_frame, width=23, textvariable=self.search_string_var)
        self.search_button       = ttk.Button(self.search_frame, text="Find",
                                                 command=lambda: find_replace.FindReplace(self.window, self.search_string_var, self.replace_string, replace=False))
        self.search_string_entry.bind('<Return>', lambda event : find_replace.FindReplace(self.window, self.search_string_var, self.replace_string, replace=False))
        self.search_button.bind      ('<Return>', lambda event : find_replace.FindReplace(self.window, self.search_string_var, self.replace_string, replace=False))
        self.search_string_entry.grid (row=0, column=0)
        self.search_button.grid       (row=0, column=1)
        self.search_is_running = False

        self.search_replace_label = ttk.Label(self.search_frame, text=" ")
        self.search_replace_label.grid (row=0, column=3)

        self.replace_string       = tk.StringVar()
        self.replace_string.set("")
        self.replace_string_entry = ttk.Entry (self.search_frame, width=23, textvariable=self.replace_string) # Defined before the button to keep the focus order convenient.
        self.replace_button       = ttk.Button(self.search_frame, text="Find & Replace",
                                                  command=lambda: find_replace.FindReplace(self.window, self.search_string_var, self.replace_string, replace=True))
        self.replace_string_entry.bind('<Return>', lambda event : find_replace.FindReplace(self.window, self.search_string_var, self.replace_string, replace=True))
        self.replace_button.bind      ('<Return>', lambda event : find_replace.FindReplace(self.window, self.search_string_var, self.replace_string, replace=True))
        self.replace_string_entry.grid (row=0, column=4)
        self.replace_button.grid       (row=0, column=5)
        self.search_replace_hier_var    = tk.BooleanVar  (value=False)
        self.search_replace_hier_label  = ttk.Label  (self.search_frame, text=" ")
        self.search_replace_hier_check  = ttk.Checkbutton(self.search_frame, text="Find/Replace through hierarchy", variable=self.search_replace_hier_var, width=35)
        self.search_replace_hier_label.grid (row=0, column=6)
        self.search_replace_hier_check.grid (row=0, column=7)

        self.info_menu_button = ttk.Menubutton(self.menue_frame, text="Info")
        self.info_menu = tk.Menu(self.info_menu_button)
        self.info_menu_button.configure(menu=self.info_menu)
        self.info_menu.add_command(label="About", command=lambda : messagebox.showinfo("About:", constants.HEADER_STRING))

        self.file_menu_button.grid    (row=0, column=0)
        self.hdl_menu_button .grid    (row=0, column=1)
        self.tool_title      .grid    (row=0, column=2)
        #self.edit_menu_button.grid    (row=0, column=2)
        self.search_frame.grid        (row=0, column=3)
        self.info_menu_button.grid    (row=0, column=4)
        self.menue_frame.columnconfigure(2, weight=1)

    def __generate_single_module(self):
        # Saving is necessary, otherwise the content of the HDL might be "newer" than the content of the HSE file:
        if self.window.title().endswith("*"):
            file_write.FileWrite(self.window, self.design, "save")
        hdl_generate.GenerateHDL(self, self.window.notebook_top, self.design, self.hdl_tab, write_to_file=True, top=True, write_message=True)

    def __generate_through_hierarchy(self):
        # Saving is necessary, otherwise the content of the HDL might be "newer" than the content of the HSE file:
        if self.window.title().endswith("*"):
            file_write.FileWrite(self.window, self.design, "save")
        hdl_generate_through_hierarchy.HdlGenerateHierarchy(self.root, self.window, force=False, write_to_file=True) # Also all submodules are saved if they were changed.

    def __force_generate_through_hierarchy(self):
        # Saving is necessary, otherwise the content of the HDL might be "newer" than the content of the HSE file:
        if self.window.title().endswith("*"):
            file_write.FileWrite(self.window, self.design, "save")
        hdl_generate_through_hierarchy.HdlGenerateHierarchy(self.root, self.window, force=True, write_to_file=True) # Also all submodules are saved if they were changed.

    def __print(self):
        bus_wires = self.__reduce_line_width_for_better_picture()
        rectangle = self.window.notebook_top.diagram_tab.canvas.bbox("all")
        height = rectangle[3] - rectangle[1]
        width  = rectangle[2] - rectangle[0]
        module_name = self.design.get_module_name()
        working_directory_of_design = self.design.get_working_directory()
        if working_directory_of_design=="":
            messagebox.showinfo("Print:", 'Please provide a "Working directory" in the Control-Tab before printing.\nPrinting aborted.')
            return
        self.window.notebook_top.diagram_tab.grid_drawer.remove_grid()
        self.window.notebook_top.diagram_tab.canvas.postscript(colormode="color",
                                                               file=working_directory_of_design + '/' + module_name + ".eps",
                                                               rotate=True,
                                                               height=height,
                                                               width=width,
                                                               x=rectangle[0],
                                                               y=rectangle[1])
        self.window.notebook_top.diagram_tab.grid_drawer.draw_grid()
        self.__restore_line_width(bus_wires)
        messagebox.showinfo("Print:", "Created " + working_directory_of_design + '/' + module_name + ".eps")

    def __reduce_line_width_for_better_picture(self):
        # Reduce line width for a better picture:
        all_canvas_ids = self.window.notebook_top.diagram_tab.canvas.find_all()
        bus_wires = []
        for canvas_id in all_canvas_ids:
            if self.window.notebook_top.diagram_tab.canvas.type(canvas_id)=="line":
                if self.window.notebook_top.diagram_tab.canvas.itemcget(canvas_id, "width")=="3.0":
                    bus_wires.append(canvas_id)
                    self.window.notebook_top.diagram_tab.canvas.itemconfigure(canvas_id, width=1)
        return bus_wires

    def __restore_line_width(self, bus_wires):
        for bus_wire in bus_wires:
            # Restore original line width:
            self.window.notebook_top.diagram_tab.canvas.itemconfigure(bus_wire, width=3)

    def create_binding_for_menu_accelerators(self):
        # This method is called at any time, when the focus is set to another widget of the window, which is way to often.
        # But it was chosen as solution, because the accelerators must be bound to the schematic window (from severals) which has focus.
        # This method is called by the event <FocusIn>.
        # As block_edit also uses Control-s to save data, FileWrite must not be bound to Control-s, when block_edit is active.
        # Bindings of the menus:
        if not self.window.design.get_block_edit_is_running():
            self.window.bind_all("<Control-s>", lambda event : file_write.FileWrite(self.window, self.design, "save"))
        self.window.bind_all("<Control-S>", lambda event : self.__create_capslock_warning('S'))
        self.window.bind_all("<Control-o>", lambda event : file_read.FileRead (self.window, fill_link_dictionary=True))
        self.window.bind_all("<Control-O>", lambda event : self.__create_capslock_warning('O'))
        self.window.bind_all("<Control-g>", lambda event : self.__generate_single_module())
        self.window.bind_all("<Control-G>", lambda event : self.__generate_through_hierarchy())
        self.window.bind_all("<Control-n>", lambda event : self.window_class(self.root, self.wire_class, self.signal_name_class,
                                                                     self.input_class, self.output_class, self.inout_class, self.block_class, self.symbol_reading_class,
                                                                     self.symbol_insertion_class, self.symbol_instance_class, self.hdl_generate_class,
                                                                     self.design_data_class, self.generate_frame_class, visible=True, working_directory=self.working_directory))
        self.window.bind_all("<Control-N>", lambda event : self.__create_capslock_warning('N'))
        self.window.bind_all("<Control-p>", lambda event : hdl_compile.CompileHDL(self.window, self.window.notebook_top,
                                                                                  self.window.notebook_top.log_tab, self.design,
                                                                                  compile_through_hierarchy=False, flipflop_stat=False))
        self.window.bind_all("<Control-P>", lambda event : hdl_compile.CompileHDL(self.window, self.window.notebook_top,
                                                                                  self.window.notebook_top.log_tab, self.design,
                                                                                  compile_through_hierarchy=True, flipflop_stat=False))
        self.window.bind_all('<Control-f>', lambda event : self.__start_find())
        self.window.bind_all("<Control-F>", lambda event : self.__create_capslock_warning('F'))
        # Don't use "bind_all" for Ctrl-z, as otherwise a Ctrl-z in the interface tab (as an example) also causes an undo() in the diagram_tab:
        self.window.notebook_top.diagram_tab.canvas.bind("<Control-z>", lambda event: self.window.notebook_top.diagram_tab.undo())
        self.window.notebook_top.diagram_tab.canvas.bind("<Control-Z>", lambda event: self.window.notebook_top.diagram_tab.redo())
        self.window.notebook_top.diagram_tab.canvas.bind("<Delete>"   , lambda event: self.window.notebook_top.diagram_tab.delete_selection())
        self.window.notebook_top.diagram_tab.canvas.bind("<Control-c>", lambda event: self.window.notebook_top.diagram_tab.copy())
        self.window.notebook_top.diagram_tab.canvas.bind("<Control-v>", self.window.notebook_top.diagram_tab.paste)

    def __create_capslock_warning(self, character):
        messagebox.showwarning("HDl_SCHEM-Editor", "There is no shortcut for the capital letter '" + character + "'.\n" +
                               "Perhaps CapsLock is activated.")

    def __start_find(self):
        try:
            self.search_string_entry.focus_set()
            self.search_string_var.set(self.root.selection_get()) # unklar ob das gut ist, es verwirrt Visual Studio Code.
        except Exception:
            pass
