"""
Generates the VHDL-Entity

"""
import re
import hdl_generate_functions
import link_dictionary
import list_separation_check

class GenerateEntity():
    def __init__(self,
                 design, #   : design_data.DesignData,
                 input_declarations, output_declarations, inout_declarations, file_name):
        self.design = design
        self.entity = ""
        module_name     = self.design.get_module_name()
        text_dictionary = self.design.get_text_dictionary()
        self.file_line_number = 3 # Line 1 is filename-comment, Line 2 is date-comment
        if "interface_packages" in text_dictionary:
            self.entity += self.__get_interface_packages(text_dictionary, file_name)
        self.entity += self.__get_entity_declaration_line(module_name, file_name)
        if "interface_generics" in text_dictionary:
            self.entity += self.__get_generic_declarations(text_dictionary, file_name)
        self.entity += self.__get_port_declarations(input_declarations, output_declarations, inout_declarations, file_name)
        self.entity += "end entity "+ module_name +";\n"
        self.file_line_number += 1

    def get_entity(self):
        return self.entity

    def __get_interface_packages(self, text_dictionary, file_name):
        interface_packages = text_dictionary["interface_packages"]
        if interface_packages!="" and not interface_packages.isspace():
            if interface_packages[-1]!="\n":
                interface_packages += "\n"
            number_of_new_lines = interface_packages.count("\n")
            link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                   "interface_packages", number_of_new_lines, "", "")
            self.file_line_number += number_of_new_lines
            return interface_packages
        return ""

    def __get_entity_declaration_line(self, module_name, file_name):
        link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                "entity", 1, "", "")
        self.file_line_number += 1
        return "entity " + module_name + " is\n"

    def __get_generic_declarations(self, text_dictionary, file_name):
        generic_declarations = ""
        generics = text_dictionary["interface_generics"]
        generics = list_separation_check.ListSeparationCheck(generics, "VHDL").get_fixed_list()
        if generics!="" and not generics.isspace():
            generics = re.sub("^([^\\n])", " "*8 + "\\1", generics, flags=re.MULTILINE) # Add 8 blanks at the line start.
            if generics[-1]!="\n":
                generics += "\n"
            number_of_new_lines = generics.count("\n")
            generic_declarations  = "    generic (\n"
            self.file_line_number += 1
            link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                   "interface_generics", number_of_new_lines, "", "")
            self.file_line_number += number_of_new_lines
            generic_declarations += generics
            generic_declarations += "    );\n"
            self.file_line_number += 1
        return generic_declarations

    def __get_port_declarations(self, input_declarations, output_declarations, inout_declarations,file_name):
        declaration_list = sorted(input_declarations) + sorted(output_declarations) + sorted(inout_declarations)
        if declaration_list==[]:
            return ""
        declaration_list = hdl_generate_functions.HdlGenerateFunctions.indent_identically(':', declaration_list)
        declarations = "    port (\n"
        self.file_line_number += 1
        for declaration in declaration_list: # Get port_name by split_declaration before ';' is added.
            declaration = re.sub(r":\s*in\s+"   , ": ", declaration)
            declaration = re.sub(r":\s*out\s+"  , ": ", declaration)
            declaration = re.sub(r":\s*inout\s+", ": ", declaration)
            port_name, _, _, _, _ = hdl_generate_functions.HdlGenerateFunctions.split_declaration(declaration, "VHDL")
            link_dictionary.LinkDictionary.link_dict_reference.add(self.design.window, file_name, self.file_line_number,
                                                                    "port_declaration", 1, port_name, "")
            self.file_line_number += 1
        declaration_list = self.__add_semicolons_to_all_but_last_declaration(declaration_list)
        for declaration in declaration_list:
            declarations += declaration
        declarations += "    );\n"
        self.file_line_number += 1
        return declarations

    def __add_semicolons_to_all_but_last_declaration(self, declaration_list):
        declaration_list_with_semicolon = []
        for declaration in declaration_list:
            if   " --" in declaration:
                declaration = re.sub(r" --", r"; --", declaration)
                declaration_list_with_semicolon.append(" "*8 + declaration + "\n")
            elif "--"  in declaration:
                declaration = re.sub(r"--" , r"; --", declaration)
                declaration_list_with_semicolon.append(" "*8 + declaration + "\n")
            else:
                declaration_list_with_semicolon.append(" "*8 + declaration + ";\n")
        declaration_list_with_semicolon[-1] = re.sub(r";\n" , r"\n" , declaration_list_with_semicolon[-1])
        declaration_list_with_semicolon[-1] = re.sub(r"; --", r" --", declaration_list_with_semicolon[-1])
        return declaration_list_with_semicolon
