"""
This class creates HDL for a hierachical design through all hierarchies.
"""
from tkinter import messagebox
from datetime import datetime
import subprocess
import json

import schematic_window
import hdl_generate
import file_write
import hdl_generate_functions

class HdlGenerateHierarchy(): # Called by menu_bar (for generate HDL) or by update_hdl_tab_from().
    def __init__(self, root, window, force, write_to_file):
        self.window = window
        self.generation_failed = False
        if write_to_file:
            self.window.notebook_top.show_tab("Messages")
            self.window.notebook_top.log_tab.log_frame_text.insert_line(
                "\n+++++++++++++++++++++++++++++++++ " + datetime.today().ctime() +" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n",
                state_after_insert="disabled")
        opened_designs_list = [] # When a design is found the second time in a recursive hardware hierarchy loop, HDL generation must be aborted.
        self.__generate_for_window(root, window, opened_designs_list, force, write_to_file, top=True)
        if write_to_file:
            self.window.notebook_top.log_tab.log_frame_text.insert_line(
                "HDL generation ready.\n",
                state_after_insert="disabled")

    def __generate_for_window(self, root, window, opened_designs_list, force, write_to_file, top):
        self.__generate_hdl_for_this_schematic(window, force, write_to_file, top)
        self.__generate_hdl_for_all_symbols_in_this_schematic(window, root, opened_designs_list, force, write_to_file)

    def __generate_hdl_for_this_schematic(self, window, force, write_to_file, top):
        generate_path_value = window.design.get_generate_path_value()
        module_name         = window.design.get_module_name()
        architecture_name   = window.design.get_architecture_name()
        path_name           = window.design.get_path_name()
        if window.design.get_language()=="VHDL":
            if window.design.get_number_of_files()==1:
                hdlfilename = generate_path_value + "/" + module_name + ".vhd"
                hdlfilename_architecture = None
            else:
                hdlfilename              = generate_path_value + "/" + module_name + "_e.vhd"
                hdlfilename_architecture = generate_path_value + "/" + module_name + '_' + architecture_name + ".vhd"
        else:
            hdlfilename = generate_path_value + "/" + module_name + ".v"
            hdlfilename_architecture = None
        if (force or
            not write_to_file or # independent from the following check in the next line
            hdl_generate_functions.HdlGenerateFunctions.hdl_must_be_generated(path_name, hdlfilename, hdlfilename_architecture, show_message=False) or
            window.title().endswith("*")
            ):
            hdl_generate.GenerateHDL(self, window.notebook_top, window.design, window.notebook_top.hdl_tab, write_to_file, top)
            if not self.generation_failed and write_to_file:
                self.window.notebook_top.log_tab.log_frame_text.insert_line("HDL was generated: " + module_name + "\n",  state_after_insert="disabled")
            else:
                self.generation_failed = False # Reset the flag when it was set to True.
        else:
            self.window.notebook_top.log_tab.log_frame_text.insert_line("HDL is up to date: " + module_name + "\n", state_after_insert="disabled")

    def __generate_hdl_for_all_symbols_in_this_schematic(self, window, root, opened_designs_list, force, write_to_file):
        symbol_definitions = window.design.get_symbol_definitions()
        for symbol_definition in symbol_definitions:
            if symbol_definition["filename"].endswith(".hse"):
                if symbol_definition["entity_name"]["name"]!=window.design.get_module_name(): # Break generation loop at recursive instantiations.
                    self.__generate_hdl_for_hse_symbol(root, symbol_definition, opened_designs_list, force, write_to_file)
            elif symbol_definition["filename"].endswith(".hfe") and write_to_file:
                self.__generate_hdl_for_hfe_symbol(window, symbol_definition, force)

    def __generate_hdl_for_hse_symbol(self, root, symbol_definition, opened_designs_list, force, write_to_file):
        sub_window = None
        for opened_window in schematic_window.SchematicWindow.open_window_dict:
            if opened_window.design.get_path_name()==symbol_definition["filename"]:
                sub_window = opened_window
                # The method __generate_hdl_for_hse_symbol is called also when schematic_window.__restore_to_version_before_changes is called.
                # In this case no HDL is generated but only the link-dictionary is filled and therefore write_to_file=False.
                # FileWrite is needed, when HDL is generated, so that all submodules are also saved.
                # But when filling the link-dictionary, the sub-modules are not allowed to be written, because it is not
                # clear if the changes shall be kept.
                if sub_window.title().endswith("*") and write_to_file:
                    file_write.FileWrite(sub_window, sub_window.design, "save") # Write to guarantee consistency between source and HDL.
        if not sub_window: # will happen when link-dictionary is filled the first time.
            architecture_name = symbol_definition["architecture_name"]
            sub_window = schematic_window.SchematicWindow.open_subwindow(root, symbol_definition["filename"], architecture_name)
        sub_module_name = sub_window.design.get_module_name()
        if sub_module_name!="":
            # File Read was a success, so HDL can be generated:
            if sub_module_name not in opened_designs_list: # Continue only if no recursive loop exists.
                opened_designs_list.append(sub_module_name)
                self.__generate_for_window(root, sub_window, opened_designs_list, force, write_to_file, top=False)

    def __generate_hdl_for_hfe_symbol(self, window, symbol_definition, force):
        # Update parameters which might have been changed since instantiation of the symbol:
        try:
            fileobject = open(symbol_definition["filename"], 'r', encoding="utf-8")
            data_read = fileobject.read()
            fileobject.close()
            hdl_fsm_editor_design_dictionary_sub = json.loads(data_read)
            generate_path_value_of_fsm = hdl_fsm_editor_design_dictionary_sub["generate_path"]
            number_of_files_of_fsm     = hdl_fsm_editor_design_dictionary_sub["number_of_files"]
        except FileNotFoundError:
            messagebox.showerror("Warning", "File " + symbol_definition["filename"] + " could not be found.\nCheck if HDL already exists may fail.")
            generate_path_value_of_fsm = symbol_definition["generate_path_value"]
            number_of_files_of_fsm     = symbol_definition["number_of_files"]
        if symbol_definition["language"]=="VHDL":
            if number_of_files_of_fsm==1:
                hdlfilename = generate_path_value_of_fsm + "/" + symbol_definition["entity_name"]["name"] + ".vhd"
            else:
                hdlfilename = generate_path_value_of_fsm + "/" + symbol_definition["entity_name"]["name"] + "_e.vhd"
        else:
            hdlfilename = generate_path_value_of_fsm + "/" + symbol_definition["entity_name"]["name"] + ".v"
        path_name = symbol_definition["filename"]
        if (force or
            hdl_generate_functions.HdlGenerateFunctions.hdl_must_be_generated(path_name, hdlfilename, hdlfilename_architecture=None, show_message=False) or
            window.title().endswith("*")
            ):
            command_array = [self.window.design.get_hfe_cmd(), "-generate_hdl", "-no_version_check", "-no_message", path_name]
            try:
                process = subprocess.Popen(command_array,
                                            text=True, # Decoding is done by Popen.
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT)
                for line in process.stdout: # Terminates when process.stdout is closed.
                    if line!="\n": # VHDL report-statements cause empty lines which mess up the protocol.
                        #print("line =", line)
                        self.window.notebook_top.log_tab.log_frame_text.insert_line(line, state_after_insert="disabled")
            except FileNotFoundError:
                command_string = ""
                for word in command_array:
                    command_string += word + " "
                messagebox.showerror("Error in HDL-SCHEM-Editor", "FileNotFoundError caused by compile command:\n" + command_string)
                return
            except PermissionError:
                command_string = ""
                for word in command_array:
                    command_string += word + " "
                messagebox.showerror("Error in HDL-SCHEM-Editor", "PermissionError caused by compile command:\n" + command_string)
                return
            self.window.notebook_top.log_tab.log_frame_text.insert_line(
                "HDL was generated: " + symbol_definition["entity_name"]["name"] + "\n",  state_after_insert="disabled")
        else:
            self.window.notebook_top.log_tab.log_frame_text.insert_line(
                "HDL is up to date: " + symbol_definition["entity_name"]["name"] + "\n", state_after_insert="disabled")
