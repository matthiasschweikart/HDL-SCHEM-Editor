""" Write the schematic into a JSON file """
from tkinter.filedialog import asksaveasfilename
from tkinter import messagebox
import json
import os
#import notebook_diagram_tab

class FileWrite():
    def __init__(self, window, design, command):
        actual_path_name = design.get_path_name()
        self.success = False
        if command=="backup":
            if not actual_path_name.startswith("unnamed"):
                self.__save_in_file(window, design, actual_path_name + ".tmp", actual_path_name + ".tmp")
        else:
            if actual_path_name.startswith("unnamed") or command=="save_as":
                new_path_name = asksaveasfilename(defaultextension=".hse",
                                            initialfile = design.get_module_name(),
                                            filetypes=(("HDL-Schem-Editor files","*.hse"),("all files","*.*")))
                if new_path_name!="":
                    design.set_path_name(new_path_name)
            new_or_actual_path_name = design.get_path_name()
            if new_or_actual_path_name!="" and not new_or_actual_path_name.startswith("unnamed"):
                self.success = self.__save_in_file(window, design, new_or_actual_path_name, actual_path_name)

    def __save_in_file(self, window, design, new_or_actual_path_name, actual_path_name):
        # design zoomen auf standard
        # Falls es mehrere Architectures gibt, müssen alle gezoomt werden.
        # Oder man bringt sie beim Arch-Wechsel immer auf die Standardgröße.
        window.config(cursor="watch")
        success = False
        try:
            fileobject = open(new_or_actual_path_name, 'w', encoding="utf-8")
            fileobject.write(json.dumps(design.get_design_dictionary_for_all_architectures(), indent=4, default=str))
            fileobject.close()
            success = True
            if not actual_path_name.endswith(".tmp"):
                window.__class__.open_window_dict[window] = new_or_actual_path_name
                if new_or_actual_path_name!=actual_path_name:
                    window.quick_access_object.path_name_changed(actual_path_name, new_or_actual_path_name)
                if os.path.isfile(actual_path_name + ".tmp"):
                    os.remove(actual_path_name + ".tmp")
                design.update_window_title(written=True)
        except FileNotFoundError:
            messagebox.showerror("Error in HDL-SCHEM-Editor", "File " + new_or_actual_path_name + " could not be found at write.")
        except PermissionError:
            messagebox.showerror("Error in HDL-SCHEM-Editor", "File " + new_or_actual_path_name + " has no write permission.")
        # design zurück zoomen auf aktuelle Größe
        window.config(cursor="arrow")
        return success
