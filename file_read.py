""" Read the schematic from a JSON file """
from tkinter.filedialog import askopenfilename
from tkinter import messagebox
import json

class FileRead():
    def __init__(self,
                 window  , #: schematic_window.SchematicWindow,
                 filename="",
                 architecture_name="",
                 fill_link_dictionary=False
                ):
        if window.title().endswith("*"):
            discard = messagebox.askokcancel("HDL-Schem-Editor:", "There are unsaved changes in module " +
                                             window.design.get_module_name() + ", do you want to discard them?", default="cancel")
            if discard is False:
                return
            window.title("")
        if filename=="":
            filename = askopenfilename(filetypes=(("HDL-SCHEM-Editor files","*.hse"),("all files","*.*")))
            for open_window, open_file in window.__class__.open_window_dict.items():
                if filename==open_file:
                    #open_window.show_already_opened_window(open_window)
                    open_window.open_this_window()
                    FileRead (open_window, filename, architecture_name, fill_link_dictionary)
                    if window!=open_window:
                        window.close_this_window()
                        return
        if filename!="": # filename is equal "", when the user has pressed "abort" or used the Escape-Key.
            if filename: # Contrary to documention, instead of "" a () is returned in case of abort.
                try:
                    fileobject = open(filename, 'r', encoding="utf-8")
                    data = fileobject.read()
                    fileobject.close()
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
                    window.notebook_top.show_tab("Diagram")
                    new_dict_of_selected_architecture = window.design.extract_design_dictionary_of_active_architecture(new_dict, architecture_name)
                    window.update_schematic_window_from(new_dict_of_selected_architecture, fill_link_dictionary)
                    window.focus()
                    window.design.update_window_title(written=True)
                    window.__class__.open_window_dict[window] = filename
                    #print("Nach file_read: open_window_dict =", window.__class__.open_window_dict)
                except FileNotFoundError:
                    messagebox.showerror("Error in HDL-SCHEM-Editor", "File " + filename + " could not be found.")
