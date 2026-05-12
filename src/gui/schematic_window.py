"""This is the schematic entry window (Toplevel)."""

import json
import os
import sys
import tkinter as tk
from os.path import exists
from pathlib import Path
from tkinter import messagebox, ttk

from codegen import hdl_generate_through_hierarchy
from data_io import design_data_selector, file_read, file_write, write_data_creator
from gui import hierarchy_tree, menu_bar, notebook_diagram_tab, notebook_top, quick_access


class SchematicWindow(tk.Toplevel):
    """This is the schematic entry window (Toplevel)."""

    window_id = 0
    number_of_open_windows = 0
    open_window_dict = {}

    def __init__(
        self,
        root,
        visible,
        working_directory,
    ):
        super().__init__()
        self.root = root
        self.geometry("1400x800")
        if not visible:
            self.withdraw()
        self.protocol("WM_DELETE_WINDOW", self.close_this_window)
        self.closing_in_process = False

        # Set the application icon
        try:
            icon_path = self._get_resource_path("hse_icon.ico")
            if icon_path.exists():
                self.iconbitmap(icon_path)
            else:
                print(f"Warning: Icon file not found at {icon_path}")
        except Exception as e:  # pylint: disable=broad-except
            print(f"Warning: Could not set application icon: {e}")

        self._build_window(working_directory)
        unnamed_name = "unnamed" + str(self.window_id + 1)
        self.design.set_path_name(unnamed_name)
        self.bind("<FocusIn>", lambda event: self.menu_bar.create_binding_for_menu_accelerators())
        # Was introduced, because sometimes it seemed like the virtual event FocusIn did not reach the correct window:
        self.update_idletasks()
        self.event_generate("<FocusIn>", when="now")
        self._add_quick_access_button_for_each_already_open_module_to_this_window()
        SchematicWindow.number_of_open_windows += 1
        SchematicWindow.window_id += 1
        SchematicWindow.open_window_dict[self] = (
            unnamed_name  # when a file is read or written, then the value is replaced by the file name
        )
        if visible:
            self._add_quick_access_button_for_this_module_to_all_open_modules(unnamed_name, unnamed_name)
        self._store_module_name_in_design_data(unnamed_name)
        self.window_width = 0
        self.window_height = 0
        self.bind("<Configure>", self._check_for_window_resize)

    def _get_resource_path(self, resource_name: str) -> Path:
        """Get the path to a resource file, handling both development and PyInstaller environments."""
        # The object "sys" is either the Python interpreter or the executable (created by Pyinstaller).
        # Pyinstaller adds the attribute "frozen" with value true to the executable, while the Python interpreter does
        # not have an attribute "frozen". sys.__MEIPATH is an attribute added by Pyinstaller, which contains
        # the temporary folder where the unpacked executable is located.
        base_path = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).parent.parent
        return base_path / "rsc" / resource_name

    def _check_for_window_resize(self, event):
        if event.widget == self and (event.width != self.window_width or event.height != self.window_height):
            if event.height != self.window_height:
                self.update_idletasks()
                self.notebook_top.interface_tab.adjust_sash_positions()
                self.update_idletasks()
                self.notebook_top.internals_tab.adjust_sash_positions()
            self.window_width = event.width
            self.window_height = event.height
            self.update_idletasks()
            self.notebook_top.diagram_tab.adjust_scroll_region_at_zoom(1.0)
            self.notebook_top.diagram_tab.grid_drawer.draw_grid()

    def _build_window(self, working_directory):
        self.columnconfigure(0, weight=1)  # The window has only 1 column.
        row_for_menubar = 0
        row_for_notebook = 1
        row_for_quick_access = 2
        self.rowconfigure(row_for_menubar, weight=0)
        self.rowconfigure(row_for_notebook, weight=1)
        last_line_frame = ttk.Frame(self, relief=tk.RAISED, borderwidth=4)
        last_line_frame.grid(row=row_for_quick_access, column=0, sticky=(tk.W, tk.S, tk.E, tk.N))
        last_line_frame.columnconfigure(0, weight=1)
        last_line_frame.columnconfigure(1, weight=0)
        self.design = design_data_selector.DesignDataSelector(self.root, window=self)
        self.write_data_creator_ref = write_data_creator.WriteDataCreator(standard_size=self.design.get_font_size())
        self.hierarchytree = hierarchy_tree.HierarchyTree(
            self.root, schematic_window=self, frame=last_line_frame, column=1, row=0
        )
        self.notebook_top = notebook_top.NotebookTop(
            self.root,
            schematic_window=self,
            design=self.design,
            column=0,
            row=row_for_notebook,
            working_directory=working_directory,
        )
        self.menu_bar = menu_bar.MenuBar(
            schematic_window=self,
            design=self.design,
            root=self.root,
            column=0,
            row=row_for_menubar,
            window_class=SchematicWindow,
            hdl_tab=self.notebook_top.hdl_tab,
            log_tab=self.notebook_top.log_tab,
            working_directory=working_directory,
        )
        self.quick_access_object = quick_access.QuickAccess(
            schematic_window=self, frame=last_line_frame, column=0, row=0
        )

    def open_this_window(self):
        """Opens this window, if it is withdrawn. Called by quick_access.QuickAccess."""
        if self.state() == "withdrawn":  # This window is only open for the creation of the link-dictionary.
            self._add_quick_access_button_for_this_module_to_all_open_modules(
                self.design.get_path_name(), self.design.get_module_name()
            )
        self.deiconify()  # needed for "withdrawn" windows and windows which the user iconified
        # Sometimes using the link from log-tab to schematic showed full-view instead of a small area,
        # this here might help:
        self.after_idle(self.lift_window)

    def lift_window(self):
        """Brings this window to the front. Called by open_this_window()."""
        self.lift()
        self.attributes("-topmost", True)
        self.after(2000, self.attributes, "-topmost", False)

    def _add_quick_access_button_for_each_already_open_module_to_this_window(self):
        for open_window in SchematicWindow.open_window_dict:
            if (
                open_window != notebook_diagram_tab.NotebookDiagramTab.clipboard_window
                and open_window.state() != "withdrawn"
            ):
                self.quick_access_object.add_quick_access_button(
                    open_window, open_window.design.get_path_name(), open_window.design.get_module_name()
                )

    def _add_quick_access_button_for_this_module_to_all_open_modules(self, path_name, module_name):
        for open_window in SchematicWindow.open_window_dict:
            open_window.quick_access_object.add_quick_access_button(self, path_name, module_name)
            if open_window == self:
                self.quick_access_object.quick_access_buttons_dict[path_name].config(style="Quick_Access.TButton")

    def _store_module_name_in_design_data(self, unnamed_name):
        # As now all buttons exist, the module_name can be set.
        self.notebook_top.control_tab.module_name.set(
            unnamed_name
        )  # Changes the name in design_data by a "trace", but adds '*' to window_title.
        self.design.update_window_title(written=True)  # removes '*' from window_title

    def close_this_window(self):
        """Closes this window."""
        # If a schematic-window is closed, which does not contain the toplevel window of a design,
        # then the schematic-window will only be withdrawn which means:
        #   The schematic-window will disappear and
        #   will not be visible as an icon in any taskbar,
        #   but will still exist in memory for HDL generation and hierarchy tree.
        # If the closed schematic-window is a toplevel, then it will be completely destroyed and
        # removed from open_window_dict and also disappear in the hierarchy tree.
        if self._abort_closing():
            return
        self.quick_access_object.remove_quick_access_button(self.design.get_path_name())
        if self.hierarchytree.this_module_is_top_module:
            SchematicWindow.number_of_open_windows -= 1
            del SchematicWindow.open_window_dict[self]
            if self._get_number_of_withdrawn_windows() == SchematicWindow.number_of_open_windows:
                # Only unvisible schematic-windows are left.
                self._write_rc_file()
                self.root.destroy()
            else:
                self.hierarchytree.refresh_treeviews()  # necessary because a toplevel is removed
                self.destroy()
        else:
            self.withdraw()
            # The following is needed because setting self.hierarchytree.this_module_is_top_module to True
            # is not implemented correctly when an unnamed design is opened, when several unnamed designs are open,
            # when 2 toplevels are opened simultaneously.
            # Therefore even when self.hierarchytree.this_module_is_top_module is False, it must be checked
            # if the tool must be stopped:
            if self._get_number_of_withdrawn_windows() == SchematicWindow.number_of_open_windows:
                # Only unvisible schematic-windows are left.
                self._write_rc_file()
                self.root.quit()

    def _write_rc_file(self):
        config_dictionary = {}
        config_dictionary["schematic_background"] = self.notebook_top.diagram_tab.canvas.cget("bg")
        config_dictionary["working_directory"] = self.design.get_working_directory()
        try:
            with open(Path.home() / ".hdl-schem-editor.rc", "w", encoding="utf-8") as fileobject:
                fileobject.write(json.dumps(config_dictionary, indent=4, default=str))
                print("Created configuration file " + str(Path.home()) + "/.hdl-schem-editor.rc")
        except Exception as e:  # pylint: disable=broad-except
            print("HDL-SCHEM-Editor-Warning: Could not write to file " + str(Path.home()) + "/.hdl-schem-editor.rc.", e)

    def close_all_windows(self):
        """Closes all windows. Called by menu_bar.MenuBar when the user clicks at "Exit" in the menu."""
        local_copy_of_open_window_dict = dict(SchematicWindow.open_window_dict)
        for window in local_copy_of_open_window_dict:
            if window.state() != "withdrawn":
                window.close_this_window()

    def iconify_all_windows(self):
        """Iconifies all windows. Called by menu_bar.MenuBar when the user clicks at "Minimize All" in the menu."""
        for window in SchematicWindow.open_window_dict:
            if (
                window.state() != "withdrawn"
            ):  # The unvisible windows shall not be iconified, because they will get visible as icon then.
                window.iconify()

    def _abort_closing(self):
        if self.title().endswith("*"):
            self.closing_in_process = True
            result = messagebox.askyesnocancel(
                "HDL-SCHEM-Editor",
                f"There are unsaved changes in design:\n{self.title()[:-1]}\nDo you want to save them?",
                default="cancel",
                icon="warning",
            )
            self.closing_in_process = False
            if result is None:
                return True  # Closing is canceled.
            if result is True:
                ref = file_write.FileWrite(self, self.design, "save")
                if ref.success is False:
                    return True  # Closing is canceled.
            # The window will only be withdrawn, the changes must be removed for the case
            # when HDL-SCHEM-Editor keeps running.
            path_name = self.design.get_path_name()
            # Must be removed before the file is read, otherwise there would pop up a window asking to read the tmpfile:
            self._remove_back_up_file(path_name)
            self._restore_to_version_before_changes(path_name)
        return False

    def _remove_back_up_file(self, path_name):
        if os.path.isfile(path_name + ".tmp"):
            os.remove(path_name + ".tmp")

    def _restore_to_version_before_changes(self, path_name):
        self.title("")  # Remove the '*' so that file read ignores the changes.
        if exists(path_name):  # Needed, because the changed file may never have been saved.
            file_read.FileRead(self, path_name, self.design.get_architecture_name())
            hdl_generate_through_hierarchy.HdlGenerateHierarchy(self.root, self, force=False, write_to_file=False)

    def _get_number_of_withdrawn_windows(self):
        number_of_withdrawn_windows = 0
        for open_window in SchematicWindow.open_window_dict:
            if open_window.state() == "withdrawn":
                number_of_withdrawn_windows += 1
        return number_of_withdrawn_windows

    def update_schematic_window_from(self, new_dict):
        """Updates the schematic window from the given dictionary."""
        self.notebook_top.update_notebook_top_from(new_dict)

    @classmethod
    def open_subwindow(cls, root, filename, architecture_name):
        """Opens a new window"""
        sub_window = SchematicWindow(
            root,
            visible=False,
            working_directory="",
        )
        file_read.FileRead(sub_window, filename, architecture_name)
        return sub_window

    @classmethod
    def open_clipboard_window(cls, root):
        """Creates a clipboard window, which is used for copy and paste."""
        sub_window = SchematicWindow(
            root,
            visible=False,
            working_directory="",
        )
        return sub_window
