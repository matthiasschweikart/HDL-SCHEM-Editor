"""
This class analyses all files found in the given hdl-file-list.
For each file the signals are determined which will be implemented by flipflops in synthesis.
For each signal a report(VHDL)/$display(Verilog) command is created and put into a new HDL-file together with the original code.
The hdl-file-list is modified to contain the new HDL file names.
"""
import re
import vhdl_parsing
import verilog_parsing

class GenerateFlipflopStat():
    def __init__(self, hdl_file_list_name, hdl_file_list):
        self.sub_type_identifier       = 0
        output_names                   = []
        output_types                   = []
        output_ranges                  = []
        signal_names                   = []
        signal_types                   = []
        signal_ranges                  = []
        signals_clocked                = []
        entity_name_in_work            = "entity not found"
        self.hdl_file_list_for_ff_stat = ""
        filenames_to_be_changed        = []
        package_type_declarations      = []
        for filename in hdl_file_list:
            if "lib:" not in filename:
                hdl = self.__get_hdl(filename)
                if filename.endswith(".vhd") or filename.endswith(".vhdl"): # external VHDL could use ".vhdl"
                    vhdl_parser_object = vhdl_parsing.VhdlParser(hdl, "entity_context", parse_big_files=False)
                    package_name      = vhdl_parser_object.get("package_name")
                    entity_name       = vhdl_parser_object.get("entity_name")
                    architecture_name = vhdl_parser_object.get("architecture_name")
                    # When the VHDL-module is separated into 2 files, then the first file must be the entity-file, the second the architecture-file.
                    if package_name!="":
                        package_type_declarations += self.__get_type_declarations(vhdl_parser_object)
                        #print("Packge Name =", package_name, package_type_declarations)
                    if entity_name!="":
                        entity_name_in_work = entity_name
                        output_names, output_types, output_ranges = self.__get_outputs(vhdl_parser_object)
                    if architecture_name!="":
                        filename_with_architecture = filename
                        signal_names, signal_types, signal_ranges, signals_clocked, signals_clocked_generate_condition_lists = self.__get_signals(vhdl_parser_object)
                        type_declarations = self.__get_type_declarations(vhdl_parser_object) + package_type_declarations
                        declared_names  = output_names  + signal_names
                        declared_types  = output_types  + signal_types
                        declared_ranges = output_ranges + signal_ranges
                        dummy_type_declarations, report_commands = self.__create_report_commands(entity_name_in_work, signals_clocked, signals_clocked_generate_condition_lists,
                                                                                                 declared_names, declared_types, declared_ranges, type_declarations)
                        self.__create_extended_vhdl_file(filename_with_architecture, hdl, dummy_type_declarations, report_commands, architecture_name)
                        filenames_to_be_changed.append(filename)
                        self.hdl_file_list_for_ff_stat = self.__modify_hdl_file_list(hdl_file_list_name, filenames_to_be_changed)
                else:
                    # Verilog file
                    verilog_parser_object = verilog_parsing.VerilogParser(hdl, "module", parse_big_files=False)
                    _, _, _, signals_clocked, signals_clocked_generate_condition_lists = self.__get_signals(verilog_parser_object)
                    report_commands = self.__create_verilog_report_commands(signals_clocked,signals_clocked_generate_condition_lists)
                    self.__create_extended_verilog_file(filename, hdl, report_commands)
                    filenames_to_be_changed.append(filename)
                    self.hdl_file_list_for_ff_stat = self.__modify_hdl_file_list(hdl_file_list_name, filenames_to_be_changed)

    def __create_extended_verilog_file(self, filename, hdl, report_commands):
        new_file_name = re.sub(r"\.v", "_flipflop_stat.v", filename)
        add_on  = "    initial begin\n"
        for report_command in report_commands:
            add_on += "        " + report_command + "\n"
        add_on += "    end;\n"
        extended_hdl = re.sub(r"endmodule", add_on + "endmodule", hdl)
        fileobject = open(new_file_name, 'w', encoding="utf-8")
        fileobject.write(extended_hdl)
        fileobject.close()

    def __get_hdl(self, filename):
        fileobject = open(filename, 'r', encoding="utf-8")
        data_read = fileobject.read()
        fileobject.close()
        return data_read

    def __get_outputs(self, vhdl_parser_object):
        output_names  = []
        output_types  = []
        output_ranges = []
        port_interface_names     = vhdl_parser_object.get("port_interface_names")
        port_interface_direction = vhdl_parser_object.get("port_interface_direction")
        port_interface_types     = vhdl_parser_object.get("port_interface_types" )
        port_interface_ranges    = vhdl_parser_object.get("port_interface_ranges")
        for index, port_name in enumerate(port_interface_names):
            if port_interface_direction[index]=="out":
                output_names .append(port_name)
                output_types .append(port_interface_types [index])
                output_ranges.append(port_interface_ranges[index])
        return output_names, output_types, output_ranges

    def __get_signals(self, parser_object):
        signal_names    = parser_object.get("signal_constant_variable_names")
        signal_types    = parser_object.get("signal_constant_variable_types")
        signal_ranges   = parser_object.get("signal_constant_variable_ranges")
        signals_clocked                          = parser_object.get("clocked_signals")
        signals_clocked_generate_condition_lists = parser_object.get("clocked_signals_generate_conditions")
        return signal_names, signal_types, signal_ranges, signals_clocked, signals_clocked_generate_condition_lists

    def __get_type_declarations(self, vhdl_parser_object):
        type_declarations = vhdl_parser_object.get("architecture_type_declarations")
        filtered_type_declarations = []
        for type_declaration in type_declarations:
            type_declaration_without_whitespace = []
            for word in type_declaration:
                if word not in ["", " ", "\n", "\r", "\t"]:
                    type_declaration_without_whitespace.append(word)
            filtered_type_declarations.append(type_declaration_without_whitespace)
        return filtered_type_declarations

    def __create_report_commands(self, entity_name_in_work, signals_clocked, signals_clocked_generate_condition_lists,
                                 declared_names, declared_types, declared_ranges, type_declarations):
        dummy_type_declarations = []
        report_commands         = []
        for signal_index, clocked_signal_name in enumerate(signals_clocked):      # Check each signal which gets a value in a clocked process.
            for declared_name_index, declared_name in enumerate(declared_names):  # Search for the signal declaration.
                if declared_name==clocked_signal_name:
                    clocked_signal_generate_conditions = signals_clocked_generate_condition_lists[signal_index]
                    if clocked_signal_generate_conditions:
                        self.__create_report_command_for_generate_condition_of_signal(clocked_signal_generate_conditions, report_commands, entity_name_in_work, clocked_signal_name)
                    clocked_signal_type  = declared_types [declared_name_index]
                    clocked_signal_range = declared_ranges[declared_name_index]
                    if clocked_signal_type in ["integer", "natural", "positive", "negative",
                                               "std_logic", "std_ulogic", "bit", "boolean",
                                               "signed", "unsigned", "std_logic_vector", "std_ulogic_vector", "bit_vector"]:
                        self.__append_report_commands(clocked_signal_type, clocked_signal_name, clocked_signal_range, entity_name_in_work, dummy_type_declarations, report_commands)
                    else: # The clocked signal has a user defined type.
                        # Supported user types are enumeration-type and "array of standard types"-types.
                        type_definition_found = False
                        for type_declaration in type_declarations:
                            if clocked_signal_type==type_declaration[1]: # In index 1 the type name is stored
                                type_definition_found = True
                                self.__append_report_command_from_user_type(entity_name_in_work, clocked_signal_name, clocked_signal_type,
                                                                        type_declaration, dummy_type_declarations, type_declarations, report_commands)
                                break
                        if not type_definition_found:
                            report_commands.append('report "flipflop_statistics for instance " & ' + entity_name_in_work + "'path_name & " + '" signal ' + clocked_signal_name +
                                                " with type " + clocked_signal_type + ' needs an unknown number of flipflops (no type definition was found).";')
        if not report_commands:
            report_commands.append('report "flipflop_statistics for instance " & ' + entity_name_in_work + "'path_name & " + '" no clocked signals found.";')
        return dummy_type_declarations, report_commands

    def __append_report_commands(self, clocked_signal_type, clocked_signal_name, clocked_signal_range, entity_name_in_work, dummy_type_declarations, report_commands):
        if clocked_signal_type in ["integer", "natural", "positive", "negative"]:
            dummy_type_declarations.append("subtype t_ff_stat_" + str(self.sub_type_identifier) + " is " + clocked_signal_type + " " + clocked_signal_range + ";")
            report_commands.append('report "flipflop_statistics for instance " & ' + entity_name_in_work + "'path_name & " + '" signal ' + clocked_signal_name +
                                    ' uses "' + " & integer'image(integer(ceil(log(real(abs(t_ff_stat_" + str(self.sub_type_identifier) + "'right " + " - " +
                                    "t_ff_stat_" + str(self.sub_type_identifier) + "'left" + ") + 1))/log(2.0)))) & " + '" flipflops.";')
            self.sub_type_identifier += 1
        elif clocked_signal_type in ["std_logic", "std_ulogic", "bit", "boolean"]:
            report_commands.append('report "flipflop_statistics for instance " & ' + entity_name_in_work + "'path_name & " + '" signal ' + clocked_signal_name +
                                    ' uses 1 flipflop.";')
        elif clocked_signal_type in ["signed", "unsigned", "std_logic_vector", "std_ulogic_vector", "bit_vector"]:
            report_commands.append('report "flipflop_statistics for instance " & ' + entity_name_in_work + "'path_name & " + '" signal ' + clocked_signal_name +
                                    ' uses "' + " & integer'image(" + clocked_signal_name + "'length) & "+ '" flipflops.";')

    def __create_report_command_for_generate_condition_of_signal(self, clocked_signal_generate_conditions, report_commands, entity_name_in_work, clocked_signal_name):
        complete_condition = ""
        for clocked_signal_generate_condition in clocked_signal_generate_conditions:
            complete_condition += '(' + clocked_signal_generate_condition + ') and'
        complete_condition = re.sub(r" and$", "", complete_condition) # Remove last added "and".
        report_commands.append('report "flipflop_statistics for instance " & ' + entity_name_in_work + "'path_name & " + '" signal ' + clocked_signal_name +
                            ' generate-condition == "' + " & boolean'image("+ complete_condition +");")

    def __create_verilog_report_commands(self, signals_clocked,signals_clocked_generate_condition_lists):
        report_commands = []
        for index, clocked_signal_name in enumerate(signals_clocked):
            generate_condition = ""
            for condition in signals_clocked_generate_condition_lists[index]:
                generate_condition += condition + " and"
            generate_condition = re.sub(r" and$", "", generate_condition)
            report_commands.append('$display("flipflop_statistics for instance %m signal ' + clocked_signal_name +
                                    ' generate-condition == ", ' + generate_condition + ');')
            report_commands.append('$display("flipflop_statistics for instance %m signal ' + clocked_signal_name +
                                    ' uses ", $bits(' + clocked_signal_name + '),  " flipflops.");')
        if not report_commands:
            report_commands.append('$display("flipflop_statistics for instance %m no clocked signals found.");')
        return report_commands

    def __append_report_command_from_user_type(self, entity_name_in_work, clocked_signal_name, clocked_signal_type,
                                            type_declaration_for_clocked_signal, dummy_type_declarations, type_declarations, report_commands):
        if type_declaration_for_clocked_signal[3]=='(': # enumeration type
            word = ""
            for word in type_declaration_for_clocked_signal:
                if word==')':
                    rightmost_value = previous_word
                    report_commands.append('report "flipflop_statistics for instance " & ' + entity_name_in_work + "'path_name & " + '" signal ' + clocked_signal_name +
                                      ' uses "' + " & integer'image(integer(ceil(log(real(" +
                                      clocked_signal_type + "'pos(" + rightmost_value + ") + 1))/log(2.0)))) & " + '" flipflops.";')
                    break
                previous_word = word
        elif type_declaration_for_clocked_signal[3]=="array":
            depth_of_type_definition = 0
            depth_of_type_definition, element_type_name, element_range_definition = self.__determine_depth_of_array_type_definition(clocked_signal_type, type_declarations,
                                                                                                                                    depth_of_type_definition)
            if depth_of_type_definition==0:
                report_commands.append('report "flipflop_statistics for instance " & ' + entity_name_in_work + "'path_name & " + '" signal ' + clocked_signal_name +
                                                        " with type " + clocked_signal_type + ' needs an unknown number of flipflops.";')
            else:
                for _ in range(depth_of_type_definition):
                    report_commands.append('report "flipflop_statistics for instance " & ' + entity_name_in_work + "'path_name & " + '" signal ' + clocked_signal_name +
                                           ' element-length = " & ' + "integer'image(" + clocked_signal_name + "'length" + ');')
                     # No blanks are allowed in clocked_signal_name, because blanks are used as separator later on:
                    clocked_signal_name = clocked_signal_name + '(' + clocked_signal_name + "'left)"
                self.__append_report_commands(element_type_name, clocked_signal_name, element_range_definition, entity_name_in_work, dummy_type_declarations, report_commands)
        else:
            report_commands.append('report "flipflop_statistics for instance " & ' + entity_name_in_work + "'path_name & " + '" signal ' + clocked_signal_name +
                                                        " with type " + clocked_signal_type + ' needs an unknown number of flipflops.";')

    def __determine_depth_of_array_type_definition(self, type_name, type_declarations, depth):
        for type_declaration in type_declarations:
            if type_declaration[1]==type_name and type_declaration[3]=="array":
                element_type_name, element_range_definition = self.__get_the_type_of_an_array_element(type_declaration)
                if element_type_name=="":
                    #print("__determine_depth_of_array_type_definition: In the type-declarations no element-type was found (missing word 'of' or type-declaration is incomplete).")
                    return 0, "", ""
                depth += 1
                if element_type_name in ["integer", "natural", "positive", "negative",
                                            "std_logic_vector", "std_ulogic_vector", "bit_vector", "unsigned", "signed",
                                            "std_logic", "std_ulogic", "bit"]:
                    return depth, element_type_name, element_range_definition
                return self.__determine_depth_of_array_type_definition(element_type_name, type_declarations, depth)
        return depth, "", ""

    def __get_the_type_of_an_array_element(self, type_declaration):
        element_type_name        = ""
        element_range_definition = ""
        next_word_is_type   = False
        copy_range          = False
        for word in type_declaration:
            if word=='of':
                next_word_is_type = True
                copy_range = True
            elif next_word_is_type:
                element_type_name = word
                next_word_is_type = False
            elif copy_range and word!=';':
                element_range_definition += ' ' + word
        return element_type_name, element_range_definition

    def __create_extended_vhdl_file(self, filename_with_architecture, hdl, dummy_type_declarations, report_commands, architecture_name):
        new_file_name = re.sub(r"\.vhd", "_flipflop_stat.vhd", filename_with_architecture)
        prefix  = "library ieee;\n"
        prefix += "use ieee.math_real.all;\n"
        add_on  = "    process\n"
        for dummy_type_declaration in dummy_type_declarations:
            add_on += "        " + dummy_type_declaration + "\n"
        add_on += "    begin\n"
        for report_command in report_commands:
            add_on += "        " + report_command + "\n"
        add_on += "        wait;\n"
        add_on += "    end process;\n"
        # End of file:
        # 1: end architecture;
        # 2: end architecture <name>;
        # 3: end <name>;
        extended_hdl = re.sub(r"((end\s+architecture|end\s+" + architecture_name + "))", add_on + r"\1", prefix + hdl)
        fileobject = open(new_file_name, 'w', encoding="utf-8")
        fileobject.write(extended_hdl)
        fileobject.close()

    def __modify_hdl_file_list(self, hdl_file_list_name, filenames_to_be_changed):
        fileobject = open(hdl_file_list_name, 'r', encoding="utf-8")
        hdl_file_list_for_ff_stat = fileobject.read()
        fileobject.close()
        for filename_to_be_changed in filenames_to_be_changed:
            if   filename_to_be_changed.endswith(".vhdl"):
                extension = ".vhdl"
            elif filename_to_be_changed.endswith(".vhd"):
                extension = ".vhd"
            elif filename_to_be_changed.endswith(".v"):
                extension = ".v"
            elif filename_to_be_changed.endswith(".sv"):
                extension = ".sv"
            else:
                print("HDL-SCHEM-Editor: Fatal, file has unknown file extension:", filename_to_be_changed)
                return []
            filename_to_be_changed_without_extension = re.sub(extension + '$', "", filename_to_be_changed)
            hdl_file_list_for_ff_stat = re.sub(filename_to_be_changed, filename_to_be_changed_without_extension + "_flipflop_stat" + extension, hdl_file_list_for_ff_stat)
        fileobject = open(hdl_file_list_name, 'w', encoding="utf-8")
        fileobject.write(hdl_file_list_for_ff_stat)
        fileobject.close()
        return hdl_file_list_for_ff_stat
