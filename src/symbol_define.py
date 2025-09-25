"""
This class tries to read the HDL file.
The read file is parsed and the information found is copied into an symbol insertion object.
The reference to the symbol insertion object can be asked by get_symbol_insertion_ref().
"""
from   tkinter import messagebox
import json
import os
import re
import vhdl_parsing
import verilog_parsing
import symbol_insertion
import list_separation_check

class SymbolDefine():
    def __init__(self, root, window, diagram_tab, filename):
        try:
            self.symbol_insertion_ref = None
            file_to_read = filename
            if os.path.isfile(filename + ".tmp"):
                answer = messagebox.askyesno("HDL-SCHEM-Editor",
                                            "Found BackUp-File\n" +
                                             filename + ".tmp\n" +
                                            "This file contains all not saved changes.\n" +
                                            "Shall it be read instead of\n"+
                                             filename + "?\n"
                                            )
                if answer:
                    file_to_read = filename + ".tmp"
            fileobject = open(file_to_read, 'r', encoding="utf-8")
            data_read = fileobject.read()
            fileobject.close()
            if filename.endswith(".vhd"):
                language_of_instance = "VHDL"
                module_library     = ""
                additional_sources = []
                name_of_dir, _     = os.path.split(filename)
                generate_path_value= name_of_dir
                hdl_parsed         = vhdl_parsing.VhdlParser(data_read, "entity_context")
                library_names      = hdl_parsed.get("entity_library_name")
                package_names      = hdl_parsed.get("package_name")
                entity_name        = hdl_parsed.get("entity_name")
                architecture_name  = hdl_parsed.get("architecture_name")
                if architecture_name=="":
                    number_of_files = 2
                else:
                    number_of_files = 1
                architecture_list  = []
                port_names         = hdl_parsed.get("port_interface_names")
                port_direction     = hdl_parsed.get("port_interface_direction")
                port_types         = hdl_parsed.get("port_interface_types")
                port_ranges        = hdl_parsed.get("port_interface_ranges")
                port_constraints   = hdl_parsed.get("port_interface_constraints")
                generic_definition = hdl_parsed.get("generic_definition")
                generic_types      = hdl_parsed.get("generics_interface_types")
            elif filename.endswith(".hse"):
                hdl_schem_editor_design_dictionary = json.loads(data_read)
                if "active__architecture" in hdl_schem_editor_design_dictionary:
                    architecture_list = list(hdl_schem_editor_design_dictionary.keys())
                    architecture_list.remove("active__architecture")
                    hdl_schem_editor_design_dictionary = hdl_schem_editor_design_dictionary[hdl_schem_editor_design_dictionary["active__architecture"]]
                else:
                    architecture_list = []
                language_of_instance = hdl_schem_editor_design_dictionary["language"]
                generate_path_value  = hdl_schem_editor_design_dictionary["generate_path_value"]
                number_of_files      = hdl_schem_editor_design_dictionary["number_of_files"]
                module_library       = hdl_schem_editor_design_dictionary["module_library"]
                additional_sources   = hdl_schem_editor_design_dictionary["additional_sources"].split(',') # Conversion from comma-separated string into list
                port_list            = hdl_schem_editor_design_dictionary["port_declarations"]
                if language_of_instance=="VHDL":
                    interface_package_parsed  = vhdl_parsing.VhdlParser(
                                                window.design.get_interface_packages_from_design_dictionary(hdl_schem_editor_design_dictionary),
                                                "entity_context")
                    entity_dummy = "entity dummy is port("
                    for port in port_list:
                        port = re.sub(r"--.*", "", port) # Remove any comment, before ';' is added
                        entity_dummy += port + ';'
                    entity_dummy = entity_dummy[:-1] + "); end entity;"
                    interface_ports_parsed    = vhdl_parsing.VhdlParser(entity_dummy, "entity_context")
                    interface_generics_parsed = vhdl_parsing.VhdlParser(window.design.get_generics_from_design_dictionary(hdl_schem_editor_design_dictionary), "generics")
                    library_names      = interface_package_parsed.get("entity_library_name")
                    package_names      = interface_package_parsed.get("package_name")
                    entity_name        = hdl_schem_editor_design_dictionary["module_name"]
                    if "architecture_name" in hdl_schem_editor_design_dictionary:
                        architecture_name = hdl_schem_editor_design_dictionary["architecture_name"]
                    else: # Old versions of HDL-SCHEM-Editor do not support different architecture names.
                        architecture_name = "struct"
                    if not architecture_list:
                        architecture_list = [architecture_name]
                    port_names         = interface_ports_parsed.get("port_interface_names")
                    port_direction     = interface_ports_parsed.get("port_interface_direction")
                    port_types         = interface_ports_parsed.get("port_interface_types")
                    port_ranges        = interface_ports_parsed.get("port_interface_ranges")
                    port_constraints   = interface_ports_parsed.get("port_interface_constraints")
                    generic_definition = interface_generics_parsed.get("generic_definition")
                    generic_types      = interface_generics_parsed.get("generics_interface_types")
                else: # Verilog
                    module_dummy = "module dummy ("
                    for port in port_list:
                        port = re.sub(r"//.*", "", port) # Remove any comment, before ';' is added
                        module_dummy += port + ','
                    module_dummy = module_dummy[:-1] + ");"
                    interface_ports_parsed    = verilog_parsing.VerilogParser(module_dummy, "module")
                    interface_generics_parsed = verilog_parsing.VerilogParser(window.design.get_generics_from_design_dictionary(hdl_schem_editor_design_dictionary),
                                                                              "parameter_list")
                    library_names      = ""
                    package_names      = ""
                    entity_name        = hdl_schem_editor_design_dictionary["module_name"]
                    architecture_name  = ""
                    architecture_list  = []
                    port_names         = interface_ports_parsed   .get("port_interface_names")
                    port_direction     = interface_ports_parsed   .get("port_interface_direction")
                    port_types         = interface_ports_parsed   .get("port_interface_types")
                    port_ranges        = interface_ports_parsed   .get("port_interface_ranges")
                    port_constraints   = interface_ports_parsed   .get("port_interface_constraints")
                    generic_definition = interface_generics_parsed.get("parameter_definition")
                    generic_types      = []
            elif filename.endswith(".hfe"):
                try: # "try" is needed because an old file hfe-format exists.
                    hdl_fsm_editor_design_dictionary = json.loads(data_read)
                    language_of_instance = hdl_fsm_editor_design_dictionary["language"]
                    generate_path_value  = hdl_fsm_editor_design_dictionary["generate_path"]
                    number_of_files      = hdl_fsm_editor_design_dictionary["number_of_files"]
                    module_library       = ""
                    if "additional_sources" in hdl_fsm_editor_design_dictionary:
                        additional_sources = hdl_fsm_editor_design_dictionary["additional_sources"].split(',')
                    if language_of_instance=="VHDL":
                        interface_package_parsed  = vhdl_parsing.VhdlParser(hdl_fsm_editor_design_dictionary["interface_package" ], "entity_context")
                        interface_ports_parsed    = vhdl_parsing.VhdlParser(hdl_fsm_editor_design_dictionary["interface_ports"   ], "ports")
                        interface_generics_parsed = vhdl_parsing.VhdlParser(hdl_fsm_editor_design_dictionary["interface_generics"], "generics")
                        library_names      = interface_package_parsed.get("entity_library_name")
                        package_names      = interface_package_parsed.get("package_name")
                        entity_name        = hdl_fsm_editor_design_dictionary["modulename"]
                        architecture_name  = "fsm"
                        architecture_list  = []
                        port_names         = interface_ports_parsed.get("port_interface_names")
                        port_direction     = interface_ports_parsed.get("port_interface_direction")
                        port_types         = interface_ports_parsed.get("port_interface_types")
                        port_ranges        = interface_ports_parsed.get("port_interface_ranges")
                        port_constraints   = interface_ports_parsed.get("port_interface_constraints")
                        generic_definition = interface_generics_parsed.get("generic_definition")
                        generic_types      = interface_generics_parsed.get("generics_interface_types")
                    else: # Verilog
                        interface_ports_parsed    = verilog_parsing.VerilogParser(hdl_fsm_editor_design_dictionary["interface_ports"   ], "port_region")
                        interface_generics_parsed = verilog_parsing.VerilogParser(hdl_fsm_editor_design_dictionary["interface_generics"], "parameter_list")
                        library_names      = ""
                        package_names      = ""
                        entity_name        = hdl_fsm_editor_design_dictionary["modulename"]
                        architecture_name  = ""
                        architecture_list  = []
                        port_names         = interface_ports_parsed.get("port_interface_names")
                        port_direction     = interface_ports_parsed.get("port_interface_direction")
                        port_types         = interface_ports_parsed.get("port_interface_types")
                        port_ranges        = interface_ports_parsed.get("port_interface_ranges")
                        port_constraints   = ["" for _ in port_ranges]
                        generic_definition = interface_generics_parsed.get("parameter_definition")
                        generic_types      = []
                    generic_definition = list_separation_check.ListSeparationCheck(generic_definition, language_of_instance).get_fixed_list()
                except json.JSONDecodeError:
                    messagebox.showerror("Error in HDL-SCHEM-Editor", "File " + filename + " is not a .hfe file in JSON format.")
                    return
            elif filename.endswith(".v"):
                language_of_instance = "Verilog"
                #generate_path_value  = filename[:-2]
                name_of_dir, _       = os.path.split(filename)
                generate_path_value  = name_of_dir
                number_of_files      = 1
                module_library       = ""
                additional_sources   = []
                hdl_parsed           = verilog_parsing.VerilogParser(data_read, "module")
                library_names        = ""
                package_names        = ""
                entity_name          = hdl_parsed.get("entity_name")
                architecture_name    = "struct" # default name for Verilog designs
                architecture_list    = []
                port_names           = hdl_parsed.get("port_interface_names")
                port_direction       = hdl_parsed.get("port_interface_direction")
                port_types           = hdl_parsed.get("port_interface_types")
                port_ranges          = hdl_parsed.get("port_interface_ranges")
                port_constraints     = ["" for _ in port_ranges]
                generic_definition   = hdl_parsed.get("parameter_definition")
            elif filename.endswith(".sv"):
                language_of_instance = "SystemVerilog"
                #generate_path_value  = filename[:-2]
                name_of_dir, _       = os.path.split(filename)
                generate_path_value  = name_of_dir
                number_of_files      = 1
                module_library       = ""
                additional_sources   = []
                hdl_parsed           = verilog_parsing.VerilogParser(data_read, "module")
                library_names        = ""
                package_names        = ""
                entity_name          = hdl_parsed.get("entity_name")
                architecture_name    = "struct" # default name for Verilog designs
                architecture_list    = []
                port_names           = hdl_parsed.get("port_interface_names")
                port_direction       = hdl_parsed.get("port_interface_direction")
                port_types           = hdl_parsed.get("port_interface_types")
                port_ranges          = hdl_parsed.get("port_interface_ranges")
                port_constraints     = ["" for _ in port_ranges]
                generic_definition   = hdl_parsed.get("parameter_definition")
            else:
                messagebox.showerror("Error in HDL-SCHEM-Editor", "No parser found for this file: " + filename)
                return
            old_language_of_entity = window.design.get_stored_language_of_entity(entity_name)
            if old_language_of_entity is not None:
                if language_of_instance!=old_language_of_entity:
                    messagebox.showerror("Error in HDL-SCHEM-Editor", "It is not allowed to insert the same module\ndescribed in 2 different languages.\nModule " +
                                         entity_name + " is already instantiated as a " +
                                         old_language_of_entity + " module\nand now you want to instantiate it as a " +
                                         language_of_instance + " module.")
                    return
            if window.design.get_language()!="VHDL": # "Verilog", "SystemVerilog"
                if language_of_instance=="VHDL":
                    for generic_type in generic_types:
                        if generic_type!="integer":
                            messagebox.showerror("Error in HDL-SCHEM-Editor", "The VHDL module " + entity_name + " has a generic with type " + generic_type + ".\n" +
                                                 "But only the type integer is allowed, when a module is instantiated in a not VHDL design.")
                            return
            self.symbol_insertion_ref = symbol_insertion.SymbolInsertion(root, window, diagram_tab)
            self.symbol_insertion_ref.set_language           (language_of_instance)
            self.symbol_insertion_ref.set_number_of_files    (number_of_files)
            self.symbol_insertion_ref.add_file_name          (filename)
            self.symbol_insertion_ref.add_generate_path_value(generate_path_value)
            self.symbol_insertion_ref.add_library_names      (library_names)
            self.symbol_insertion_ref.add_package_names      (package_names)
            self.symbol_insertion_ref.add_entity_name_name   (entity_name)
            self.symbol_insertion_ref.add_architecture_name  (architecture_name)
            self.symbol_insertion_ref.add_architecture_list  (architecture_list)
            self.symbol_insertion_ref.add_generic_definition (generic_definition)
            if module_library!="":
                self.symbol_insertion_ref.add_module_library(module_library)
            self.symbol_insertion_ref.add_additional_sources(additional_sources)
            if language_of_instance=="VHDL":
                for index, name in enumerate(port_names):
                    port_declaration = name + " : " + port_direction[index] + " " + port_types[index] + " " + port_ranges[index] + " " + port_constraints[index]
                    self.symbol_insertion_ref.add_port(port_declaration)
            else: # language_of_instance in ["Verilog", "SystemVerilog"]
                for index, name in enumerate(port_names):
                    port_direction_comment = ""
                    if window.design.get_language()=="VHDL" and port_ranges[index]!="":
                        port_range = re.sub(r".*\[(.*)\].*", r"\1", port_ranges[index])
                        bounds = port_range.split(":")
                        if bounds[0].isnumeric() and bounds[1].isnumeric():
                            port_direction_comment = ''
                        else:
                            answer = messagebox.askquestion("HDL-Schem-Editor:",
                                                            'Shall at instance ' + entity_name + ' at the port\n"' + 
                                                            port_direction[index] + ' ' + port_types[index] + ' ' + port_ranges[index] + ' ' + name +
                                                            '"\nthe range-descriptor "to" instead of "downto" be used?',
                                                            default="no")
                            if answer=="yes":
                                port_direction_comment = "//HDL-SCHEM-Editor:to"
                            else:
                                port_direction_comment = "//HDL-SCHEM-Editor:downto"
                    port_declaration = port_direction[index] + ' ' + port_types[index] + ' ' + port_ranges[index] + ' ' + name + port_direction_comment
                    self.symbol_insertion_ref.add_port(port_declaration)
        except FileNotFoundError:
            messagebox.showerror("Error in HDL-SCHEM-Editor", "File " + filename + " could not be found by SymbolDefine.")
    def get_symbol_insertion_ref(self): # Will be called by symbol_reading, symbol_update_infos/ports.
        return self.symbol_insertion_ref
