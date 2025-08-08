"""
Generate the content of a Verilog module
"""
from tkinter import messagebox
import re
import hdl_generate_functions
import link_dictionary

class GenerateModuleContent:
    def __init__(self, design, signal_declarations, instance_connection_definitions,
                 block_list, component_declarations_dict, generic_mapping_dict,
                 sorted_canvas_ids_for_hdl, generate_dictionary, file_name, start_line_number_of_content):
        self.design = design
        self.file_line_number = start_line_number_of_content + 2 # Filename comment-line and Header comment-line
        self.module_content = ""
        self.module_content += self.__add_first_declarations(file_name)
        self.module_content += self.__add_signal_declarations(signal_declarations, file_name)
        self.__translate_component_declarations_dict_into_verilog(component_declarations_dict)
        hdl_dict = {}
        instance_definitions = self.__get_instance_definitions(instance_connection_definitions, component_declarations_dict, generic_mapping_dict)
        for canvas_id, hdl_text in block_list.items():
            hdl_dict[canvas_id] = {"type": "block"   , "hdl_text": hdl_text}
        for canvas_id, hdl_text in generate_dictionary.items():
            hdl_dict[canvas_id] = {"type": "generate", "hdl_text": hdl_text}
        for canvas_id, hdl_text in instance_definitions.items():
            hdl_dict[canvas_id] = {"type": "instance", "hdl_text": hdl_text}
        self.module_content += self.__add_schematic_elements(sorted_canvas_ids_for_hdl, hdl_dict, generate_dictionary, file_name)
        self.module_content += "endmodule\n"

    def __add_first_declarations(self, file_name):
        text_dictionary = self.design.get_text_dictionary()
        if (    text_dictionary["architecture_first_declarations"]     and
                text_dictionary["architecture_first_declarations"]!="" and
            not text_dictionary["architecture_first_declarations"].isspace()):
            declarations = text_dictionary["architecture_first_declarations"]
            declarations = re.sub("^([^\\n])", " "*4 + "\\1", declarations, flags=re.MULTILINE) # Add 4 blanks at the line start of a not empty line.
            if declarations[-1]!="\n":
                declarations += "\n"
            number_of_new_lines = declarations.count("\n")
            link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                   "first_declarations", number_of_new_lines, "", "")
            self.file_line_number += number_of_new_lines
            return declarations
        return ""

    def __add_signal_declarations(self, signal_declarations, file_name):
        signal_declarations = sorted(set(signal_declarations)) # Removes also double entries.
        for signal_declaration in signal_declarations:
            signal_declaration = re.sub(r"^\s*", "", signal_declaration)
            signal_name, _, _, _, _, _ = hdl_generate_functions.HdlGenerateFunctions.split_declaration(signal_declaration, "Verilog")
            link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                   "signal_declaration", 1, signal_name, "")
            self.file_line_number += 1
        signal_declarations = self.__add_semicolon_and_return(signal_declarations)
        # signal_declarations_text = ""
        # for signal_declaration in signal_declarations:
        #     signal_declarations_text += signal_declaration
        signal_declarations_text = ''.join(signal_declarations)
        return signal_declarations_text

    def __add_semicolon_and_return(self,  signal_declarations):
        signal_declarations_text_list = []
        for signal_declaration in signal_declarations:
            if   " //" in signal_declaration:
                signal_declaration = re.sub(r" //", r"; //", signal_declaration)
            elif "//"  in signal_declaration:
                signal_declaration = re.sub(r"//" , r"; //", signal_declaration)
            else:
                signal_declaration = signal_declaration + ";"
            signal_declarations_text_list.append(" "*4 + signal_declaration + "\n")
        return signal_declarations_text_list

    def __translate_component_declarations_dict_into_verilog(self, component_declarations_dict):
        for _, declarations in component_declarations_dict.items():
            port_declaration_list, _, _, language = declarations # '_'=generic_definition, '_'=insert_component
            # port_declaration_list VHDL    = ['res_i : in  std_logic', 'clk_i : in  std_logic', 'counter_o : out std_logic_vector(g_counter_width-1 downto 0)', ...]
            # port_declaration_list Verilog = ['input   res_i', 'input   clk_i', 'output reg [g_counter_width-1:0] counter_o', ...]
            if language=="VHDL":
                # Translate into Verilog:
                # The default generics must not be translated, as in Verilog there is no component declaration.
                for index, port_declaration in enumerate(port_declaration_list):
                    port_declaration_without_comment = re.sub(r"--.*", "", port_declaration)
                    port_name = re.sub(r"\s*:.*", "", port_declaration_without_comment)
                    if " in " in port_declaration_without_comment:
                        port_direction = "input "
                    elif " out " in port_declaration_without_comment:
                        port_direction = "output wire "
                    else:
                        port_direction = "inout wire "
                    if '(' in port_declaration_without_comment:
                        port_range = re.sub(r".*\((.*)\).*", r"[\1] ", port_declaration_without_comment)
                        port_range = re.sub(r" downto ", ":", port_range)
                        port_range = re.sub(r" to "    , ":", port_range)
                    else:
                        port_range = ""
                    port_declaration_list[index] = port_direction + port_range + port_name

    def __get_instance_definitions(self, instance_connection_definitions, component_declarations_dict, generic_mapping_dict):
        # The unconnected_instance_dict has an entry for each module, where all ports are left open, which is: "(),"
        unconnected_instance_dict, component_language_dict = self.__create_unconnected_instance_dict(component_declarations_dict)
        instances_dictionary = {}
        instance_connection_dict = self.__create_instance_connection_dict(instance_connection_definitions, component_language_dict)
        # instance_connection_dict = {"Instance-Name": {"entity-name": <string>, "canvas_id": <Canvas-ID of rectangle>,
        #                                                connections": [[<port-name>, <signal-name>, <signal-range>, <port-type>]]},..}
        for instance_name_def, generic_info in generic_mapping_dict.items():
            if instance_name_def not in instance_connection_dict:
                instance_connection_dict[instance_name_def] = {"entity_name": generic_info["entity_name"], "canvas_id": generic_info["canvas_id"], "connections": []}
        for instance_name_def, instance_info in instance_connection_dict.items():
            #print("instance_name, instance_info =", instance_name, instance_info)
            comment_of_instance_name = re.sub(r".*//", " //", instance_name_def)
            if comment_of_instance_name==instance_name_def:
                comment_of_instance_name = ""
            instance_name_without_comment = re.sub(r"\s*//.*", "", instance_name_def)
            entity_name = instance_info["entity_name"]
            instance_declaration = re.sub(r"instance-name \(", instance_name_without_comment + " (" + comment_of_instance_name, unconnected_instance_dict[entity_name])
            if component_language_dict[entity_name]=="VHDL":
                # Translate into Verilog:
                if instance_name_def not in generic_mapping_dict:
                    messagebox.showerror("Error in HDL-SCHEM-Editor", "The instance name " + instance_name_without_comment + " is not found in database. HDL will be corrupted")
                    return {}
                generic_mapping = re.sub(">" , ""  , generic_mapping_dict[instance_name_def]["generic_map"])
                generic_mapping = re.sub("--", "//", generic_mapping)
            else:
                if instance_name_def not in generic_mapping_dict:
                    messagebox.showerror("Error in HDL-SCHEM-Editor", "The instance name " + instance_name_without_comment + " is not found in database. HDL will be corrupted")
                    return {}
                generic_mapping = generic_mapping_dict[instance_name_def]["generic_map"]
            generic_mapping = self.__create_verilog_format(generic_mapping)
            generic_mapping = re.sub(r"(?m)^", "    ", generic_mapping) # indent by 4 blanks
            instance_declaration = re.sub(r"#generic_definition#", r"#(\n" + generic_mapping + "\n    ) ", instance_declaration)
            for connection in instance_info["connections"]:
                # Insert the connected signals into the empty brackets "()":"
                instance_declaration = re.sub(r"(" + connection[0] + r" +)\(\)", r"\1(" + connection[1] + connection[2] + ")", instance_declaration)
            instances_dictionary[instance_info["canvas_id"]] = instance_declaration
        return instances_dictionary

    def __add_schematic_elements(self, sorted_canvas_ids_for_hdl, hdl_dict, generate_dictionary, file_name):
        schematic_elements = ""
        indent = 4
        # for canvas_id_for_hdl in sorted_canvas_ids_for_hdl:
        #     if (canvas_id_for_hdl in hdl_dict or    # Filter symbols without connected wires (they have a canvas ID but are not part of hdl_dict).
        #         (isinstance(canvas_id_for_hdl, str) and canvas_id_for_hdl.startswith("end generate")) # The string "end generate ..." is an entry of sorted_canvas_ids_for_hdl.
        #        ):
        #         if isinstance(canvas_id_for_hdl, int):
        #             hdl_text = hdl_dict[canvas_id_for_hdl]["hdl_text"]
        #             hdl_text = re.sub(r"^\s*//\s*[0-9]+\s*\n"    , ""   , hdl_text) # Remove the first line if it is a comment line which has only priority information.
        #             hdl_text = re.sub(r"([^^])\s*//\s*[0-9]+\s*$", r"\1", hdl_text, flags=re.MULTILINE) # Remove priority-comments at line end (from generates or instance-names).
        #             hdl_text = re.sub(r"^", ' '*indent, hdl_text, flags=re.MULTILINE)
        #             if hdl_text[-1]!="\n":
        #                 hdl_text += "\n"
        #             hdl_text_for_check = None
        #             if canvas_id_for_hdl in generate_dictionary:
        #                 # There is the possibility to have "begin" already in hdl_text.
        #                 # To check this the word "begin" must be separated from the possible neighbour characters ')' and ':':
        #                 hdl_text_for_check = re.sub(r"\)", " ) ", hdl_text)
        #                 hdl_text_for_check = re.sub(r":" , " : ", hdl_text_for_check)
        #                 if " begin " in hdl_text_for_check:
        #                     hdl_text = re.sub(r" begin ", r"\n        begin", hdl_text_for_check)
        #                     hdl_text = re.sub(r" \) ", ")", hdl_text)
        #                     hdl_text = re.sub(r" : " , ":", hdl_text)
        #                     indent += 8
        #                 else:
        #                     indent += 4
        #                     hdl_text += ' '*indent + "begin\n" # Add "begin" after the "generate"-statement.
        #                     indent += 4
        #             schematic_elements += hdl_text
        #             # Generate-Anweisung, Block, Instance
        #             self.__fill_link_dictionary(hdl_text, file_name, canvas_id_for_hdl, hdl_dict[canvas_id_for_hdl]["type"])
        #         else: # canvas_ids_for_hdl = "end generate <canvas_id_of_generate>"
        #             indent -= 4
        #             schematic_elements += ' '*indent + "end\n"
        #             self.file_line_number += 1
        #             indent -= 4
        #             schematic_elements += ' '*indent + "endgenerate\n"
        #             self.file_line_number += 1
        for canvas_id_for_hdl in sorted_canvas_ids_for_hdl:
            if canvas_id_for_hdl in hdl_dict: # Filter symbols without connected wires (they have a canvas ID but are not part of hdl_dict).
                hdl_text = hdl_dict[canvas_id_for_hdl]["hdl_text"]
                hdl_text = re.sub(r"^\s*//\s*[0-9]+\s*\n"    , ""   , hdl_text) # Remove the first line if it is a comment line which has only priority information.
                hdl_text = re.sub(r"([^^])\s*//\s*[0-9]+\s*$", r"\1", hdl_text, flags=re.MULTILINE) # Remove priority-comments at line end (from generates or instance-names).
                hdl_text = re.sub(r"^", ' '*indent, hdl_text, flags=re.MULTILINE)
                if hdl_text[-1]!="\n":
                    hdl_text += "\n"
                hdl_text_for_check = None
                if canvas_id_for_hdl in generate_dictionary:
                    # There is the possibility to have "begin" already in hdl_text.
                    # To check this the word "begin" must be separated from the possible neighbour characters ')' and ':':
                    hdl_text_for_check = re.sub(r"\)", " ) ", hdl_text)
                    hdl_text_for_check = re.sub(r":" , " : ", hdl_text_for_check)
                    if " begin " in hdl_text_for_check:
                        hdl_text = re.sub(r" begin ", r"\n        begin", hdl_text_for_check)
                        hdl_text = re.sub(r" \)" , ")", hdl_text)
                        hdl_text = re.sub(r" : " , ":", hdl_text)
                        indent += 8
                    else:
                        indent += 4
                        hdl_text += ' '*indent + "begin\n" # Add "begin" after the "generate"-statement.
                        indent += 4
                schematic_elements += hdl_text
                # Generate-Anweisung, Block, Instance
                self.__fill_link_dictionary(hdl_text, file_name, canvas_id_for_hdl, hdl_dict[canvas_id_for_hdl]["type"])
            elif isinstance(canvas_id_for_hdl, str) and canvas_id_for_hdl.startswith("end generate"): # "end generate ..." is an entry of sorted_canvas_ids_for_hdl.
                indent -= 4
                schematic_elements += ' '*indent + "end\n"
                self.file_line_number += 1
                indent -= 4
                schematic_elements += ' '*indent + "endgenerate\n"
                self.file_line_number += 1
        return schematic_elements

    def __fill_link_dictionary(self, hdl_text, file_name, canvas_id_for_hdl, hdl_type):
        # Generate-Anweisung, Block, Instance
        hdl_text_list = hdl_text[:-1].split("\n") # The last "return" of hdl_text is removed before split()
        hdl_text_list_stripped = self.__strip_list_from_endline_comments_and_trailing_blanks(hdl_text_list)
        if hdl_type=="generate":
            link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                "generate", 2, canvas_id_for_hdl, "") # "generate" line and "begin" line
            self.file_line_number += 2
        elif hdl_type=="block":
            for index in range(len(hdl_text_list)):
                link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                    "block", 1, canvas_id_for_hdl, index+1)
                self.file_line_number += 1
        else: # "symbol"
            kind_of_line = ""
            for index, hdl_line in enumerate(hdl_text_list_stripped):
                if index==0 and not hdl_line.endswith("#("):
                    link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                        "instance_name", 1, canvas_id_for_hdl, "")
                    self.file_line_number += 1
                    if hdl_line.endswith("("):
                        kind_of_line = "port_connection"
                elif hdl_line.endswith("#("):
                    kind_of_line = "generic_mapping"
                    local_line_number_in_generic_map = 1
                    self.file_line_number += 1
                elif hdl_line.startswith(") "): # end of generic map
                    if hdl_line.endswith('('):
                        link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                            "instance_name", 1, canvas_id_for_hdl, "")
                        kind_of_line = "port_connection"
                    else:
                        kind_of_line = ""
                    self.file_line_number += 1
                elif hdl_line==');': # end of port map
                    kind_of_line = ""
                    self.file_line_number += 1
                else:
                    if kind_of_line=="generic_mapping":
                        link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                                "generic_mapping", 1, canvas_id_for_hdl, local_line_number_in_generic_map)
                        local_line_number_in_generic_map += 1
                    elif kind_of_line=="port_connection":
                        signal_name = re.sub(r".*\((.*)\).*", r"\1", hdl_line) # extract connected signal from parenthesis
                        signal_name = re.sub(r"\[.*", "", signal_name) # Remove indices from signal name
                        signal_name = signal_name.strip()
                        link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                                "port_connection", 1, canvas_id_for_hdl, signal_name)
                    self.file_line_number += 1

    def __strip_list_from_endline_comments_and_trailing_blanks(self, hdl_text_list):
        hdl_text_list_stripped = []
        for hdl_line in hdl_text_list:
            hdl_line = re.sub(r"//.*", "", hdl_line)
            hdl_line = hdl_line.strip()
            hdl_text_list_stripped.append(hdl_line)
        return hdl_text_list_stripped

    def __create_verilog_format(self, generic_mapping):
        generic_mapping_list = generic_mapping.split("\n")
        generic_mapping = ""
        for generic_entry in generic_mapping_list:
            comment = re.sub(r".*//", "", generic_entry)
            if comment==generic_entry:
                generic_entry_new = generic_entry
                comment = ""
            else:
                generic_entry_new = re.sub(r"//.*", "", generic_entry)
                if generic_entry_new!="":
                    comment = " //" + comment
                else:
                    comment = "//" + comment
            generic_entry_new = re.sub(r",", "", generic_entry_new)
            if generic_entry!=generic_mapping_list[-1]:
                generic_entry_new = re.sub(r"^\s*(.*?)\s*=\s*([^\s]*)\s*", r".\1(\2),", generic_entry_new) + comment
                generic_mapping += generic_entry_new + "\n"
            else:
                generic_entry_new = re.sub(r"^\s*(.*?)\s*=\s*([^\s]*)\s*", r".\1(\2)" , generic_entry_new) + comment
                generic_mapping += generic_entry_new
        return generic_mapping

    def __create_unconnected_instance_dict(self, component_declarations_dict):
        unconnected_instance_dict = {}
        component_language_dict   = {}
        for entity_name, declarations in component_declarations_dict.items():
            component_port_declarations  = declarations[0]
            generic_definition           = declarations[1]
            component_language_dict  [entity_name] = declarations[3]
            unconnected_instance_dict[entity_name] = self.__create_unconnected_instance_declaration(entity_name, component_port_declarations, generic_definition)
        return unconnected_instance_dict, component_language_dict

    def __create_unconnected_instance_declaration(self, entity_name, component_port_declarations, generic_definition):
        open_instance = entity_name + ' '
        if generic_definition!="":
            open_instance += "#generic_definition#"  # The #generic_definition# will be replaced by the parameters defined in the schematic.
        open_instance += "instance-name ("
        port_declaration = []
        #component_port_declarations when VHDL    = ['res_i : in  std_logic', 'clk_i : in  std_logic', ...]
        #component_port_declarations when Verilog = ['input   res_i', 'input   clk_i', ...]
        if component_port_declarations:
            open_instance += "\n"
            for declaration in component_port_declarations:
                declaration_words = declaration.split()
                port_name = declaration_words[-1]
                port_declaration.append(" "*4 + '.' + port_name + "#(),\n") # '#' is used temporarily for indent.
            port_declaration = hdl_generate_functions.HdlGenerateFunctions.indent_identically("#", port_declaration)
            for line in port_declaration:
                line = re.sub("#", "", line)
                open_instance += line
            open_instance = open_instance[:-2] + "\n"
        open_instance += ");"
        return open_instance

    def __create_instance_connection_dict(self, instance_connection_definitions, component_language_dict):
        instance_connection_dict = {}
        for instance_connection_definition in instance_connection_definitions:
            instance_name      = instance_connection_definition["instance_name"]
            entity_name        = instance_connection_definition["entity_name"]
            port_declaration   = instance_connection_definition["port_declaration"]
            signal_declaration = instance_connection_definition["declaration"]
            if instance_name not in instance_connection_dict: # Only the first connection of an instance initializes the dictionary.
                instance_connection_dict[instance_name] = {}
                instance_connection_dict[instance_name]["connections"] = []
                instance_connection_dict[instance_name]["canvas_id"]   = instance_connection_definition["canvas_id"]
            if component_language_dict[entity_name]=="VHDL":
                port_name = port_declaration.split()[0]
            else:
                port_name = port_declaration.split()[-1]
            signal_name, sub_range, _, _, _, _ = hdl_generate_functions.HdlGenerateFunctions.split_declaration(signal_declaration , self.design.get_language())
            signal_name = re.sub(r"\[.*", "", signal_name) # The array range of a signal must not be used, when the signal is connected to a port.
            instance_connection_dict[instance_name]["entity_name"] = entity_name
            instance_connection_dict[instance_name]["connections"].append([port_name, signal_name, sub_range])
        return instance_connection_dict

    def get_content(self):
        return self.module_content
