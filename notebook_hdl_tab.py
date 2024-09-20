""" This notebook tab shows the generated VHDL code. """
import tkinter as tk
from   tkinter import ttk
from   tkinter import messagebox

import re
import custom_text
import vhdl_parsing
import hdl_generate_functions
import link_dictionary
import hdl_generate_through_hierarchy

class NotebookHdlTab():
    def __init__(self, root, schematic_window, notebook):
        self.root = root
        self.schematic_window = schematic_window
        self.line_number_under_pointer = -1
        self.last_line_number_of_file1 = 0
        self.size_of_file1_line_number = 0
        self.size_of_file2_line_number = 0
        self.generation_failed         = False # Changed by hdl_generate.GenerateHdl() below
        self.func_id_jump              = None
        self.hdl_frame = ttk.Frame(notebook)
        self.hdl_frame.grid()
        self.hdl_frame.columnconfigure(0, weight=1)
        self.hdl_frame.rowconfigure   (0, weight=1)
        self.hdl_frame_text = custom_text.CustomText(self.hdl_frame, window=self.schematic_window,
                                    parser=vhdl_parsing.VhdlParser, tag_list=vhdl_parsing.VhdlParser.tag_list, text_name="generated_hdl",
                                    has_line_numbers=True, undo=False, font=("Courier", 10))
        self.hdl_frame_text.grid(row=0, column=0, sticky=(tk.N,tk.W,tk.E,tk.S))
        self.hdl_frame_text.columnconfigure((0,0), weight=1)
        self.hdl_frame_text.config(state=tk.DISABLED)
        self.hdl_frame_text.bind("<Motion>", self.__cursor_move)
        self.hdl_frame_text_scroll = ttk.Scrollbar (self.hdl_frame, orient=tk.VERTICAL, cursor='arrow', command=self.hdl_frame_text.yview)
        self.hdl_frame_text.config(yscrollcommand=self.hdl_frame_text_scroll.set)
        self.hdl_frame_text_scroll.grid   (row=0, column=1, sticky=(tk.W,tk.E,tk.S,tk.N))
        notebook.add(self.hdl_frame, sticky=tk.N+tk.E+tk.W+tk.S, text="generated HDL")

    def __cursor_move(self, event):
        if self.hdl_frame_text.get("1.0", tk.END + "- 1 char")=="":
            return
        # Determine current cursor position:
        delta_x = self.hdl_frame_text.winfo_pointerx() - self.hdl_frame_text.winfo_rootx()
        delta_y = self.hdl_frame_text.winfo_pointery() - self.hdl_frame_text.winfo_rooty()
        index_string = self.hdl_frame_text.index(f"@{delta_x},{delta_y}")
        # Determine current line number:
        line_number = int(re.sub(r"\..*", "", index_string))
        if line_number!=self.line_number_under_pointer:
            self.hdl_frame_text.tag_delete("underline")
            file_name, file_name_architecture = self.schematic_window.design.get_file_names()
            if line_number>self.last_line_number_of_file1:
                line_number_in_file = line_number - self.last_line_number_of_file1
                selected_file = file_name_architecture
                start_index   = self.size_of_file2_line_number
                #print("In architect: selected_file, start_index =", selected_file, start_index, line_number_in_file)
            else:
                line_number_in_file = line_number
                selected_file = file_name
                start_index   = self.size_of_file1_line_number
            #print(link_dictionary.LinkDictionary.link_dict_reference.link_dict[selected_file])
            while self.hdl_frame_text.get(str(line_number) + '.' + str(start_index-1))==' ':
                start_index += 1
            if selected_file in link_dictionary.LinkDictionary.link_dict_reference.link_dict: # Can for example happen with empty architecture or module content.
                if line_number_in_file in link_dictionary.LinkDictionary.link_dict_reference.link_dict[selected_file]["lines"]:
                    self.hdl_frame_text.tag_add("underline", str(line_number) + "." + str(start_index-1), str(line_number+1) + ".0" )
                    self.hdl_frame_text.tag_config("underline", underline=1)
                    self.func_id_jump = self.hdl_frame_text.bind("<Control-Button-1>",
                                                                lambda event : link_dictionary.LinkDictionary.link_dict_reference.jump_to_source(selected_file,
                                                                                                                                                line_number_in_file))
                else:
                    self.hdl_frame_text.unbind("<Button-1>"      , self.func_id_jump)
                    self.func_id_jump = None
            self.line_number_under_pointer = line_number

    def update_hdl_tab_from(self, new_dict, fill_link_dictionary):
        if new_dict["language"]=="VHDL":
            if new_dict["number_of_files"]==1:
                filename = new_dict["generate_path_value"] + "/" + new_dict["module_name"] + ".vhd"
                filename_architecture = None
            else:
                filename              = new_dict["generate_path_value"] + "/" + new_dict["module_name"] + "_e.vhd"
                if "architecture_name" in new_dict:
                    architecture_name = new_dict["architecture_name"]
                else:
                    architecture_name = "struct"
                filename_architecture = new_dict["generate_path_value"] + "/" + new_dict["module_name"] + '_' + architecture_name + ".vhd"
        else: # verilog
            filename = new_dict["generate_path_value"] + "/" + new_dict["module_name"] + ".v"
            filename_architecture = None
        # Compare modification time of HDL file against modification_time of design file (.hse):
        hdl = ""
        if not hdl_generate_functions.HdlGenerateFunctions.hdl_must_be_generated(self.schematic_window.design.get_path_name(),
                                                                                 filename, filename_architecture, show_message=False):
            # HDL-file(s) exists and are "newer" than the design-file.
            try:
                fileobject = open(filename, 'r', encoding="utf-8")
                entity = fileobject.read()
                fileobject.close()
                hdl += self._add_line_numbers(entity)
                self.last_line_number_of_file1 = hdl.count("\n")
                self.size_of_file1_line_number = len(str(self.last_line_number_of_file1)) + 2 # "+2" because of string ": "
                self.size_of_file2_line_number = 0
            except FileNotFoundError:
                messagebox.showerror("Error in HDL-SCHEM-Editor", "File " + filename + " could not be opened for copying into HDL-Tab.")
            if new_dict["number_of_files"]==2:
                # HDL-file exists and was generated after the design-file was saved.
                try:
                    fileobject = open(filename_architecture, 'r', encoding="utf-8")
                    arch = fileobject.read()
                    fileobject.close()
                    hdl += self._add_line_numbers(arch)
                    self.size_of_file2_line_number = len(str(hdl.count("\n"))) + 2 # "+2" because of string ": "
                except FileNotFoundError:
                    messagebox.showwarning("Error in HDL-SCHEM-Editor", "File " + filename + " (architecture-file) could not be opened for copying into HDL-Tab.")
            self.hdl_frame_text.insert_text(hdl, state_after_insert="disabled")
            if fill_link_dictionary:
                link_dictionary.LinkDictionary.link_dict_reference.clear_link_dict(filename)
                if filename_architecture!="":
                    link_dictionary.LinkDictionary.link_dict_reference.clear_link_dict(filename_architecture)
                hdl_generate_through_hierarchy.HdlGenerateHierarchy(self.root, self.schematic_window, force=False, write_to_file=False)
        else:
            # No HDL was found which could be loaded into HDL-tab, so clear the HDL-tab:
            self.hdl_frame_text.insert_text("", state_after_insert="disabled")

    def _add_line_numbers(self, text):
        text_lines = text.split("\n")
        text_length_as_string = str(len(text_lines))
        number_of_needed_digits_as_string = str(len(text_length_as_string))
        content_with_numbers = ""
        for line_number, line in enumerate(text_lines, start=1):
            content_with_numbers += format(line_number, "0" + number_of_needed_digits_as_string + "d") + ": " + line + "\n"
        return content_with_numbers

    def find_string(self, search_string):
        all_text_widgets = [self.hdl_frame_text]
        number_of_matches = 0
        for text_widget in all_text_widgets:
            index = "1.0"
            while index!="":
                index = text_widget.search(search_string, index, nocase=1, stopindex=tk.END)
                if index!="":
                    number_of_matches += 1
                    self.schematic_window.notebook_top.show_tab("generated HDL")
                    index2 = index + " + " + str(len(search_string)) + " chars"
                    text_widget.tag_add      ("selected", index, index2)
                    text_widget.tag_configure("selected", background="blue")
                    text_widget.see(index)
                    continue_search = messagebox.askyesno("Continue ...", "Find next?")
                    text_widget.tag_remove   ("selected", index, index2)
                    if not continue_search:
                        return -1
                    index = index2
        return number_of_matches
