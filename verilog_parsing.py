"""
Verilog Parser
The Verilog Parser does leave generate loops before they are ended. This allows nested generates.
"""
import re

class VerilogParser():
    tag_position_list = (
        "comment_positions"                 ,
        "entity_name_positions"             ,
        "keyword_positions"                 ,
        "label_positions"                   ,
        "begin_label_positions"             ,
        "data_type_positions"               ,
        "port_interface_direction_positions"
        )
    def __init__(self, verilog, region="module", parse_big_files=False):
        self.debug = False
        self.verilog = verilog.lower()
        self.region  = region
        self.return_region = None
        length       = len(self.verilog)
        reg_ex_list_for_splitting_into_words = [
                       #re.compile(r"$"),
                       re.compile(r"\("),
                       re.compile(r"\)"),
                       re.compile(r"\["),
                       re.compile(r"\]"),
                       re.compile(r"\n"),
                       re.compile(r"<="),
                       re.compile(r">="),
                       re.compile(r"=="),
                       re.compile(r"!="),
                       re.compile(r"#"),
                       re.compile(r";"),
                       re.compile(r":"),
                       re.compile(r"="),
                       re.compile(r"<"),
                       re.compile(r">"),
                       re.compile(r","),
                       re.compile(r"//.*(\n|$)"),
                       re.compile(r"(?s)/\*.*\*/"), # Multiline comment. (?s) = Extension notation, 's' means '.' matches all, this means also newline characters.
                       re.compile(r"[ \n\r\t]|$") # White space: Blank, Return, Linefeed, Tabulator or String-End
                      ]
        self.number_of_characters_read = 0
        word_list = []
        while self.number_of_characters_read<length and (self.number_of_characters_read<100000 or parse_big_files is True):
            # data_word1 contains the characters from index 0 to the string searched for.
            # data_word2 contains the string searched for.
            data_word1, data_word2 = self._get_next_words(reg_ex_list_for_splitting_into_words)
            word_list.append(data_word1)
            word_list.append(data_word2)
        self.parse_result = {}
        self.parse_result["keyword_positions"                              ] = [] # There is no entry with the key "keyword" as such a list is useless.
        self.parse_result["comment"                                        ] = []
        self.parse_result["comment_positions"                              ] = []
        self.parse_result["entity_name"                                    ] = ""
        self.parse_result["entity_name_positions"                          ] = []
        self.parse_result["label_names"                                    ] = []
        self.parse_result["label_positions"                                ] = []
        self.parse_result["begin_label_names"                              ] = []
        self.parse_result["begin_label_positions"                          ] = []
        self.parse_result["instance_types"                                 ] = []
        self.parse_result["port_interface_names"                           ] = []
        self.parse_result["port_interface_names_positions"                 ] = []
        self.parse_result["port_interface_direction"                       ] = []
        self.parse_result["port_interface_direction_positions"             ] = []
        self.parse_result["port_interface_types"                           ] = []
        self.parse_result["port_interface_types_positions"                 ] = []
        self.parse_result["port_interface_ranges"                          ] = []
        self.parse_result["port_interface_init"                            ] = []
        self.parse_result["port_interface_init_positions"                  ] = []
        self.parse_result["port_interface_init_range"                      ] = []
        self.parse_result["generics_interface_names"                       ] = []
        self.parse_result["generics_interface_names_positions"             ] = []
        self.parse_result["generics_interface_ranges"                      ] = []
        self.parse_result["generics_interface_init"                        ] = []
        self.parse_result["generics_interface_init_positions"              ] = []
        self.parse_result["signal_constant_variable_names"                 ] = []
        self.parse_result["signal_constant_variable_types"                 ] = []
        self.parse_result["signal_constant_variable_ranges"                ] = []
        self.parse_result["clocked_signals"                                ] = []
        self.parse_result["clocked_signals_generate_conditions"            ] = [] # Contains a list of conditions for each element of self.parse_result["clocked_signals")
        self._analyze(word_list)

    def _get_next_words(self, reg_ex_list_for_splitting_into_words):
        match_list = []
        for reg_ex in reg_ex_list_for_splitting_into_words:
            match = reg_ex.search(self.verilog)
            if match is not None:
                match_list.append(match)
        end_of_file = False
        first_match = 0
        if len(match_list)==1:
            first_match = match_list[0]
            if str(match.re)=="re.compile('$')":
                end_of_file = True
        else:
            index_of_first_match = len(self.verilog)
            for match in match_list:
                if match.start()<index_of_first_match:
                    first_match          = match
                    index_of_first_match = match.start()
        start_index_of_word_before_search_string = self.number_of_characters_read
        end_index_of_word_before_search_string   = self.number_of_characters_read + first_match.start()
        start_index_of_search_string_match       = end_index_of_word_before_search_string
        end_index_of_search_string_match         = self.number_of_characters_read + first_match.end()
        word1 = self.verilog[0:first_match.start()]
        if end_of_file is False:
            word2 = self.verilog[first_match.start():first_match.end()]
        else:
            # Without checking end_of_file, word2 would get the value "" (empty string).
            # Here this empty string is replaced by "End-Of-File".
            # This change is needed, because at region=="parameter_value" the incoming parameter value can consist out of several
            # words. So these words are accumulated to the needed parameter-value and stored in parse_result["generics_interface_init"]
            # as soon as the region is left. But when a parameter_list was parsed "alone", the region will not be left. Then the end
            # of file must be detected, which becomes possible by the replacement done here:
            word2 = "End-Of-File"
        self.verilog = self.verilog[first_match.end():]
        self.number_of_characters_read = end_index_of_search_string_match
        return   [word1, start_index_of_word_before_search_string, end_index_of_word_before_search_string
               ],[word2, start_index_of_search_string_match, end_index_of_search_string_match]

    def _analyze(self, word_list):
        parameter_definition = ""
        in_generate = 0
        active_generate_conditions = []
        for word in word_list:
            if self.debug and word[0] not in ["", " ", "\n", "\r", "\t"]:
                print("word[0] =", word[0])
            # By _analyze() the Verilog is splitted up and all the single pieces are packed into self.parse_result.
            # But the parameter definitions of an module (and all the included comments) are sometimes needed in their original form.
            # So here during the parsing all peaces of the parameter definition are collected and put back together.
            # Because the parsing is still in one of the relevant "parameter_.." regions, when the closing bracket of the parameter
            # definition is found, the closing bracket must be excluded:
            if (self.region=="parameter_value" and word[0]!=')') or self.region in ["parameter_list", "parameter_range"]:
                parameter_definition += word[0]
            if word[0].startswith("//"):
                self.parse_result["comment"]           += [word[0]]
                self.parse_result["comment_positions"] += [[word[1], word[2]]]
            elif word[0].startswith("/*"):
                #print("Comment = ", word[0])
                self.parse_result["comment"]           += [word[0]]
                self.parse_result["comment_positions"] += [[word[1], word[2]]]
            elif self.region=="module":
                if word[0]=="module":
                    self.region = "module_name"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    if self.debug:
                        print("jump to self.region =", self.region)
            elif self.region=="module_name":
                if word[0]=="#":
                    self.region = "parameter_list_region"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0]=="(":
                    self.region = "port_region"
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0]==";":
                    self.region = "declaration_region"
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0] not in ["", " ", "\n", "\r", "\t"]: # Jump over whitespaces
                    self.parse_result["entity_name"] = word[0]
                    self.parse_result["entity_name_positions"] += [[word[1], word[2]]]
            elif self.region=="parameter_list_region":
                if word[0]=="(":
                    self.region = "parameter_region"
                    if self.debug:
                        print("jump to self.region =", self.region)
            elif self.region=="parameter_region":
                if word[0]=="parameter":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "parameter_list"
                    if self.debug:
                        print("jump to self.region =", self.region)
            elif self.region=="parameter_list":
                if word[0]=="=":
                    self.region = "parameter_value"
                    parameter_value = ""
                    parameter_value_position = [0, 0]
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0]=="[":
                    self.region = "parameter_range"
                    parameter_range = "["
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0] not in ["", " ", "\n", "\r", "\t"]: # Jump over whitespaces
                    self.parse_result["generics_interface_names"].append(word[0])
                    self.parse_result["generics_interface_names_positions"].append([word[1], word[2]])
                    self.parse_result["generics_interface_ranges"].append("") # Default value, as a parameter must not have a range.
            elif self.region=="parameter_range":
                if word[0]=="]":
                    self.region = "parameter_list"
                    self.parse_result["generics_interface_ranges"][-1] = parameter_range + ']'
                    if self.debug:
                        print("jump to self.region =", self.region)
                else:
                    parameter_range += word[0]
            elif self.region=="parameter_value":
                if word[0]==")": # This is the last bracket which closes the parameter declaration.
                    self.region = "module_name"
                    self.parse_result["generics_interface_init"].append(parameter_value)
                    self.parse_result["generics_interface_init_positions"].append(parameter_value_position)
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0]==",":
                    self.parse_result["generics_interface_init"].append(parameter_value)
                    self.parse_result["generics_interface_init_positions"].append(parameter_value_position)
                    self.region = "parameter_list"
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0]=="End-Of-File":
                    self.parse_result["generics_interface_init"].append(parameter_value)
                    self.parse_result["generics_interface_init_positions"].append(parameter_value_position)
                elif word[0] not in ["", " ", "\n", "\r", "\t"]: # Jump over whitespaces
                    if parameter_value_position[0]==0:
                        parameter_value_position[0] = word[1]
                    parameter_value += word[0]
                    parameter_value_position[1] = word[2]
            elif self.region=="port_region":
                if word[0] not in ["", " ", "\n", "\r", "\t"]: # Jump over whitespaces
                    self.parse_result["port_interface_direction"          ].append(word[0])  # word[0] is "input", "output" or "inout".
                    self.parse_result["port_interface_direction_positions"].append([word[1], word[2]])
                    self.parse_result["port_interface_ranges"             ].append("") # Default value, as a range must not exist.
                    self.parse_result["port_interface_types"              ].append("") # Default value, as a type must not exist.
                    self.parse_result["port_interface_types_positions"    ].append([0, 0]) # Default value, as a type must not exist.
                    self.port_declaration_subtype = False
                    self.region = "port_declaration"
                    if self.debug:
                        print("jump to self.region =", self.region)
            elif self.region=="port_declaration":
                if word[0] in ["signed", "unsigned"]:
                    self.port_declaration_subtype = True
                    self.parse_result["port_interface_types"          ][-1] = word[0]
                    self.parse_result["port_interface_types_positions"][-1] = [word[1], word[2]]
                elif word[0]=="reg" or word[0]=="wire" or word[0]=="logic":
                    if not self.port_declaration_subtype:
                        self.parse_result["port_interface_types"          ][-1] = word[0]
                        self.parse_result["port_interface_types_positions"][-1] = [word[1], word[2]]
                    else:
                        self.parse_result["port_interface_types"          ][-1] += ' ' + word[0]
                        self.parse_result["port_interface_types_positions"][-1][1] = word[2]
                elif word[0]=='[':
                    self.region = "port_range_region"
                    port_range = '['
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0]==',':
                    self.region = "port_region"
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0]==')':
                    self.region = "module_name"
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0] not in ["", " ", "\n", "\r", "\t"]: # Jump over whitespaces
                    self.parse_result["port_interface_names"          ].append(word[0])
                    self.parse_result["port_interface_names_positions"].append([word[1], word[2]])
            elif self.region=="port_range_region":
                if word[0]=="]":
                    self.region = "port_declaration"
                    self.parse_result["port_interface_ranges"][-1] = port_range + ']'
                    if self.debug:
                        print("jump to self.region =", self.region)
                else:
                    port_range += word[0]
            elif self.region=="declaration_region":
                if word[0]=="endmodule":
                    self.region = "module"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0]==":" and previous_word[0]=="begin":
                    self.region = "begin_label"
                    self.return_region = "declaration_region"
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0] in ["endgenerate"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    del active_generate_conditions[-1]
                    in_generate -= 1
                elif word[0] in ["end"]: # relicts from "always", "generate", which were not parsed.
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]=="function":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "function"
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0] in ["integer", "real", "reg"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "variable_declaration"
                elif word[0] in ["wire", "assign", "genvar", "parameter", "localparam"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "statement"
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0] in ["always"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    begin_counter = 0
                    signal_name = ""
                    self.region = "always_block"
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0] in ["generate"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    in_generate += 1
                    generate_if_condition_string   = ""
                    generate_for_condition_string  = ""
                    generate_case_condition_string = ""
                    self.region = "generate_block"
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0] in ["initial"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    begin_counter = 0
                    self.region = "initial_block"
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    #print("found instance:", word[0])
                    self.parse_result["instance_types"].append(word[0])
                    self.region = "instance"
                    begin_counter = 0
                    if self.debug:
                        print("jump to self.region =", self.region)
            elif self.region=="variable_declaration":
                if word[0]==";":
                    self.region = "declaration_region"
                    if self.debug:
                        print("jump to self.region =", self.region)
            elif self.region=="initial_block":
                if word[0]=="begin":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    begin_counter += 1
                elif word[0]=="end":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    begin_counter -= 1
                    if begin_counter==0:
                        self.region = "declaration_region"
                        if self.debug:
                            print("jump to self.region =", self.region)
                elif word[0] in ["forever", "if", "for", "else", "while"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="instance":
                #print("in instance: word[0] =", word[0])
                if word[0]=='#':
                    open_bracket = 0
                    self.region = "generic_list"
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0]==';':
                    self.region = "declaration_region"
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    #print("found instance_name:", word[0])
                    self.parse_result["label_names"].append(word[0])
                    self.parse_result["label_positions"] += [[word[1], word[2]]]
                    open_bracket = 0
                    self.region = "port_map"
                    if self.debug:
                        print("jump to self.region =", self.region)
            elif self.region=="generic_list":
                if word[0]=='(':
                    open_bracket += 1
                elif word[0]==')':
                    open_bracket -= 1
                    if open_bracket==0:
                        self.region = "instance"
                        if self.debug:
                            print("jump to self.region =", self.region)
            elif self.region=="port_map":
                if word[0]=='(':
                    open_bracket += 1
                elif word[0]==')':
                    open_bracket -= 1
                    if open_bracket==0:
                        self.region = "instance"
                        if self.debug:
                            print("jump to self.region =", self.region)
            elif self.region=="function":
                # Everything is ignored here until "endfunction"
                if word[0]=="endfunction":
                    self.region = "declaration_region"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0] in ["if", "for", "else", "while", "begin" ]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="statement":
                if word[0]==';':
                    self.region = "declaration_region"
                    if self.debug:
                        print("jump to self.region =", self.region)
            elif self.region=="always_block":
                #print("always_block:", word[0], previous_word)
                if word[0]=="@":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "sensitivity_list"
                    clocked_always_block = False
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0]=="begin":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    begin_counter += 1
                elif word[0]==":" and previous_word[0]=="begin":
                    self.region = "begin_label"
                    self.return_region = "always_block"
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0]==":":
                    self.parse_result["begin_label_names"].append(previous_word[0]) # value of "case"
                    self.parse_result["begin_label_positions"] += [[previous_word[1], previous_word[2]]]
                elif word[0] in ["else", "default", "endcase"]: # "default" is used by case.
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0] in ["if", "for", "while", "case"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    bracket_counter = 0
                    self.return_region = "always_block"
                    self.region = "always_block_condition"
                elif word[0] in ["case"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    bracket_counter = 0
                    self.return_region = "always_block"
                    self.region = "always_block_condition"
                elif word[0]=="end":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    begin_counter -= 1
                    if begin_counter==0:
                        self.region = "declaration_region"
                        if self.debug:
                            print("jump to self.region =", self.region)
            elif self.region=="always_block_condition":
                if word[0]=="(":
                    bracket_counter += 1
                elif word[0]==")":
                    bracket_counter -= 1
                    if bracket_counter==0:
                        self.region = self.return_region
            elif self.region=="sensitivity_list":
                if word[0]==")":
                    begin_counter = 0
                    if clocked_always_block:
                        self.region = "clocked_always_block"
                    else:
                        self.region = "always_block"
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0] in ["posedge", "negedge"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    bracket_counter = 0
                    clocked_always_block = True
            elif self.region=="clocked_always_block":
                #print("clocked_always_block: word[0] =", word[0])
                if word[0]=="begin":
                    begin_counter += 1
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0] in ["else", "default", "endcase"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0] in ["if", "for", "while", "case"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    bracket_counter = 0
                    self.return_region = "clocked_always_block"
                    self.region = "always_block_condition"
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0]==":" and previous_word[0]=="begin":
                    self.region = "begin_label"
                    self.return_region = "clocked_always_block"
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0]==":":
                    signal_name = "" # The value of case must be removed from the signal_name
                    self.parse_result["begin_label_names"].append(previous_word[0]) # value of "case"
                    self.parse_result["begin_label_positions"] += [[previous_word[1], previous_word[2]]]
                elif word[0]=="end":
                    begin_counter -= 1
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    if begin_counter==0:
                        self.region = "declaration_region"
                        if self.debug:
                            print("jump to self.region =", self.region)
                elif word[0]=="<=":
                    signal_name = re.sub(r"\[.*", "", signal_name) # remove indices
                    if signal_name not in self.parse_result["clocked_signals"]:
                        self.parse_result["clocked_signals"].append(signal_name)
                        if not active_generate_conditions:
                            self.parse_result["clocked_signals_generate_conditions"].append([])
                            #print("self.parse_result[clocked_signals_generate_conditions] 0 =", self.parse_result["clocked_signals_generate_conditions"])
                        else:
                            copied_list = list(active_generate_conditions)
                            self.parse_result["clocked_signals_generate_conditions"].append(copied_list)
                            #print("self.parse_result[clocked_signals_generate_conditions] 1 =", self.parse_result["clocked_signals_generate_conditions"])
                    signal_name = ""
                    self.region = "clocked_statement"
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    signal_name += word[0]
            elif self.region=="clocked_statement":
                if word[0]==";":
                    self.region = "clocked_always_block"
            elif self.region=="generate_block":
                bracket_counter = 0
                if word[0] in ["if"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "generate_if_condition"
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0] in ["for"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "generate_for_condition"
                    if self.debug:
                        print("jump to self.region =", self.region)
                elif word[0] in ["case"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "generate_case_condition"
                    if self.debug:
                        print("jump to self.region =", self.region)
            elif self.region=="generate_if_condition":
                generate_if_condition_string += word[0]
                if word[0]=='(':
                    bracket_counter += 1
                elif word[0]==')':
                    bracket_counter -= 1
                    if bracket_counter==0:
                        active_generate_conditions.append(generate_if_condition_string)
                        self.region = "generate_begin"
                        if self.debug:
                            print("jump to self.region =", self.region)
            elif self.region=="generate_for_condition":
                generate_if_condition_string += word[0]
                if word[0]=='(':
                    bracket_counter += 1
                elif word[0]==')':
                    bracket_counter -= 1
                    if bracket_counter==0:
                        active_generate_conditions.append(generate_for_condition_string)
                        self.region = "generate_begin"
                        if self.debug:
                            print("jump to self.region =", self.region)
            elif self.region=="generate_case_condition":
                generate_if_condition_string += word[0]
                if word[0]=='(':
                    bracket_counter += 1
                elif word[0]==')':
                    bracket_counter -= 1
                    if bracket_counter==0:
                        active_generate_conditions.append(generate_case_condition_string)
                        self.region = "generate_begin"
                        if self.debug:
                            print("jump to self.region =", self.region)
            elif self.region=="generate_begin":
                if word[0]=="begin":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "declaration_region"
                    if self.debug:
                        print("jump to self.region =", self.region)
            elif self.region=="begin_label":
                if word[0] not in ["", " ", "\n", "\r", "\t"]:
                    self.parse_result["begin_label_names"].append(word[0])
                    self.parse_result["begin_label_positions"] += [[word[1], word[2]]]
                    self.region = self.return_region
                    if self.debug:
                        print("jump to self.region =", self.region)
            if word[0] not in ["", " ", "\n", "\r", "\t"]:
                previous_word = word

        parameter_definition = re.sub("^\n"      , "", parameter_definition) # remove empty lines
        parameter_definition = re.sub(r"(?m)^\s*", "", parameter_definition) # remove leading blanks, multiline flag is set
        self.parse_result["parameter_definition"]  = parameter_definition
        self.parse_result["data_type"           ]  = []
        self.parse_result["data_type"           ] += self.parse_result["port_interface_types"]
        self.parse_result["data_type_positions" ]  = []
        self.parse_result["data_type_positions" ] += self.parse_result["port_interface_types_positions"]

    def get_positions(self, tag_name):
        return self.parse_result[tag_name]

    def get(self, tag_name):
        if tag_name in self.parse_result:
            # if tag_name=="clocked_signals_generate_conditions":
            #     print("return value =", self.parse_result["clocked_signals_generate_conditions"])
            return self.parse_result[tag_name]
        print("VHDL-Parsing: did not find tag ", tag_name)
        return ""
