"""Create the menu bar of the schematic editor window"""

import tkinter as tk
from tkinter import messagebox, ttk

import constants
from actions import convert_hdl, find_replace, hdl_compile
from codegen import hdl_generate, hdl_generate_through_hierarchy
from data_io import file_read, file_write

from . import help_selection, help_shortcuts


class MenuBar:
    """This class creates the menu bar of the schematic editor window."""

    def __init__(
        self,
        schematic_window,
        design,
        root,
        column,
        row,
        window_class,
        hdl_tab,
        log_tab,
        working_directory,
    ):
        self.window = schematic_window
        self.design = design
        self.root = root
        self.window_class = window_class
        self.working_directory = working_directory
        self.hdl_tab = hdl_tab
        self.log_tab = log_tab
        self.generation_failed = False  # This attribute is set by GenerateHDL, but not used by class MenuBar.
        self.menue_frame = ttk.Frame(self.window, borderwidth=2, relief=tk.RAISED, style="My.TFrame")
        self.menue_frame.grid(row=row, column=column, sticky=(tk.N, tk.W, tk.E, tk.S))

        self.file_menu_button = ttk.Menubutton(self.menue_frame, text="File", style="My.TMenubutton")
        self.hdl_menu_button = ttk.Menubutton(self.menue_frame, text="HDL", style="My.TMenubutton")
        self.prefs_menu_button = ttk.Menubutton(self.menue_frame, text="Prefs", style="My.TMenubutton")
        self.tool_title = ttk.Label(self.menue_frame, text="HDL-SCHEM-Editor", font=("Arial", 15), style="My.TLabel")
        self.search_frame = ttk.Frame(self.menue_frame, borderwidth=2, style="My.TFrame")  # , relief=RAISED)
        self.info_menu_button = ttk.Menubutton(self.menue_frame, text="Info", style="My.TMenubutton")

        self.file_menu_button.grid(row=0, column=0)
        self.hdl_menu_button.grid(row=0, column=1)
        self.prefs_menu_button.grid(row=0, column=2)
        self.tool_title.grid(row=0, column=3)
        self.search_frame.grid(row=0, column=4)
        self.info_menu_button.grid(row=0, column=5)
        self.menue_frame.columnconfigure(3, weight=1)

        self.file_menu = tk.Menu(self.file_menu_button)
        self.file_menu_button.configure(menu=self.file_menu)
        self.file_menu.add_command(
            label="New",
            accelerator="Ctrl+n",
            command=lambda: window_class(
                root,
                visible=True,
                working_directory=self.working_directory,
            ),
        )
        self.file_menu.add_command(label="Open ...", accelerator="Ctrl+o", command=self._fileread)
        self.file_menu.add_command(
            label="Save", accelerator="Ctrl+s", command=lambda: file_write.FileWrite(self.window, design, "save")
        )
        self.file_menu.add_command(
            label="Save as ...", command=lambda: file_write.FileWrite(self.window, design, "save_as")
        )
        self.file_menu.add_command(
            label="Convert VHDL into HSE design ..",
            command=lambda: convert_hdl.ConvertHdl(self.root, self.window, "VHDL"),
        )
        self.file_menu.add_command(
            label="Convert Verilog into HSE design ..",
            command=lambda: convert_hdl.ConvertHdl(self.root, self.window, "Verilog"),
        )
        self.file_menu.add_command(label="Print", command=self._print)
        self.file_menu.add_command(label="Iconify all windows", command=self.window.iconify_all_windows)
        self.file_menu.add_command(label="Exit window", command=self.window.close_this_window)
        self.file_menu.add_command(label="Exit all windows", command=self.window.close_all_windows)

        self.hdl_menu = tk.Menu(self.hdl_menu_button)
        self.hdl_menu_button.configure(menu=self.hdl_menu)
        self.hdl_menu.add_command(
            label="Generate single Module", accelerator="Ctrl+g", command=self._generate_single_module
        )
        self.hdl_menu.add_command(
            label="Generate through Hierarchy", accelerator="Ctrl+G", command=self._generate_through_hierarchy
        )
        self.hdl_menu.add_command(
            label="Force Generate through Hierarchy", command=self._force_generate_through_hierarchy
        )
        self.hdl_menu.add_command(
            label="Compile single Module",
            accelerator="Ctrl+p",
            command=lambda: hdl_compile.CompileHDL(
                self.window,
                self.window.notebook_top,
                self.window.notebook_top.log_tab,
                design,
                compile_through_hierarchy=False,
                flipflop_stat=False,
            ),
        )
        self.hdl_menu.add_command(
            label="Compile through Hierarchy",
            accelerator="Ctrl+P",
            command=lambda: hdl_compile.CompileHDL(
                self.window,
                self.window.notebook_top,
                self.window.notebook_top.log_tab,
                design,
                compile_through_hierarchy=True,
                flipflop_stat=False,
            ),
        )
        self.hdl_menu.add_command(
            label="Compile through Hierarchy with flipflop statistic",
            command=lambda: hdl_compile.CompileHDL(
                self.window,
                self.window.notebook_top,
                self.window.notebook_top.log_tab,
                design,
                compile_through_hierarchy=True,
                flipflop_stat=True,
            ),
        )

        self.prefs_menu = tk.Menu(self.prefs_menu_button, tearoff=0)
        self.prefs_menu_button.configure(menu=self.prefs_menu)
        self.prefs_menu.add_command(
            label="Dark Mode",
            command=self.switch_between_normal_and_dark_mode,
            font=("Arial", 10),
        )

        self.search_string_var = tk.StringVar()
        self.search_string_var.set("")
        self.search_string_entry = ttk.Entry(
            self.search_frame, width=23, textvariable=self.search_string_var, style="My.TEntry"
        )
        self.search_button = ttk.Button(
            self.search_frame,
            text="Find",
            command=lambda: find_replace.FindReplace(
                self.window,
                self.search_string_var.get().lower(),
                self.replace_string.get(),
                self.search_replace_hier_var.get(),
                replace=False,
            ),
            style="My.TButton",
        )
        self.search_string_entry.bind(
            "<Return>",
            lambda event: find_replace.FindReplace(
                self.window,
                self.search_string_var.get().lower(),
                self.replace_string.get(),
                self.search_replace_hier_var.get(),
                replace=False,
            ),
        )
        self.search_button.bind(
            "<Return>",
            lambda event: find_replace.FindReplace(
                self.window,
                self.search_string_var.get().lower(),
                self.replace_string.get(),
                self.search_replace_hier_var.get(),
                replace=False,
            ),
        )
        self.search_string_entry.grid(row=0, column=0)
        self.search_button.grid(row=0, column=1)
        self.search_is_running = False

        self.search_replace_label = ttk.Label(self.search_frame, text=" ", style="My.TLabel")
        self.search_replace_label.grid(row=0, column=3)

        self.replace_string = tk.StringVar()
        self.replace_string.set("")
        self.replace_string_entry = ttk.Entry(
            self.search_frame, width=23, textvariable=self.replace_string, style="My.TEntry"
        )  # Defined before the button to keep the focus order convenient.
        self.replace_button = ttk.Button(
            self.search_frame,
            text="Find & Replace",
            command=lambda: find_replace.FindReplace(
                self.window,
                self.search_string_var.get().lower(),
                self.replace_string.get(),
                self.search_replace_hier_var.get(),
                replace=True,
            ),
            style="My.TButton",
        )
        self.replace_string_entry.bind(
            "<Return>",
            lambda event: find_replace.FindReplace(
                self.window,
                self.search_string_var.get().lower(),
                self.replace_string.get(),
                self.search_replace_hier_var.get(),
                replace=True,
            ),
        )
        self.replace_button.bind(
            "<Return>",
            lambda event: find_replace.FindReplace(
                self.window,
                self.search_string_var.get().lower(),
                self.replace_string.get(),
                self.search_replace_hier_var.get(),
                replace=True,
            ),
        )
        self.replace_string_entry.grid(row=0, column=4)
        self.replace_button.grid(row=0, column=5)
        self.search_replace_hier_var = tk.BooleanVar(value=False)
        self.search_replace_hier_label = ttk.Label(self.search_frame, text=" ", style="My.TLabel")
        self.search_replace_hier_check = ttk.Checkbutton(
            self.search_frame,
            text="Find/Replace through hierarchy",
            variable=self.search_replace_hier_var,
            width=35,
            style="My.TCheckbutton",
        )
        self.search_replace_hier_label.grid(row=0, column=6)
        self.search_replace_hier_check.grid(row=0, column=7)

        self.info_menu = tk.Menu(self.info_menu_button)
        self.info_menu_button.configure(menu=self.info_menu)
        self.help_menu = tk.Menu(self.info_menu, tearoff=0)
        self.info_menu.add_cascade(
            label="Help",
            menu=self.help_menu,
            font=("Arial", 10),
        )
        self.info_menu.add_command(
            label="About", command=lambda: messagebox.showinfo("About:", constants.HEADER_STRING)
        )
        self.help_menu.add_command(
            label="Editing Shortcuts",
            command=lambda: help_shortcuts.ShortCutsDialog(self.root),
            font=("Arial", 10),
        )
        self.help_menu.add_command(
            label="Text Selection",
            command=lambda: help_selection.SelectionDialog(self.root),
            font=("Arial", 10),
        )

    def _fileread(self):
        file_read.FileRead(self.window)
        # This is necessary to fill the link-dictionary:
        hdl_generate_through_hierarchy.HdlGenerateHierarchy(self.root, self.window, force=False, write_to_file=False)

    def _generate_single_module(self):
        # Saving is necessary, otherwise the content of the HDL might be "newer" than the content of the HSE file:
        if self.window.title().endswith("*"):
            file_write.FileWrite(self.window, self.design, "save")
        hdl_generate.GenerateHDL(
            self, self.window.notebook_top, self.design, self.hdl_tab, write_to_file=True, write_message=True
        )

    def _generate_through_hierarchy(self):
        # Saving is necessary, otherwise the content of the HDL might be "newer" than the content of the HSE file:
        if self.window.title().endswith("*"):
            file_write.FileWrite(self.window, self.design, "save")
        hdl_generate_through_hierarchy.HdlGenerateHierarchy(
            self.root, self.window, force=False, write_to_file=True
        )  # Also all submodules are saved if they were changed.

    def _force_generate_through_hierarchy(self):
        # Saving is necessary, otherwise the content of the HDL might be "newer" than the content of the HSE file:
        if self.window.title().endswith("*"):
            file_write.FileWrite(self.window, self.design, "save")
        hdl_generate_through_hierarchy.HdlGenerateHierarchy(
            self.root, self.window, force=True, write_to_file=True
        )  # Also all submodules are saved if they were changed.

    def switch_between_normal_and_dark_mode(self) -> None:  # Called by menu item and by _open_first_window()
        """Switch between "Dark Mode" and "Normal Mode"."""
        new_mode = self.prefs_menu.entrycget(0, "label")
        self.root.style_admin_ref.switch_style(new_mode)
        # Configure in all open windows all widgets which do not support the ttk.style feature:
        for window in type(self.window).open_window_dict:
            window.menu_bar.configure_this_window_for_mode(new_mode)

    def configure_this_window_for_mode(self, new_mode):
        if new_mode == "Dark Mode":
            self.prefs_menu.entryconfig(0, label="Normal Mode")
        else:
            self.prefs_menu.entryconfig(0, label="Dark Mode")
        self._configure_menus(new_mode)
        self._configure_listboxes(new_mode)
        declaration_text_list = (
            self.window.notebook_top.interface_tab.interface_generics_text,
            self.window.notebook_top.internals_tab.architecture_first_declarations_text,
            self.window.notebook_top.hdl_tab.hdl_frame_text,
            self.window.notebook_top.log_tab.log_frame_text,
        )
        if self.window.notebook_top.control_tab.language.get() == "VHDL":
            declaration_text_list += (
                self.window.notebook_top.interface_tab.interface_packages_text,
                self.window.notebook_top.internals_tab.internals_packages_text,
                self.window.notebook_top.internals_tab.architecture_last_declarations_text,
            )
        for text_widget in declaration_text_list:
            text_widget.configure_mode(new_mode)
        # Configure all elements already inserted into the diagram:
        wire_refs = self.design.get_list_of_canvas_wire_references()
        for wire_ref in wire_refs:
            wire_ref.configure_mode(new_mode)
        signal_name_refs = self.design.get_list_of_canvas_signal_name_references()
        for signal_name_ref in signal_name_refs:
            signal_name_ref.configure_mode(new_mode)
        generate_frame_refs = self.design.get_list_of_canvas_generate_frame_references()
        for generate_frame_ref in generate_frame_refs:
            generate_frame_ref.configure_mode(new_mode)
        block_refs = self.design.get_list_of_canvas_block_references()
        for block_ref in block_refs:
            block_ref.configure_mode(new_mode)
        self._configure_diagram_tab_background(new_mode)
        instance_refs = self.design.get_list_of_canvas_instance_references()
        for instance_ref in instance_refs:
            instance_ref.configure_mode(new_mode)
        interface_refs = self.design.get_list_of_canvas_interface_references()
        for interface_ref in interface_refs:
            interface_ref.configure_mode(new_mode)
        # # The new background color must be stored for sure in the design file, as at any read from file
        # # the background color is determined by the value found in design file:
        # if (
        #     project_manager.root.title() != "tk"
        #     and project_manager.root.title() != "tk*"
        #     and not project_manager.root.title().startswith("unnamed")
        # ):
        #     file_handling.save()

    def _configure_menus(self, new_mode):
        menu_list = [self.file_menu, self.hdl_menu, self.prefs_menu, self.info_menu, self.help_menu]
        for menu in menu_list:
            if new_mode == "Dark Mode":
                menu.configure(background="black", foreground="white", activebackground="gray")
            else:
                menu.configure(background="gray92", foreground="black", activebackground="royal blue")

    def _configure_listboxes(self, new_mode):
        self.root.option_clear()
        if new_mode == "Normal Mode":
            self.root.option_clear()
            self.root.option_add("*TCombobox*Listbox.background", "white")
            self.root.option_add("*TCombobox*Listbox.foreground", "black")
            self.root.option_add("*TCombobox*Listbox.selectBackground", "#0078D7")
            self.root.option_add("*TCombobox*Listbox.selectForeground", "white")
            self.root.option_add("*TCombobox*Listbox.highlightThickness", "1")
        else:
            self.root.option_add("*TCombobox*Listbox.background", "black")
            self.root.option_add("*TCombobox*Listbox.foreground", "white")
            self.root.option_add("*TCombobox*Listbox.selectBackground", "black")
            self.root.option_add("*TCombobox*Listbox.selectForeground", "white")
            self.root.option_add("*TCombobox*Listbox.highlightThickness", "1")

    def _configure_diagram_tab_background(self, new_mode):
        diagram_background = self.window.notebook_top.diagram_tab.canvas.cget("bg")
        if new_mode == "Dark Mode":
            if self._tk_color_to_hex(diagram_background) == self._tk_color_to_hex(
                constants.DIAGRAM_BACKGROUND_COLOR_NORMAL_MODE
            ):
                # Change the color because the user has not changed the background color from the default.
                diagram_background = constants.DIAGRAM_BACKGROUND_COLOR_DARK_MODE
            grid_color = constants.GRID_COLOR_DARK_MODE
        else:
            if self._tk_color_to_hex(diagram_background) == self._tk_color_to_hex(
                constants.DIAGRAM_BACKGROUND_COLOR_DARK_MODE
            ):
                # Change the color because the user has not changed the background color from the default.
                diagram_background = constants.DIAGRAM_BACKGROUND_COLOR_NORMAL_MODE
            grid_color = constants.GRID_COLOR_NORMAL_MODE
        self.window.notebook_top.diagram_tab.canvas.configure(bg=diagram_background)
        self.root.diagram_background_color = diagram_background
        self.window.notebook_top.diagram_tab.grid_drawer.remove_grid()
        self.window.notebook_top.diagram_tab.grid_drawer.color = grid_color
        self.window.notebook_top.diagram_tab.grid_drawer.draw_grid()

    def _tk_color_to_hex(self, color_name: str) -> str:
        r16, g16, b16 = self.root.winfo_rgb(color_name)  # 0..65535
        # auf 8-bit umrechnen (0..255)
        r8, g8, b8 = r16 // 256, g16 // 256, b16 // 256
        return f"#{r8:02x}{g8:02x}{b8:02x}"

    def _print(self):
        bus_wires = self._reduce_line_width_for_better_picture()
        rectangle = self.window.notebook_top.diagram_tab.canvas.bbox("all")
        height = rectangle[3] - rectangle[1]
        width = rectangle[2] - rectangle[0]
        module_name = self.design.get_module_name()
        working_directory_of_design = self.design.get_working_directory()
        if working_directory_of_design == "":
            messagebox.showinfo(
                "Print:", 'Please provide a "Working directory" in the Control-Tab before printing.\nPrinting aborted.'
            )
            return
        self.window.notebook_top.diagram_tab.grid_drawer.remove_grid()
        self.window.notebook_top.diagram_tab.canvas.postscript(
            colormode="color",
            file=working_directory_of_design + "/" + module_name + ".eps",
            rotate=True,
            height=height,
            width=width,
            x=rectangle[0],
            y=rectangle[1],
        )
        self.window.notebook_top.diagram_tab.grid_drawer.draw_grid()
        self._restore_line_width(bus_wires)
        messagebox.showinfo("Print:", "Created " + working_directory_of_design + "/" + module_name + ".eps")

    def _reduce_line_width_for_better_picture(self):
        # Reduce line width for a better picture:
        all_canvas_ids = self.window.notebook_top.diagram_tab.canvas.find_all()
        bus_wires = []
        for canvas_id in all_canvas_ids:
            if (
                self.window.notebook_top.diagram_tab.canvas.type(canvas_id) == "line"
                and self.window.notebook_top.diagram_tab.canvas.itemcget(canvas_id, "width") == "3.0"
            ):
                bus_wires.append(canvas_id)
                self.window.notebook_top.diagram_tab.canvas.itemconfigure(canvas_id, width=1)
        return bus_wires

    def _restore_line_width(self, bus_wires):
        for bus_wire in bus_wires:
            # Restore original line width:
            self.window.notebook_top.diagram_tab.canvas.itemconfigure(bus_wire, width=3)

    def create_binding_for_menu_accelerators(self):
        """This method creates bindings for menu accelerators."""
        # This method is called at any time, when the focus is set to another widget of the window, which is way to
        # often. But it was chosen as solution, because the accelerators must be bound to the schematic window which
        # has focus.
        # The method is called by the event <FocusIn>.
        # As block_edit also uses Control-s to save data, FileWrite must not be bound to Control-s, when block_edit
        # is active.
        # Bindings of the menus:
        if not self.window.design.get_block_edit_is_running():
            self.window.bind_all("<Control-s>", lambda event: file_write.FileWrite(self.window, self.design, "save"))
        self.window.bind_all("<Control-S>", lambda event: self._create_capslock_warning("S"))
        self.window.bind_all("<Control-o>", lambda event: self._fileread())
        self.window.bind_all("<Control-O>", lambda event: self._create_capslock_warning("O"))
        self.window.bind_all("<Control-g>", lambda event: self._generate_single_module())
        self.window.bind_all("<Control-G>", lambda event: self._generate_through_hierarchy())
        self.window.bind_all(
            "<Control-n>",
            lambda event: self.window_class(
                self.root,
                visible=True,
                working_directory=self.working_directory,
            ),
        )
        self.window.bind_all("<Control-N>", lambda event: self._create_capslock_warning("N"))
        self.window.bind_all(
            "<Control-p>",
            lambda event: hdl_compile.CompileHDL(
                self.window,
                self.window.notebook_top,
                self.window.notebook_top.log_tab,
                self.design,
                compile_through_hierarchy=False,
                flipflop_stat=False,
            ),
        )
        self.window.bind_all(
            "<Control-P>",
            lambda event: hdl_compile.CompileHDL(
                self.window,
                self.window.notebook_top,
                self.window.notebook_top.log_tab,
                self.design,
                compile_through_hierarchy=True,
                flipflop_stat=False,
            ),
        )
        self.window.bind_all("<Control-f>", lambda event: self._start_find())
        self.window.bind_all("<Control-F>", lambda event: self._create_capslock_warning("F"))
        # Don't use "bind_all" for Ctrl-z, as otherwise a Ctrl-z in the interface tab (as an example) also
        # causes an undo() in the diagram_tab:
        self.window.notebook_top.diagram_tab.canvas.bind(
            "<Control-z>", lambda event: self.window.notebook_top.diagram_tab.undo()
        )
        self.window.notebook_top.diagram_tab.canvas.bind(
            "<Control-Z>", lambda event: self.window.notebook_top.diagram_tab.redo()
        )
        self.window.notebook_top.diagram_tab.canvas.bind(
            "<Delete>", lambda event: self.window.notebook_top.diagram_tab.delete_selection()
        )
        self.window.notebook_top.diagram_tab.canvas.bind(
            "<Control-c>", lambda event: self.window.notebook_top.diagram_tab.copy()
        )
        self.window.notebook_top.diagram_tab.canvas.bind("<Control-v>", self.window.notebook_top.diagram_tab.paste)

    def _create_capslock_warning(self, character):
        messagebox.showwarning(
            "HDl_SCHEM-Editor",
            "There is no shortcut for the capital letter '" + character + "'.\n" + "Perhaps CapsLock is activated.",
        )

    def _start_find(self):
        try:
            self.search_string_entry.focus_set()
            self.search_string_var.set(
                self.root.selection_get()
            )  # The selection_get() method confuses sometimes Visual Studio Code.
        except Exception:  # pylint: disable=broad-except
            pass
