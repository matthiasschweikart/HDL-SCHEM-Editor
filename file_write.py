""" Write the schematic into a JSON file """
from tkinter.filedialog import asksaveasfilename
from tkinter import messagebox
import json
#import notebook_diagram_tab

class FileWrite():
    def __init__(self, window, design, command):
        old_path_name = design.get_path_name()
        if old_path_name.startswith("unnamed") or command=="save_as":
            path_name = asksaveasfilename(defaultextension=".hse",
                                          initialfile = design.get_module_name(),
                                          filetypes=(("HDL-Schem-Editor files","*.hse"),("all files","*.*")))
            if path_name!="":
                design.set_path_name(path_name)
        if design.get_path_name()!="" and not design.get_path_name().startswith("unnamed"):
            self.__save_in_file(window, design, old_path_name)
    def __save_in_file(self, window, design, old_path_name):
        path_name = design.get_path_name()
        try:
            fileobject = open(path_name, 'w', encoding="utf-8")
            fileobject.write(json.dumps(design.get_design_dictionary_for_all_architectures(), indent=4, default=str))
            fileobject.close()
            design.update_window_title(written=True)
            window.__class__.open_window_dict[window] = path_name
            window.quick_access_object.path_name_changed(old_path_name, path_name)
        except FileNotFoundError:
            messagebox.showerror("Error in HDL-SCHEM-Editor", "File " + path_name + " could not be found.")
        except PermissionError:
            messagebox.showerror("Error in HDL-SCHEM-Editor", "File " + path_name + " has no write permission.")
