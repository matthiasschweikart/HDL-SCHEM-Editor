""" 
Write the schematic into a JSON file:
command can be: "save", "save_as", "backup"
The attribute "success" is used by close_this_window(): Without success the window stays opened.
"""
from tkinter.filedialog import asksaveasfilename
from tkinter import messagebox
import json
import os

class FileWrite():
    def __init__(self, window, design, command):
        self.success = False
        actual_path_name = design.get_path_name()
        path_name = self._determine_path_name(design, command, actual_path_name)
        if path_name=="":
            return
        design_dictionary = self._get_design_dictionary(window, design, command)
        window.config(cursor="watch")
        try:
            self.success = self._write_to_file(path_name, design_dictionary)
            if command!="backup":
                self._update_data_base(window, design, actual_path_name, path_name)
        except FileNotFoundError:
            messagebox.showerror("Error in HDL-SCHEM-Editor", "File " + path_name + " could not be found at write.")
        except PermissionError:
            messagebox.showerror("Error in HDL-SCHEM-Editor", "File " + path_name + " has no write permission.")
        except Exception:
            messagebox.showerror("Error in HDL-SCHEM-Editor", "File " + path_name + " is not writable.")
        window.config(cursor="arrow")

    def _determine_path_name(self, design, command, actual_path_name):
        if command=="backup":
            if actual_path_name.startswith("unnamed"):
                return "" # No ".tmp"-file shall be created.
            return actual_path_name + ".tmp"
        if command=="save_as" or actual_path_name.startswith("unnamed"):
            new_path_name = asksaveasfilename(defaultextension=".hse",
                                              initialfile = design.get_module_name(),
                                              filetypes=(("HDL-Schem-Editor files","*.hse"),("all files","*.*")))
            if new_path_name!="":
                design.set_path_name(new_path_name)
            return new_path_name # new_path_name is "", if the user aborted the dialog
        return actual_path_name

    def _get_design_dictionary(self, window, design, command):
        if command=="backup":
            return design.get_design_dictionary_for_all_architectures()
        zoom_factor = window.write_data_creator_ref.zoom_graphic_to_standard_size(window, design.get_font_size())
        design_dictionary = design.get_design_dictionary_for_all_architectures()
        design_dictionary = window.write_data_creator_ref.round_numbers(design_dictionary)
        window.write_data_creator_ref.zoom_graphic_back_to_actual_size(window, zoom_factor)
        return design_dictionary

    def _write_to_file(self, path_name, design_dictionary):
        with open(path_name, 'w', encoding="utf-8") as fileobject:
            fileobject.write(json.dumps(design_dictionary, indent=4, default=str))
        return True

    def _update_data_base(self, window, design, actual_path_name, path_name):
        window.__class__.open_window_dict[window] = path_name
        if path_name!=actual_path_name:
            window.quick_access_object.path_name_changed(actual_path_name, path_name)
        if os.path.isfile(actual_path_name + ".tmp"):
            os.remove(actual_path_name + ".tmp")
        design.update_window_title(written=True)
