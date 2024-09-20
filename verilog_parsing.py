"""
Verilog Parser
"""
import re

class VerilogParser():
    tag_list = (
        "comment"                 ,
        "entity_name"             ,
        "keyword"                 ,
        "label"                   ,
        "data_type"               ,
        "port_interface_direction"
        )
    def __init__(self, verilog, region="module"):
        self.verilog = verilog.lower()
        self.region  = region
        length       = len(self.verilog)
        reg_ex_list_for_splitting_into_words = [
                       #re.compile(r"$"),
                       re.compile(r"\("),
                       re.compile(r"\)"),
                       re.compile(r"\["),
                       re.compile(r"\]"),
                       re.compile(r"#"),
                       re.compile(r";"),
                       re.compile(r":"),
                       re.compile(r"="),
                       re.compile(r"<"),
                       re.compile(r">"),
                       re.compile(r","),
                       re.compile(r"//.*\n"),
                       re.compile(r"(?s)/\*.*\*/"), # Multiline comment. (?s) = Extension notation, 's' means '.' matches all, this means also newline characters.
                       re.compile(r"[ \n\r\t]|$") # White space: Blank, Return, Linefeed, Tabulator or String-End
                      ]
        self.number_of_characters_read = 0
        word_list = []
        while self.number_of_characters_read<length:
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
        self.parse_result["label_names"                                    ] = []
        self.parse_result["label_positions"                                ] = []
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
        for word in word_list:
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
            elif self.region=="module_name":
                if word[0]=="#":
                    self.region = "parameter_list_region"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]=="(":
                    self.region = "port_region"
                elif word[0]==";":
                    self.region = "declaration_region"
                elif word[0] not in ["", " ", "\n", "\r", "\t"]: # Jump over whitespaces
                    self.parse_result["entity_name"] = word[0]
                    self.parse_result["entity_name_positions"] += [[word[1], word[2]]]
            elif self.region=="parameter_list_region":
                if word[0]=="(":
                    self.region = "parameter_region"
            elif self.region=="parameter_region":
                if word[0]=="parameter":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "parameter_list"
            elif self.region=="parameter_list":
                if word[0]=="=":
                    self.region = "parameter_value"
                    parameter_value = ""
                    parameter_value_position = [0, 0]
                elif word[0]=="[":
                    self.region = "parameter_range"
                    parameter_range = "["
                elif word[0] not in ["", " ", "\n", "\r", "\t"]: # Jump over whitespaces
                    self.parse_result["generics_interface_names"].append(word[0])
                    self.parse_result["generics_interface_names_positions"].append([word[1], word[2]])
                    self.parse_result["generics_interface_ranges"].append("") # Default value, as a parameter must not have a range.
            elif self.region=="parameter_range":
                if word[0]=="]":
                    self.region = "parameter_list"
                    self.parse_result["generics_interface_ranges"][-1] = parameter_range + ']'
                else:
                    parameter_range += word[0]
            elif self.region=="parameter_value":
                if word[0]==")": # This is the last bracket which closes the parameter declaration.
                    self.region = "module_name"
                    self.parse_result["generics_interface_init"].append(parameter_value)
                    self.parse_result["generics_interface_init_positions"].append(parameter_value_position)
                elif word[0]==",":
                    self.parse_result["generics_interface_init"].append(parameter_value)
                    self.parse_result["generics_interface_init_positions"].append(parameter_value_position)
                    self.region = "parameter_list"
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
                elif word[0]==',':
                    self.region = "port_region"
                elif word[0]==')':
                    self.region = "module_name"
                elif word[0] not in ["", " ", "\n", "\r", "\t"]: # Jump over whitespaces
                    self.parse_result["port_interface_names"          ].append(word[0])
                    self.parse_result["port_interface_names_positions"].append([word[1], word[2]])
            elif self.region=="port_range_region":
                if word[0]=="]":
                    self.region = "port_declaration"
                    self.parse_result["port_interface_ranges"][-1] = port_range + ']'
                else:
                    port_range += word[0]
            elif self.region=="declaration_region":
                if word[0]=="endmodule":
                    self.region = "module"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0] in ["wire", "reg", "localparam", "always", "posedge", "negedge", "if", "begin", "end", "else", ]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]

        parameter_definition = re.sub("^\n"      , "", parameter_definition) # remove empty lines
        parameter_definition = re.sub(r"(?m)^\s*", "", parameter_definition) # remove leading blanks, multiline flag is set
        self.parse_result["parameter_definition"]  = parameter_definition
        self.parse_result["data_type"           ]  = []
        self.parse_result["data_type"           ] += self.parse_result["port_interface_types"]
        self.parse_result["data_type_positions" ]  = []
        self.parse_result["data_type_positions" ] += self.parse_result["port_interface_types_positions"]

    def get_positions(self, tag_name):
        return self.parse_result[tag_name + "_positions"]

    def get(self, tag_name):
        return self.parse_result[tag_name]
