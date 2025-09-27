""" Root Window of HDL-SCHEM-Editor
"""

from   os.path import exists
import tkinter as tk
from   tkinter import ttk
from   tkinter import messagebox
import urllib.request
import re
import argparse
import json
from pathlib import Path

import constants
import schematic_window

# These classes are imported here to prevent "circular imports".
# They are needed in notebook_diagram_tab.py.
import wire_insertion
import interface_input
import interface_output
import interface_inout
import signal_name
import block_insertion
import symbol_reading
import symbol_insertion
import symbol_instance
import hdl_generate
import design_data
import file_read
import generate_frame
import link_dictionary

class MyTk(tk.Tk):
    def __init__(self):
        super().__init__()
        self.schematic_background_color = "#ffffff" # white
        self.show_grid = True

class HdlSchemEditor:
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
        working_directory = self._configure_hse(root)
        link_dictionary.LinkDictionary(root)
        self._open_first_window(root, working_directory, args)
        root.mainloop()

    def _parse_arguments(self):
        argument_parser = argparse.ArgumentParser()
        argument_parser.add_argument("filename", nargs='?')
        argument_parser.add_argument("-no_version_check", action="store_true", help="HDL-SCHEM-Editor will not check for a newer version at start.")
        argument_parser.add_argument("-no_message"      , action="store_true", help="HDL-SCHEM-Editor will not check for a message at start.")
        arguments = argument_parser.parse_args()
        return arguments

    def _check_version(self):
        try:
            print("Checking for a newer version ...")
            self.start_messages += "Checking for a newer version ..." + "\n"
            source = urllib.request.urlopen("http://www.hdl-schem-editor.de/index.php")
            website_source   = str(source.read())
            version_start    = website_source.find("Version")
            new_version      = website_source[version_start:version_start+24]
            end_index        = new_version.find("(")
            new_version      = new_version[:end_index]
            new_version      = re.sub(" ", "", new_version)
            constant_version = re.sub(" ", "", constants.VERSION)
            if new_version!=constant_version:
                print("Please update to the new version of HDL-SCHEM-Editor available at http://www.hdl-schem-editor.de")
                self.start_messages += "Please update to the new version of HDL-SCHEM-Editor available at http://www.hdl-schem-editor.de" + "\n"
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
            source  = urllib.request.urlopen("http://www.hdl-schem-editor.de/message.txt")
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
        self._set_word_boundaries(root) # Defines what is selected at a doubleclick at a word in text.
        style = ttk.Style(root)
        style.theme_use("default")
        style.configure("My.TLabel", font=("TkDefaultFont", 9, "underline")) # Used for the property menu of an instance.
        style.configure("Quick_Access.TButton", background="darkgrey")
        try:
            with open(Path.home()/".hdl-schem-editor.rc", 'r', encoding="utf-8") as fileobject:
                data = fileobject.read()
                print("Configuration file " + str(Path.home()) + "/.hdl-schem-editor.rc was read.")
                self.start_messages += "Configuration file " + str(Path.home()) + "/.hdl-schem-editor.rc was read." + "\n"
            config_dict = json.loads(data)
            root.schematic_background_color = config_dict["schematic_background"]
            work_dir                        = config_dict["working_directory"]
            #print("working-dir gefunden:", working_directory)
        except Exception:
            work_dir = ""
            print("Configuration file " + str(Path.home()) + "/.hdl-schem-editor.rc was not found.")
            self.start_messages += "Configuration file " + str(Path.home()) + "/.hdl-schem-editor.rc was not found." + "\n"
        return work_dir

    def _open_first_window(self, root, working_directory, args):
        window = schematic_window.SchematicWindow(root, wire_insertion.Wire, signal_name.SignalName,
                                            interface_input.Input, interface_output.Output, interface_inout.Inout,
                                            block_insertion.Block,
                                            symbol_reading.SymbolReading, symbol_insertion.SymbolInsertion, symbol_instance.Symbol, hdl_generate.GenerateHDL,
                                            design_data.DesignData, generate_frame.GenerateFrame, visible=True, working_directory=working_directory)
        if args.filename is not None:
            if not exists(args.filename):
                messagebox.showerror("Error in HDL-SCHEM-Editor", "File " + args.filename + " was not found.")
            else:
                file_read.FileRead(window, args.filename, fill_link_dictionary=True)
        window.notebook_top.log_tab.log_frame_text.insert_text(self.start_messages, state_after_insert="disabled")

    def _set_word_boundaries(self, root):
        # this first statement triggers tcl to autoload the library
        # that defines the variables we want to override.
        root.tk.call('tcl_wordBreakAfter', '', 0)
        # This defines what tcl considers to be a "word". For more
        # information see http://www.tcl.tk/man/tcl8.5/TclCmd/library.htm#M19 :
        root.tk.call('set', 'tcl_wordchars'   ,  '[a-zA-Z0-9_]')
        root.tk.call('set', 'tcl_nonwordchars', '[^a-zA-Z0-9_]')

if __name__ == "__main__":
    HdlSchemEditor()
