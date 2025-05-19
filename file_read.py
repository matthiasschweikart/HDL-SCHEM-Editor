""" Read the schematic from a JSON file """
from tkinter.filedialog import askopenfilename
from tkinter import messagebox
import json
import os

class FileRead():
    def __init__(self,
                 window, #: schematic_window.SchematicWindow,
                 filename="",
                 architecture_name="",
                 fill_link_dictionary=False # The default value must exist, because the preceeding parameters have one, but is never used.
                ):                          # fill_link_dictionary is False, when sub-modules of a toplevel design are read, as the link-dictionary shall only be filled once.
        if window.title().endswith("*"):
            discard = messagebox.askokcancel("HDL-Schem-Editor:", "There are unsaved changes in module " +
                                             window.design.get_module_name() + ", do you want to discard them?", default="cancel")
            if not discard:
                return
            window.title("")
        if filename=="": # Then the user used Control-o or the "file read"-menu-entry.
            filename = askopenfilename(filetypes=(("HDL-SCHEM-Editor files","*.hse"),("all files","*.*")))
            for open_window, open_file in window.__class__.open_window_dict.items():
                if filename==open_file:
                    self.__remove_backup_file(window.design.get_path_name() + ".tmp")
                    # The file is open, may be because it was automatically read in when only the toplevel was read in.
                    open_window.open_this_window()
                    # To be sure to get the latest content, update the window:
                    FileRead(open_window, filename, architecture_name, fill_link_dictionary=True)
                    if window!=open_window:
                        # Reading was started in an existing window, which the user wants to fill with new content.
                        # As there is already a window with the new content, this must used, but the existing window must be closed.
                        window.close_this_window()
                    return
        if filename!="": # filename is equal "", when the user has pressed "abort" or used the Escape-Key at askopenfilename().
            if filename: # Contrary to documention, instead of "" an empty tuple () is returned in case of abort.
                replaced_read_filename = filename
                if os.path.isfile(filename + ".tmp"):
                    answer = messagebox.askyesno("HDL-SCHEM-Editor",
                                                "Found BackUp-File\n" + filename + ".tmp\n" +
                                                "This file remains after a HDL-SCHEM-Editor crash and contains all latest changes.\n" +
                                                "Shall this file be read?")
                    if answer:
                        replaced_read_filename = filename + ".tmp"
                try:
                    fileobject = open(replaced_read_filename, 'r', encoding="utf-8")
                    data = fileobject.read()
                    fileobject.close()
                    self.__remove_backup_file(window.design.get_path_name() + ".tmp")
                    for block_edit in window.design.get_block_edit_list():
                        block_edit.close_edit_window()
                    for signal_name in window.design.get_signal_name_edit_list():
                        signal_name.delete_entry_window()
                    for line_name in window.design.get_edit_line_edit_list():
                        line_name.delete_entry_window()
                    for text_name in window.design.get_edit_text_edit_list():
                        text_name.delete_entry_window()
                    new_dict = json.loads(data)
                    window.design.set_path_name(filename)
                    window.design.clear_stack()
                    # As interface and internal-tab must be displayed to position sash correctly, this is done later: window.notebook_top.show_tab("Diagram")
                    new_dict_of_selected_architecture = window.design.extract_design_dictionary_of_active_architecture(new_dict, architecture_name)
                    window.update_schematic_window_from(new_dict_of_selected_architecture, fill_link_dictionary)
                    window.notebook_top.diagram_tab.canvas.focus()
                    window.__class__.open_window_dict[window] = filename
                except FileNotFoundError:
                    # This error happens only, when a sub-module file is missing.
                    # This may happen when a file is opened and during the opening the sub-module-file is tried to read.
                    # But when it is not found then only the hierarchy tree is incomplete.
                    # When the user double clicks this symbol then a different dialog pops up.
                    # So there is no need for this message here:
                    pass # messagebox.showerror("Error in HDL-SCHEM-Editor", "File " + filename + " could not be found at read.")

    def __remove_backup_file(self, path_name_backup):
        if os.path.isfile(path_name_backup):
            os.remove(path_name_backup)
