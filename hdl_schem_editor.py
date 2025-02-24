""" Root Window of HDL-SCHEM-Editor
"""

import os
from   os.path import exists
import tkinter as tk
from   tkinter import ttk
from   tkinter import messagebox
import urllib.request
import re
import argparse
import json

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
        self.schematic_background_color          = "#ffffff" # white
        self.schematic_background_color_at_start = "#ffffff" # white
        self.show_grid = True

def read_message():
    try:
        source  = urllib.request.urlopen("http://www.hdl-schem-editor.de/message.txt")
        message = source.read()
        print(message.decode())
    except urllib.error.URLError:
        print("Message file was not found.")
    except ConnectionRefusedError:
        pass

def check_version():
    try:
        print("Checking for a newer version ...")
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
        else:
            print("Your version of HDL-SCHEM-Editor is up to date.")
    except urllib.error.URLError:
        print("HDL-SCHEM-Editor version could not be checked, as you are offline.")
    except ConnectionRefusedError:
        print("HDL-SCHEM-Editor version could not be checked, as connecting was refused.")

def set_word_boundaries():
    # this first statement triggers tcl to autoload the library
    # that defines the variables we want to override.
    root.tk.call('tcl_wordBreakAfter', '', 0)
    # This defines what tcl considers to be a "word". For more
    # information see http://www.tcl.tk/man/tcl8.5/TclCmd/library.htm#M19 :
    root.tk.call('set', 'tcl_wordchars'   ,  '[a-zA-Z0-9_]')
    root.tk.call('set', 'tcl_nonwordchars', '[^a-zA-Z0-9_]')

print(constants.HEADER_STRING)

argument_parser = argparse.ArgumentParser()
argument_parser.add_argument("filename", nargs='?')
argument_parser.add_argument("-no_version_check", action="store_true", help="HDL-SCHEM-Editor will not check for a newer version at start.")
argument_parser.add_argument("-no_message"      , action="store_true", help="HDL-SCHEM-Editor will not check for a message at start.")
args = argument_parser.parse_args()
if not args.no_version_check:
    check_version()
if not args.no_message:
    read_message()

root = MyTk()
root.withdraw()
set_word_boundaries() # Defines what is selected at a doubleclick at a word in text.
style = ttk.Style(root)
style.theme_use("default")
style.configure("My.TLabel", font=("TkDefaultFont", 9, "underline")) # Used for the property menu of an instance.
style.configure("Quick_Access.TButton", background="darkgrey")

try:
    fileobject = open(".hdl-schem-editor.rc", 'r', encoding="utf-8")
    data = fileobject.read()
    fileobject.close()
    print("Configuration was read from file: " + os.getcwd() + '/.hdl-schem-editor.rc')
    config_dict = json.loads(data)
    if "schematic_background" in config_dict:
        root.schematic_background_color          = config_dict["schematic_background"]
        root.schematic_background_color_at_start = config_dict["schematic_background"]
except Exception:
    pass

link_dictionary.LinkDictionary(root)
window = schematic_window.SchematicWindow(root, wire_insertion.Wire, signal_name.SignalName,
                                       interface_input.Input, interface_output.Output, interface_inout.Inout,
                                       block_insertion.Block,
                                       symbol_reading.SymbolReading, symbol_insertion.SymbolInsertion, symbol_instance.Symbol, hdl_generate.GenerateHDL,
                                       design_data.DesignData, generate_frame.GenerateFrame)

if args.filename is not None:
    if not exists(args.filename):
        messagebox.showerror("Error in HDL-SCHEM-Editor", "File " + args.filename + " was not found.")
    else:
        file_read.FileRead(window, args.filename, fill_link_dictionary=True)

root.mainloop()
