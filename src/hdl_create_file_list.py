"""
This class generates the file hdl_file_list_<module_name>.txt
"""
import json
import os
from tkinter import messagebox

import hdl_generate_functions

class HdlCreateFileList():
    def __init__(self, parent, window, log_tab):
        self.window        = window
        top_library        = "work"
        self.hdl_file_list = []
        self.hdl_file_list_name = ""
        hdl_schem_editor_design_dictionary = self.window.design.create_design_dictionary_of_active_architecture()
        module_name_list = []
        module_name_list.append(hdl_schem_editor_design_dictionary["module_name"])
        active_architecture = self.window.notebook_top.diagram_tab.architecture_name
        success = self.__create_hdl_file_list_for_this_design(self.hdl_file_list, hdl_schem_editor_design_dictionary, top_library, active_architecture, module_name_list)
        if success:
            self.hdl_file_list = self.__remove_consecutive_lines_with_identical_entries(self.hdl_file_list)
        else:
            parent.run_compile = False
        self.__save_in_file(self.hdl_file_list, log_tab, hdl_schem_editor_design_dictionary["module_name"])

    def get_hdl_file_list(self):
        return self.hdl_file_list_name, self.hdl_file_list

    def __create_hdl_file_list_for_this_design(self, hdl_file_list, hdl_schem_editor_design_dictionary, top_library, active_architecture, module_name_list):
        design_library = self.__determine_design_library(hdl_schem_editor_design_dictionary, top_library)
        symbol_definitions = self.window.design.get_symbol_definitions_from_design_dictionary(hdl_schem_editor_design_dictionary)
        symbol_library = "_dummy_"
        for symbol_definition in symbol_definitions:
            if not symbol_definition["filename"].endswith(".hse"):
                symbol_library = self.__add_lib_entry_for_symbol(hdl_file_list, symbol_definition, symbol_library, design_library)
            sub_module_name = symbol_definition["entity_name"]["name"]
            if sub_module_name not in module_name_list: # Break infinite loop at recursive instantiations.
                module_name_list.append(sub_module_name)
                symbol_library = self.__add_file_entries_for_symbol(hdl_file_list, symbol_definition, symbol_library, design_library, module_name_list)
                if symbol_library is False: # symbol_library can be set to False in self.__add_file_entries_for_symbol() when HDL is not up to date.
                    return False
        if symbol_library!=design_library:
            hdl_file_list.append("lib: " + design_library)
        # additional files
        additional_files_string = hdl_schem_editor_design_dictionary["additional_sources"]
        additional_files_string = additional_files_string.strip()
        if additional_files_string!="":
            additional_files_list   = additional_files_string.split(',')
            additional_files_list   = [entry.strip() for entry in additional_files_list]
            for additional_file in additional_files_list:
                if additional_file not in hdl_file_list:
                    hdl_file_list.append(additional_file)
            if additional_files_list:
                hdl_file_list.append("lib: " + design_library) # neccessary because a hdl-file-list in additional files might have changed the library.
        if hdl_schem_editor_design_dictionary['language']=="VHDL":
            if hdl_schem_editor_design_dictionary['number_of_files']==1:
                filename = hdl_schem_editor_design_dictionary['generate_path_value'] + '/' + hdl_schem_editor_design_dictionary["module_name"] + ".vhd"
                if filename not in hdl_file_list:
                    hdl_file_list.append(filename)
            else:
                filename  = hdl_schem_editor_design_dictionary['generate_path_value'] + '/' + hdl_schem_editor_design_dictionary["module_name"] + "_e.vhd"
                filename2 = hdl_schem_editor_design_dictionary['generate_path_value'] + '/' + hdl_schem_editor_design_dictionary["module_name"] + "_" + active_architecture + ".vhd"
                if filename not in hdl_file_list:
                    hdl_file_list.append(filename)
                if filename2 not in hdl_file_list:
                    hdl_file_list.append(filename2)
        elif hdl_schem_editor_design_dictionary['language']=="Verilog":
            filename = hdl_schem_editor_design_dictionary['generate_path_value'] + '/' + hdl_schem_editor_design_dictionary["module_name"] + ".v"
            hdl_file_list.append(filename)
        else: # SystemVerilog
            filename = hdl_schem_editor_design_dictionary['generate_path_value'] + '/' + hdl_schem_editor_design_dictionary["module_name"] + ".sv"
            if filename not in hdl_file_list:
                hdl_file_list.append(filename)
        return symbol_library

    def __determine_design_library(self, hdl_schem_editor_design_dictionary, top_library):
        design_library = hdl_schem_editor_design_dictionary["module_library"].strip()
        if design_library in ["", "work"]:
            design_library = top_library
        return design_library

    def __add_lib_entry_for_symbol(self, hdl_file_list, symbol_definition, symbol_library, design_library):
        if (len(hdl_file_list)==0 or # There is a first symbol but no entry yet in the hdl-file-list, so in any case a lib-statement is needed.
            symbol_definition["configuration"]["library"]!=symbol_library):
            if symbol_definition["configuration"]["library"] in ["work", ""]:
                symbol_library = design_library
            else:
                symbol_library = symbol_definition["configuration"]["library"]
            hdl_file_list.append("lib: " + symbol_library)
        else:
            # There is already an entry in the hdl-file-list and this symbol uses the same library as the symbol before.
            pass
        return symbol_library

    def __add_file_entries_for_symbol(self, hdl_file_list, symbol_definition, symbol_library, design_library, module_name_list):
        path_name = symbol_definition["filename"]
        if path_name.endswith(".hse"):
            try:
                fileobject = open(path_name, 'r', encoding="utf-8")
                data_read = fileobject.read()
                fileobject.close()
                hdl_schem_editor_design_dictionary_sub = json.loads(data_read)
                if "active__architecture" in hdl_schem_editor_design_dictionary_sub:
                    hdl_schem_editor_design_dictionary_sub = self.__get_design_dict_from_dict_with_several_architectures(symbol_definition["architecture_name"],
                                                                                                                         hdl_schem_editor_design_dictionary_sub)
                if "architecture_name" not in hdl_schem_editor_design_dictionary_sub:
                    active_architecture = "struct" # Old versions of HDL-SCHEM-Editor do not store the architecture name.
                else:
                    active_architecture = hdl_schem_editor_design_dictionary_sub["architecture_name"]
                language           = hdl_schem_editor_design_dictionary_sub["language"           ]
                generate_path_name = hdl_schem_editor_design_dictionary_sub["generate_path_value"]
                module_name        = hdl_schem_editor_design_dictionary_sub["module_name"        ]
                number_of_files    = hdl_schem_editor_design_dictionary_sub["number_of_files"    ]
                language           = hdl_schem_editor_design_dictionary_sub["language"           ]
                if self.__hdl_is_not_up_to_date(path_name, language, generate_path_name, module_name, number_of_files, active_architecture):
                    return False # Error message is generated by __hdl_is_not_up_to_date().
                symbol_library = self.__create_hdl_file_list_for_this_design(hdl_file_list, hdl_schem_editor_design_dictionary_sub,
                                                                             design_library, active_architecture, module_name_list)
            except FileNotFoundError:
                messagebox.showerror("Error in HDL-SCHEM-Editor", "File " + symbol_definition["filename"] + " could not be found. hdl-file-list will be incomplete.")
        elif symbol_definition["filename"].endswith(".hfe"):
            for additional_source_file in symbol_definition["additional_files"]:
                if additional_source_file!="" and not additional_source_file.isspace() and additional_source_file not in hdl_file_list:
                    hdl_file_list.append(additional_source_file)
            try:
                fileobject = open(symbol_definition["filename"], 'r', encoding="utf-8")
                data_read = fileobject.read()
                fileobject.close()
                hdl_fsm_editor_design_dictionary_sub = json.loads(data_read)
                generate_path_value_of_fsm = hdl_fsm_editor_design_dictionary_sub["generate_path"]
            except FileNotFoundError:
                messagebox.showerror("Warning", "File " + symbol_definition["filename"] + " could not be found.\nhdl-file-list may use wrong path for VHDL file.")
                generate_path_value_of_fsm = symbol_definition['generate_path_value']
            if symbol_definition["language"]=="VHDL":
                if symbol_definition['number_of_files']==1:
                    filename = generate_path_value_of_fsm + '/' + symbol_definition['entity_name']["name"] + ".vhd"
                    if filename not in hdl_file_list:
                        hdl_file_list.append(filename)
                else:
                    filename  = generate_path_value_of_fsm + '/' + symbol_definition['entity_name']["name"] + "_e.vhd"
                    filename2 = generate_path_value_of_fsm + '/' + symbol_definition['entity_name']["name"] + "_fsm.vhd"
                    if filename not in hdl_file_list:
                        hdl_file_list.append(filename)
                    if filename2 not in hdl_file_list:
                        hdl_file_list.append(filename2)
            else:
                filename = generate_path_value_of_fsm + '/' + symbol_definition['entity_name']["name"] + ".v"
                if filename not in hdl_file_list:
                    hdl_file_list.append(filename)
        elif (symbol_definition["filename"].endswith(".vhd") or
              symbol_definition["filename"].endswith(".v"  ) or
              symbol_definition["filename"].endswith(".sv" )
                ):
            for additional_source_file in symbol_definition["additional_files"]:
                if additional_source_file!="" and not additional_source_file.isspace() and additional_source_file not in hdl_file_list:
                    hdl_file_list.append(additional_source_file)
            if symbol_definition["filename"] not in hdl_file_list:
                hdl_file_list.append(symbol_definition["filename"])
            if symbol_definition["architecture_filename"]!="" and symbol_definition["architecture_filename"] not in hdl_file_list:
                hdl_file_list.append(symbol_definition["architecture_filename"])
        return symbol_library

    def __hdl_is_not_up_to_date(self, path_name, language, generate_path_name, module_name, number_of_files, architecture_name):
        if language!="VHDL":
            hdlfilename = generate_path_name + '/' + module_name + ".v"
            hdlfilename_architecture = None
        else:
            if number_of_files==1:
                hdlfilename = generate_path_name + '/' + module_name + ".vhd"
                hdlfilename_architecture = None
            else:
                hdlfilename = generate_path_name + '/' + module_name + "_e.vhd"
                hdlfilename_architecture = generate_path_name + '/' + module_name + '_' + architecture_name + ".vhd"
        return hdl_generate_functions.HdlGenerateFunctions.hdl_must_be_generated(path_name, hdlfilename, hdlfilename_architecture, show_message=True)

    def __get_design_dict_from_dict_with_several_architectures(self, architecture_name, hdl_schem_editor_design_dictionary_sub):
        #print("hdl_schem_editor_design_dictionary_sub =", hdl_schem_editor_design_dictionary_sub)
        if architecture_name in hdl_schem_editor_design_dictionary_sub:
            active_architecture = architecture_name
        else:
            for _, database in hdl_schem_editor_design_dictionary_sub.items():
                if "module_name" in database:
                    module_name = database["module_name"]
            active_architecture = hdl_schem_editor_design_dictionary_sub["active__architecture"]
            if architecture_name!="":
                messagebox.showerror("Error at creating the hdl-file-list",
                                    "The data base of module " +  module_name+ " has several architectures (only supported for VHDL).\n" +
                                    'But the architecture "' + architecture_name +
                                    '", specified in the symbol properties of the module ' + hdl_schem_editor_design_dictionary_sub[active_architecture]["module_name"] +
                                    ', could not be found in the database.\n"' + active_architecture + '" is used instead.')
        return hdl_schem_editor_design_dictionary_sub[active_architecture]

    def __remove_consecutive_lines_with_identical_entries(self, hdl_file_list):
        temp = []
        for index, entry in enumerate(hdl_file_list):
            if index==0 or entry!=temp[-1]:
                temp.append(entry)
        return temp

    def __save_in_file(self, hdl_file_list, log_tab, module_name):
        hdl_file_list_name = "hdl_file_list_"+ module_name + ".txt"
        hdl_file_list_string = ""
        for line in hdl_file_list:
            hdl_file_list_string += line + "\n"
        try:
            fileobject = open(hdl_file_list_name, 'w', encoding="utf-8")
            fileobject.write(hdl_file_list_string)
            fileobject.close()
            current_working_directory = os.getcwd() # Current working directory is the directory set in control-tab or the directory, where HSE was started.
            if '/' in current_working_directory:
                current_working_directory += '/'
            else:
                current_working_directory += '\\'
            self.hdl_file_list_name = current_working_directory + hdl_file_list_name
            log_tab.log_frame_text.insert_line("Created          : " + self.hdl_file_list_name + "\n", state_after_insert="disabled")
        except FileNotFoundError:
            messagebox.showerror("Error in HDL-SCHEM-Editor", "File hdl_file_list.txt could not be opened.")
        except PermissionError:
            messagebox.showerror("Error in HDL-SCHEM-Editor", "File hdl_file_list.txt has no write permission.")
