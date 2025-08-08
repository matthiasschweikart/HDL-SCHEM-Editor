"""
Generates the VHDL-Architecture
"""
import re
from tkinter import messagebox
import hdl_generate_functions
import link_dictionary

class GenerateArchitecture():
    def __init__(self,
                 design, #   : design_data.DesignData,
                 architecture_name,
                 signal_declarations, instance_connection_definitions, block_list,
                 component_declarations_dict, embedded_configurations, libraries_from_instance_configuration,
                 generic_mapping_dict, sorted_canvas_ids_for_hdl,
                 generate_dictionary, file_name, start_line_number_of_architecture):
        self.design = design
        self.file_line_number = start_line_number_of_architecture
        # Die Blöcke haben canvas_ids des Textes als key und VHDL-Text als Value.
        # Die Generates haben die rectangle-canvas-id als key und eine VHDL-Condition als Value.
        # Die Instanzen haben die Canvas-ID des rectangle als key in hdl_dict und den Instanz-HDL-Code als Value.
        hdl_dict = {}
        for canvas_id, hdl_text in block_list.items():
            hdl_dict[canvas_id] = {"type": "block", "hdl_text": hdl_text}
        for canvas_id, hdl_text in generate_dictionary.items():
            hdl_dict[canvas_id] = {"type": "generate", "hdl_text": hdl_text}
        instance_definitions = self.__get_instance_definitions(instance_connection_definitions, component_declarations_dict, generic_mapping_dict)
        for canvas_id, hdl_text in instance_definitions.items():
            hdl_dict[canvas_id] = {"type": "instance", "hdl_text": hdl_text}
        configurations_in_generates = self.__find_configurations_in_generates(sorted_canvas_ids_for_hdl)
        embedded_configurations_reduced = []
        for embedded_configuration in embedded_configurations:
            if embedded_configuration.strip() not in configurations_in_generates:
                embedded_configurations_reduced.append(embedded_configuration)
        self.architecture  = self.__add_packages(file_name)
        self.architecture += self.__add_libraries_from_embedded_configurations(embedded_configurations, file_name)
        self.architecture += self.__add_libraries_from_instance_configurations(libraries_from_instance_configuration, file_name)
        self.architecture += "architecture " + architecture_name + " of " + self.design.get_module_name() + " is\n"
        self.file_line_number += 1
        self.architecture += self.__add_first_declarations(file_name)
        self.architecture += self.__add_signal_declarations(signal_declarations, file_name)
        self.architecture += self.__add_last_declarations(file_name)
        self.architecture += self.__add_component_definitions(component_declarations_dict)
        self.architecture += self.__add_embedded_configurations(embedded_configurations_reduced, file_name)
        self.architecture += "begin\n"
        self.file_line_number += 1
        self.architecture += self.__add_schematic_elements(sorted_canvas_ids_for_hdl, hdl_dict, generate_dictionary, file_name)
        self.architecture += "end architecture;\n"

    def get_architecture(self):
        return self.architecture

    def __add_packages(self, file_name):
        text_dictionary = self.design.get_text_dictionary()
        if (    text_dictionary["internals_packages"]     and
                text_dictionary["internals_packages"]!="" and
            not text_dictionary["internals_packages"].isspace()
            ):
            internals_packages = text_dictionary["internals_packages"]
            if internals_packages[-1]!="\n":
                internals_packages += "\n"
            number_of_new_lines = internals_packages.count("\n")
            link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                   "internals_packages", number_of_new_lines, "", "")
            self.file_line_number += number_of_new_lines
            return internals_packages
        return ""

    def __add_libraries_from_embedded_configurations(self, embedded_configurations, file_name):
        library_list = []
        for embedded_configuration in embedded_configurations:
            if embedded_configuration!="":
                library = re.sub(r".* use entity ", "", embedded_configuration)
                library = re.sub(r"\..*\n", "", library)
                instance_name = re.sub(r"^\s*for\s+", "", embedded_configuration)
                instance_name = re.sub(r"\s*:.*\n"  , "", instance_name)
                if library not in library_list:
                    library_list.append(library)
        embedded_library_instructions = ""
        for library in library_list:
            embedded_library_instructions += "library " + library + ";\n"
            link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                   "embedded_library_instruction", 1, instance_name, "")
            self.file_line_number += 1
        return embedded_library_instructions

    def __add_libraries_from_instance_configurations(self, libraries_from_instance_configuration, file_name):
        library_instructions = ""
        list_of_libraries = []
        for library in libraries_from_instance_configuration:
            instance_name = library[0]
            library_name  = library[1]
            if library_name not in list_of_libraries:
                list_of_libraries.append(library_name)
                library_instructions += "library " + library_name + ";\n"
                link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                    "embedded_library_instruction", 1, instance_name, "")
                self.file_line_number += 1
        return library_instructions

    def __add_first_declarations(self, file_name):
        text_dictionary = self.design.get_text_dictionary()
        if (    text_dictionary["architecture_first_declarations"]     and
                text_dictionary["architecture_first_declarations"]!="" and
            not text_dictionary["architecture_first_declarations"].isspace()):
            architecture_declarations = text_dictionary["architecture_first_declarations"]
            architecture_declarations = re.sub("^([^\\n])", " "*4 + "\\1", architecture_declarations, flags=re.MULTILINE) # Add 4 blanks at the line start of a not empty line.
            if architecture_declarations[-1]!="\n":
                architecture_declarations += "\n"
            number_of_new_lines = architecture_declarations.count("\n")
            link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                   "first_declarations", number_of_new_lines, "", "")
            self.file_line_number += number_of_new_lines
            return architecture_declarations
        return ""

    def __add_signal_declarations(self, signal_declarations, file_name):
        signal_declarations = hdl_generate_functions.HdlGenerateFunctions.indent_identically(':', signal_declarations)
        signal_declarations = sorted(set(signal_declarations))
        for signal_declaration in signal_declarations:
            signal_declaration = re.sub(r"^\s*", "", signal_declaration)
            signal_name, _, _, _, _, _ = hdl_generate_functions.HdlGenerateFunctions.split_declaration(signal_declaration, "VHDL")
            link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                   "signal_declaration", 1, signal_name, "")
            self.file_line_number += 1
        signal_declarations = self.__add_signal_identifier_and_semicolon_and_return(signal_declarations)
        signal_declarations_text = ""
        for signal_declaration in signal_declarations:
            signal_declarations_text += signal_declaration
        return signal_declarations_text

    def __add_signal_identifier_and_semicolon_and_return(self,  signal_declarations):
        signal_declarations_text_list = []
        for signal_declaration in signal_declarations:
            if   " --" in signal_declaration:
                signal_declaration = re.sub(r" --", r"; --", signal_declaration)
            elif "--"  in signal_declaration:
                signal_declaration = re.sub(r"--" , r"; --", signal_declaration)
            else:
                signal_declaration = signal_declaration + ";"
            signal_declarations_text_list.append(" "*4 + "signal " + signal_declaration + "\n")
        return signal_declarations_text_list

    def __add_last_declarations(self, file_name):
        text_dictionary = self.design.get_text_dictionary()
        if (    text_dictionary["architecture_last_declarations"]     and
                text_dictionary["architecture_last_declarations"]!="" and
            not text_dictionary["architecture_last_declarations"].isspace()):
            architecture_declarations = text_dictionary["architecture_last_declarations"]
            architecture_declarations = re.sub("^([^\\n])", " "*4 + "\\1", architecture_declarations, flags=re.MULTILINE) # Add 4 blanks at the line start of a not empty line.
            if architecture_declarations[-1]!="\n":
                architecture_declarations += "\n"
            number_of_new_lines = architecture_declarations.count("\n")
            link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                   "last_declarations", number_of_new_lines, "", "")
            self.file_line_number += number_of_new_lines
            return architecture_declarations
        return ""

    def __add_component_definitions(self, component_declarations_dict):
        self.__translate_component_declarations_dict_into_vhdl(component_declarations_dict)
        component_definitions = self.__get_component_definitions(component_declarations_dict)
        self.file_line_number += component_definitions.count("\n")
        return component_definitions

    def __add_embedded_configurations(self, embedded_configurations, file_name):
        embedded_confs = ""
        for embedded_configuration in embedded_configurations:
            if embedded_configuration!="":
                embedded_confs += embedded_configuration
                instance_name = re.sub(r"^\s*for\s+", "", embedded_configuration)
                instance_name = re.sub(r"\s*:.*\n"  , "", instance_name)
                link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                    "embedded_library_instruction", 1, instance_name, "")
                self.file_line_number += 1
        return embedded_confs

    def __add_schematic_elements(self, sorted_canvas_ids_for_hdl, hdl_dict, generate_dictionary, file_name):
        schematic_elements = ""
        indent = 4
        generate_line_for_print = ""
        for canvas_id_for_hdl in sorted_canvas_ids_for_hdl:
            if canvas_id_for_hdl in hdl_dict: # Filters symbols without connected wires (they have a canvas ID but are not part of hdl_dict).
                hdl_text = hdl_dict[canvas_id_for_hdl]["hdl_text"]
                hdl_type = hdl_dict[canvas_id_for_hdl]["type"]
                hdl_text = re.sub(r"^\s*--\s*[0-9]+\s*\n"    , ""   , hdl_text) # Remove the first line if it is a priority information comment line.
                if hdl_type=="generate":
                    generate_line_for_print = hdl_text
                    hdl_text = re.sub(r"([^^]\s*--)\s*[0-9]+", r"\1", hdl_text) # Remove priority-comment, but leave rest of comment.
                    hdl_text = re.sub(r"([^^])\s*--\s*$"     , r"\1", hdl_text) # Remove remaining empty comment.
                else:
                    hdl_text = re.sub(r"([^^])\s*--\s*[0-9]+\s*$", r"\1", hdl_text, flags=re.MULTILINE) # Remove priority-comments at line end (from blocks or from instance-names).
                hdl_text = re.sub(r"^", ' '*indent, hdl_text, flags=re.MULTILINE) # Indent accordingly.
                if hdl_text[-1]!="\n":
                    hdl_text += "\n"
                schematic_elements += hdl_text
                if canvas_id_for_hdl in generate_dictionary:
                    indent += 4
                self.__fill_link_dictionary(hdl_text, file_name, canvas_id_for_hdl, hdl_dict[canvas_id_for_hdl]["type"])
            elif isinstance(canvas_id_for_hdl, str) and canvas_id_for_hdl.startswith("begin-generate"):  # The string "begin-generate ..." is an entry of sorted_canvas_ids_for_hdl.
                string_enclosed_canvas_ids = re.sub(r"begin-generate ", "", canvas_id_for_hdl)
                if not string_enclosed_canvas_ids:
                    messagebox.showwarning("HDl_SCHEM-Editor", "There is an empty generate frame for this generate:\n" + generate_line_for_print + "\nSee file: " + file_name)
                list_of_enclosed_canvas_id_strings = string_enclosed_canvas_ids.split()
                configuration = ""
                for canvas_id_string in list_of_enclosed_canvas_id_strings:
                    type_of_canvas_id = self.design.get_schematic_element_type_of(int(canvas_id_string))
                    if type_of_canvas_id=="instance":
                        symbol_definition_of_canvas_id = self.design.get_symbol_definition_of(int(canvas_id_string))
                        if symbol_definition_of_canvas_id["configuration"]["config_statement"]=="Embedded":
                            configuration += ' '*indent + "for "
                            configuration += symbol_definition_of_canvas_id["instance_name"]["name"]
                            configuration += " : "
                            configuration += symbol_definition_of_canvas_id["entity_name"]["name"]
                            configuration += " use entity "
                            configuration += symbol_definition_of_canvas_id["configuration"]["library"]
                            configuration += '.'
                            configuration += symbol_definition_of_canvas_id["entity_name"]["name"]
                            configuration += '('
                            configuration += symbol_definition_of_canvas_id["architecture_name"]
                            configuration += ");\n"
                            link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                   "embedded_library_instruction", 1, symbol_definition_of_canvas_id["instance_name"]["name"], "")
                            self.file_line_number += 1
                if configuration!="":
                    indent -= 4
                    configuration += ' '*indent + "begin\n"
                    self.file_line_number += 1
                    schematic_elements += configuration
                    indent += 4
            elif isinstance(canvas_id_for_hdl, str) and canvas_id_for_hdl.startswith("end generate"):  # The string "end generate ..." is an entry of sorted_canvas_ids_for_hdl.
                indent -= 4
                generate_condition = hdl_dict[int(canvas_id_for_hdl.split()[2])]["hdl_text"]
                generate_condition_without_comment = re.sub(r"--.*", "", generate_condition)
                generate_label = re.sub(r":.*", "", generate_condition_without_comment)
                if generate_label!=generate_condition_without_comment:
                    schematic_elements += ' '*indent + "end generate " + generate_label + ";\n"
                else:
                    schematic_elements += ' '*indent + "end generate;\n"
                self.file_line_number += 1
        return schematic_elements

    def __find_configurations_in_generates(self, sorted_canvas_ids_for_hdl):
        configurations = ""
        for canvas_id_for_hdl in sorted_canvas_ids_for_hdl:
            if isinstance(canvas_id_for_hdl, str) and canvas_id_for_hdl.startswith("begin-generate"):  # The string "begin-generate ..." is an entry of sorted_canvas_ids_for_hdl.
                string_enclosed_canvas_ids = re.sub(r"begin-generate ", "", canvas_id_for_hdl)
                list_of_enclosed_canvas_id_strings = string_enclosed_canvas_ids.split()
                configuration = ""
                for canvas_id_string in list_of_enclosed_canvas_id_strings:
                    type_of_canvas_id = self.design.get_schematic_element_type_of(int(canvas_id_string))
                    if type_of_canvas_id=="instance":
                        symbol_definition_of_canvas_id = self.design.get_symbol_definition_of(int(canvas_id_string))
                        if symbol_definition_of_canvas_id["configuration"]["config_statement"]=="Embedded":
                            configuration += "for "
                            configuration += symbol_definition_of_canvas_id["instance_name"]["name"]
                            configuration += " : "
                            configuration += symbol_definition_of_canvas_id["entity_name"]["name"]
                            configuration += " use entity "
                            configuration += symbol_definition_of_canvas_id["configuration"]["library"]
                            configuration += '.'
                            configuration += symbol_definition_of_canvas_id["entity_name"]["name"]
                            configuration += '('
                            configuration += symbol_definition_of_canvas_id["architecture_name"]
                            configuration += ");\n"
                configurations += configuration
        return configurations

    def __strip_list_from_comments_at_end_of_line_and_trailing_blanks(self, hdl_text_list):
        hdl_text_list_stripped = []
        for hdl_line in hdl_text_list:
            hdl_line = re.sub(r"--.*", "", hdl_line)
            hdl_line = hdl_line.strip()
            hdl_text_list_stripped.append(hdl_line)
        return hdl_text_list_stripped

    def __fill_link_dictionary(self, hdl_text, file_name, canvas_id_for_hdl, hdl_type):
        # Generate-Anweisung, Block, Instance
        hdl_text_list = hdl_text[:-1].split("\n") # The last "return" of hdl_text is removed before split()
        hdl_text_list_stripped = self.__strip_list_from_comments_at_end_of_line_and_trailing_blanks(hdl_text_list)
        if hdl_type=="generate":
            link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                "generate", 1, canvas_id_for_hdl, "")
            self.file_line_number += 1
        elif hdl_type=="block":
            for index in range(len(hdl_text_list)):
                link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                    "block", 1, canvas_id_for_hdl, index+1)
                self.file_line_number += 1
        else: # "symbol"
            for index, hdl_line in enumerate(hdl_text_list_stripped):
                if index==0:
                    kind_of_line = ""
                    link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                        "instance_name", 1, canvas_id_for_hdl, kind_of_line)
                    self.file_line_number += 1
                elif hdl_line.startswith("generic map"):
                    kind_of_line = "generic_mapping"
                    self.file_line_number += 1
                    local_line_number_in_generic_map = 1
                elif hdl_line==')': # end of generic map
                    kind_of_line = ""
                    self.file_line_number += 1
                elif hdl_line.startswith("port map"):
                    kind_of_line = "port_connection"
                    self.file_line_number += 1
                elif hdl_line==');': # end of port map
                    kind_of_line = ""
                    self.file_line_number += 1
                else:
                    if kind_of_line=="generic_mapping":
                        link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                                "generic_mapping", 1, canvas_id_for_hdl, local_line_number_in_generic_map)
                        local_line_number_in_generic_map     += 1
                    elif kind_of_line=="port_connection":
                        signal_name = re.sub(r".*=>", "", hdl_line)    # Remove port-name and "=>"
                        signal_name = re.sub(r","   , "", signal_name) # Remove ',' at line end
                        signal_name = re.sub(r"\(.*", "", signal_name) # Remove subrange
                        signal_name = signal_name.strip()
                        link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                                "port_connection", 1, canvas_id_for_hdl, signal_name)
                    self.file_line_number += 1

    def __translate_component_declarations_dict_into_vhdl(self, component_declarations_dict):
        for entity_name, declarations in component_declarations_dict.items():
            port_declaration_list, generic_definition, _, language = declarations # _ = insert_component
            # port_declaration_list VHDL    = ['res_i : in  std_logic', 'clk_i : in  std_logic', 'counter_o : out std_logic_vector(g_counter_width-1 downto 0)', ...]
            # port_declaration_list Verilog = ['input   res_i', 'input   clk_i', 'output reg [g_counter_width-1:0] counter_o', ...]
            if language!="VHDL": # "Verilog", "SystemVerilog"
                # Translate into VHDL:
                for index, port_declaration in enumerate(port_declaration_list):
                    if '[' in port_declaration:
                        port_range = re.sub(r".*\[(.*)\].*", r"\1", port_declaration)
                        bounds = port_range.split(":")
                        if bounds[0].isnumeric() and bounds[1].isnumeric():
                            if int(bounds[0])>=int(bounds[1]):
                                port_range_direction = "downto"
                            else:
                                port_range_direction = "to"
                        else:
                            port_range_direction = re.sub(r".*//HDL-SCHEM-Editor:", "", port_declaration)
                            # Attention: the next instruction changes also component_declarations_dict, which is importatnt,
                            # because the comment shall not be visible in VHDL:
                            port_declaration     = re.sub(r"//HDL-SCHEM-Editor:.*", "", port_declaration)
                        port_range = re.sub(r"\s*:\s*", ' '+port_range_direction+' ', port_range)
                    else:
                        port_range = ""
                    if port_range=="":
                        port_type = " std_logic"
                    else:
                        port_type = " std_logic_vector(" + port_range + ')'
                    port_declaration_splitted = port_declaration.split()
                    port_direction = port_declaration_splitted[0]
                    if port_direction=="input":
                        port_direction = "in " # Add 1 blank to indent in the same way as "out".
                    elif port_direction=="output":
                        port_direction = "out"
                    else:
                        port_direction = "inout"
                    port_name = port_declaration_splitted[-1]
                    port_declaration_list[index] = port_name + " : " + port_direction + port_type # Attention: changes component_declarations_dict!
                # Add a type to the Verilog parameter definitions:
                component_declarations_dict[entity_name][1] = re.sub('=', ": integer :=", generic_definition) # Only Verilog integer parameters are supported.

    def __get_component_definitions(self, component_declarations_dict):
        component_definitions = ""
        for entity_name, declarations in component_declarations_dict.items():
            port_declaration_list, generic_definition, insert_component, _ = declarations # _ = language
            if insert_component:
                component_definitions += " "*4 + "component " + entity_name + " is\n"
                if generic_definition!="":
                    component_definitions += " "*8 + "generic (\n"
                    if generic_definition[-1]=="\n":
                        generic_definition = generic_definition[:-1]
                    component_definitions += re.sub(r"(?m)^", " "*12, generic_definition) + "\n" + " "*8 + ");\n"
                if port_declaration_list:
                    component_definitions += " "*8 + "port (\n"
                    port_declaration_list_indented = hdl_generate_functions.HdlGenerateFunctions.indent_identically(":", port_declaration_list)
                    for port_declaration in port_declaration_list_indented:
                        component_definitions += " "*12 + port_declaration + ";\n"
                    component_definitions = component_definitions[:-2] + "\n" + " "*8 + ");\n"
                component_definitions += " "*4 + "end component;\n"
        return component_definitions

    def __get_instance_definitions(self, instance_connection_definitions, component_declarations_dict, generic_mapping_dict):
        unconnected_instance_dict, component_language_dict = self.__create_unconnected_instance_dict(component_declarations_dict)
        instances_dictionary = {}
        instance_connection_dict = self.__create_instance_connection_dict(instance_connection_definitions, component_language_dict)
        # instance_connection_dict = {"Instance-Name": {"entity-name": <string>, "canvas_id": <Canvas-ID of rectangle>,
        #                                                connections": [[<port-name>, <signal-name>, <signal-range>, <port-type>]]},..}
        for instance_name_def, generic_info in generic_mapping_dict.items(): # instance_name_def contains the comment after the instance name
            if instance_name_def not in instance_connection_dict:
                instance_connection_dict[instance_name_def] = {"entity_name": generic_info["entity_name"], "canvas_id": generic_info["canvas_id"], "connections": []}
        #print("instance_connection_dict =", instance_connection_dict)
        for instance_name_def, instance_info in instance_connection_dict.items():
            instance_name = re.sub(r"\s*--.*", "", instance_name_def) # Remove the priority information for order in HDL from the instance name.
            entity_name = instance_info["entity_name"]
            instance_declaration = re.sub("instance-name", instance_name, unconnected_instance_dict[entity_name])
            if component_language_dict[entity_name]=="VHDL":
                generic_mapping = generic_mapping_dict[instance_name_def]["generic_map"]
            else:
                # Translate into VHDL:
                generic_mapping = re.sub("//", "--", generic_mapping_dict[instance_name_def]["generic_map"])
            generic_mapping = re.sub(r"(?m)^", " "*8, generic_mapping)
            instance_declaration = re.sub(r"#generic_definition#",  generic_mapping, instance_declaration)
            for connection in instance_info["connections"]:
                #print("connection =", connection)
                port_name = re.sub(r"//HDL-SCHEM-Editor:.*", "", connection[0])
                instance_declaration = re.sub(r"( " + port_name + " +=> )open", "\\1" + connection[1] + connection[2], instance_declaration)
            #print("instance_declaration =", instance_declaration)
            instances_dictionary[instance_info["canvas_id"]] = instance_declaration
        return instances_dictionary

    def __create_unconnected_instance_dict(self, component_declarations_dict):
        unconnected_instance_dict = {}
        component_language_dict   = {}
        for entity_name, declarations in component_declarations_dict.items():
            component_port_declarations  = declarations[0]
            generic_definition           = declarations[1]
            component_language_dict  [entity_name] = declarations[3]
            unconnected_instance_dict[entity_name] = self.__create_unconnected_instance_declaration(entity_name, component_port_declarations, generic_definition)
        return unconnected_instance_dict, component_language_dict

    def __create_instance_connection_dict(self, instance_connection_definitions, component_language_dict):
        instance_connection_dict = {}
        for instance_connection_definition in instance_connection_definitions:
            instance_name      = instance_connection_definition["instance_name"]
            entity_name        = instance_connection_definition["entity_name"]
            port_declaration   = instance_connection_definition["port_declaration"]
            signal_declaration = instance_connection_definition["declaration"]
            if instance_name not in instance_connection_dict:
                instance_connection_dict[instance_name] = {}
                instance_connection_dict[instance_name]["connections"] = []
                instance_connection_dict[instance_name]["canvas_id"]   = instance_connection_definition["canvas_id"]
            if component_language_dict[entity_name]=="VHDL": # Fehler: funktioniert nicht bei Instanz-Configuration
                port_name = port_declaration.split()[0]
            else:
                port_name = port_declaration.split()[-1]
            port_type   = re.sub(".*: ", "", port_declaration)
            signal_name, sub_range, _, _, _, signal_record_slice = hdl_generate_functions.HdlGenerateFunctions.split_declaration(signal_declaration , self.design.get_language())
            instance_connection_dict[instance_name]["entity_name"] = entity_name
            instance_connection_dict[instance_name]["connections"].append([port_name, signal_name, sub_range+signal_record_slice, port_type])
        return instance_connection_dict

    def __create_unconnected_instance_declaration(self, entity_name, component_port_declarations, generic_definition):
        open_instance  = "instance-name : " + entity_name
        if generic_definition!="":
            open_instance += "\n" + " "*4 + "generic map (\n#generic_definition#\n" + " "*4 + ")"
        component_port_declarations = hdl_generate_functions.HdlGenerateFunctions.indent_identically(':', component_port_declarations)
        if component_port_declarations:
            open_instance += "\n" + " "*4 + "port map (\n"
            for declaration in component_port_declarations:
                port_connection_open = re.sub(r":.*", r"=> open,\n", declaration) # Leave the blanks between name and ':'.
                open_instance += " "*8 + port_connection_open
            open_instance = open_instance[:-2] + "\n    );"
        else:
            open_instance += ';'
        return open_instance
