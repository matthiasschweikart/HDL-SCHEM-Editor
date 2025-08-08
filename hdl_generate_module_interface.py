"""
Generate a Verilog Module Interface
"""
import re
import link_dictionary
import hdl_generate_functions
import list_separation_check

class GenerateModuleInterface:
    def __init__(self, design, input_declarations, output_declarations, inout_declarations, file_name):
        self.design           = design
        self.module           = ""
        module_name           = self.design.get_module_name()
        text_dictionary       = self.design.get_text_dictionary()
        self.file_line_number = 3 # Line 1 is filename-comment, Line 2 is date-comment
        self.module           += "module " + module_name + "\n"
        self.file_line_number += 1
        if "interface_generics" in text_dictionary:
            self.module += self.__get_parameter_declarations(text_dictionary, file_name)
        self.module += self.__get_port_declarations(input_declarations, output_declarations, inout_declarations, file_name)

    def get_interface(self):
        return self.module

    def __get_parameter_declarations(self, text_dictionary, file_name):
        parameter_declarations = ""
        parameters = text_dictionary["interface_generics"]
        parameters = list_separation_check.ListSeparationCheck(parameters, "Verilog").get_fixed_list()
        if parameters!="" and not parameters.isspace():
            parameters = re.sub("^([^\\n])", " "*8 + "\\1", parameters, flags=re.MULTILINE) # Add 8 blanks at the line start of not empty lines.
            if parameters[-1]!="\n":
                parameters += "\n"
            number_of_new_lines = parameters.count("\n")
            parameter_declarations = "    #(parameter\n"
            self.file_line_number += 1
            link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                   "interface_generics", number_of_new_lines, "", "")
            self.file_line_number += number_of_new_lines
            parameter_declarations += parameters
            parameter_declarations += "    )\n"
            self.file_line_number += 1
        return parameter_declarations

    def __get_port_declarations(self, input_declarations, output_declarations, inout_declarations, file_name):
        declaration_list = sorted(input_declarations) + sorted(output_declarations) + sorted(inout_declarations)
        if declaration_list==[]:
            declarations = "    ;\n"
            self.file_line_number += 1
            return declarations
        declarations = "    (\n"
        self.file_line_number += 1
        for declaration in declaration_list:
            declaration = re.sub(r"^input " , "wire ", declaration)
            declaration = re.sub(r"^output ", ""     , declaration)
            declaration = re.sub(r"^inout " , ""     , declaration)
            port_name, _, _, _, _, _ = hdl_generate_functions.HdlGenerateFunctions.split_declaration(declaration, "Verilog")
            link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                   "port_declaration", 1, port_name, "")
            self.file_line_number += 1
        declaration_list = self.__add_commas_to_all_but_the_last_declaration(declaration_list)
        for declaration in declaration_list:
            declarations += declaration
        declarations += "    );\n"
        self.file_line_number += 1
        return declarations

    def __add_commas_to_all_but_the_last_declaration(self, declaration_list):
        port_declaration_list_with_comma = []
        for declaration in declaration_list:
            if   " //" in declaration:
                declaration = re.sub(r" //", r", //", declaration)
                port_declaration_list_with_comma.append(" "*8 + declaration + "\n")
            elif "//"  in declaration:
                declaration = re.sub(r"//" , ", //", declaration)
                port_declaration_list_with_comma.append(" "*8 + declaration + "\n")
            else:
                port_declaration_list_with_comma.append(" "*8 + declaration + ",\n")
        port_declaration_list_with_comma[-1] = re.sub(r",\n" , r"\n" , port_declaration_list_with_comma[-1])
        port_declaration_list_with_comma[-1] = re.sub(r", //", r" //", port_declaration_list_with_comma[-1])
        return port_declaration_list_with_comma
