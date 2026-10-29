"""Root Window of HDL-SCHEM-Editor"""

import argparse
import json
import multiprocessing
import re
import tkinter as tk
import urllib.request
from os.path import exists
from pathlib import Path
from tkinter import messagebox

import constants
from codegen import hdl_generate_through_hierarchy
from data_io import file_read
from gui import link_dictionary, schematic_window, style_admin


class MyTk(tk.Tk):
    """This class extends the tkinter Tk class by some attributes for the HDL-SCHEM-Editor."""

    def __init__(self):
        super().__init__()
        self.diagram_background_color = constants.DIAGRAM_BACKGROUND_COLOR_NORMAL_MODE
        self.generated_entity_bg = constants.PALE_BROWN
        self.generated_arch_bg = constants.PALE_YELLOW
        self.show_grid = True


class HdlSchemEditor:
    """Root Window of HDL-SCHEM-Editor"""

    def __init__(self):
        print(constants.HEADER_STRING)
        self.start_messages = constants.HEADER_STRING + "\n"
        args = self._parse_arguments()
        if not args.no_version_check:
            self._check_version()
        if not args.no_message:
            self._read_message()
        root = MyTk()
        root.withdraw()
        working_directory, graphical_mode = self._configure_hse(root)
        link_dictionary.LinkDictionary(root)
        root.style_admin_ref = style_admin.StyleAdmin(root)  # Sets style to "Normal Mode".
        self._open_first_window(root, working_directory, graphical_mode, args)
        root.mainloop()

    def _parse_arguments(self):
        argument_parser = argparse.ArgumentParser()
        argument_parser.add_argument("filename", nargs="?")
        argument_parser.add_argument(
            "-no_version_check",
            action="store_true",
            help="HDL-SCHEM-Editor will not check for a newer version at start.",
        )
        argument_parser.add_argument(
            "-no_message", action="store_true", help="HDL-SCHEM-Editor will not check for a message at start."
        )
        arguments = argument_parser.parse_args()
        return arguments

    def _check_version(self):
        try:
            print("Checking for a newer version ...")
            self.start_messages += "Checking for a newer version ..." + "\n"
            source = urllib.request.urlopen("http://www.hdl-schem-editor.de/index.php")
            website_source = str(source.read())
            version_start = website_source.find("Version")
            new_version = website_source[version_start : version_start + 24]
            end_index = new_version.find("(")
            new_version = new_version[:end_index]
            new_version = re.sub(" ", "", new_version)
            constant_version = re.sub(" ", "", constants.VERSION)
            if new_version != constant_version:
                print(
                    "Please update to the new version of HDL-SCHEM-Editor available at http://www.hdl-schem-editor.de"
                )
                self.start_messages += (
                    "Please update to the new version of HDL-SCHEM-Editor available at http://www.hdl-schem-editor.de"
                    + "\n"
                )
            else:
                print("Your version of HDL-SCHEM-Editor is up to date.")
                self.start_messages += "Your version of HDL-SCHEM-Editor is up to date." + "\n"
        except urllib.error.URLError:
            print("HDL-SCHEM-Editor version could not be checked, as you are offline.")
            self.start_messages += "HDL-SCHEM-Editor version could not be checked, as you are offline." + "\n"
        except ConnectionRefusedError:
            print("HDL-SCHEM-Editor version could not be checked, as connecting was refused.")
            self.start_messages += "HDL-SCHEM-Editor version could not be checked, as connecting was refused." + "\n"

    def _read_message(self):
        try:
            source = urllib.request.urlopen("http://www.hdl-schem-editor.de/message.txt")
            message = source.read()
            messages = message.decode()
            print(messages)
            self.start_messages += messages
        except urllib.error.URLError:
            print("Message file was not found.")
            self.start_messages += "Message file was not found." + "\n"
        except ConnectionRefusedError:
            pass

    def _configure_hse(self, root):
        self._set_word_boundaries(root)  # Defines what is selected at a doubleclick at a word in text.
        try:
            with open(Path.home() / ".hdl-schem-editor.rc", encoding="utf-8") as fileobject:
                data = fileobject.read()
                message = "Configuration file " + str(Path.home()) + "/.hdl-schem-editor.rc was read."
                print(message)
                self.start_messages += message + "\n"
            config_dict = json.loads(data)
            work_dir = config_dict["working_directory"]
            # Modify some attributes of the root, which are accessed by other modules:
            root.diagram_background_color = config_dict.get(
                "schematic_background", constants.DIAGRAM_BACKGROUND_COLOR_NORMAL_MODE
            )
            root.generated_entity_bg = config_dict.get("generated_entity_bg", constants.PALE_BROWN)
            root.generated_arch_bg = config_dict.get("generated_arch_bg", constants.PALE_YELLOW)
            graphical_mode = config_dict.get("graphical_mode", "Normal Mode")
        except Exception:  # pylint: disable=broad-except
            work_dir = ""
            graphical_mode = "Normal Mode"
            print("Configuration file " + str(Path.home()) + "/.hdl-schem-editor.rc was not found.")
            self.start_messages += (
                "Configuration file " + str(Path.home()) + "/.hdl-schem-editor.rc was not found." + "\n"
            )
        return work_dir, graphical_mode

    def _open_first_window(self, root, working_directory, graphical_mode, args):
        # root.diagram_background_color is used inside SchematicWindow to set the initial background color:
        window = schematic_window.SchematicWindow(root, visible=True, working_directory=working_directory)
        if graphical_mode == "Dark Mode":  # The first window is always opened in "Normal Mode".
            window.menu_bar.switch_between_normal_and_dark_mode()
        if args.filename is not None:
            if not exists(args.filename):
                messagebox.showerror("Error in HDL-SCHEM-Editor", "File " + args.filename + " was not found.")
            else:
                file_read.FileRead(window, args.filename)
                hdl_generate_through_hierarchy.HdlGenerateHierarchy(root, window, force=False, write_to_file=False)
        window.notebook_top.log_tab.log_frame_text.insert_text(self.start_messages, state_after_insert="disabled")

    def _set_word_boundaries(self, root):
        # this first statement triggers tcl to autoload the library
        # that defines the variables we want to override.
        root.tk.call("tcl_wordBreakAfter", "", 0)
        # This defines what tcl considers to be a "word". For more
        # information see http://www.tcl.tk/man/tcl8.5/TclCmd/library.htm#M19 :
        root.tk.call("set", "tcl_wordchars", "[a-zA-Z0-9_]")
        root.tk.call("set", "tcl_nonwordchars", "[^a-zA-Z0-9_]")


if __name__ == "__main__":
    multiprocessing.freeze_support()  # required on Windows when using ProcessPoolExecutor
    HdlSchemEditor()
