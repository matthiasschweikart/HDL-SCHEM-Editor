"""
This class takes a VHDL string (as first parameter) and creates a Python dictionary containing some information about the VHDL string.
In order to be able to parse the VHDL string, the string must be classified, before the parser can interprete it.
This is done by the second parameter, which may have one of these values:
"entity_context" (used for entity, architecture, package, configuration)
"generics"
"ports"
"entity_generic_declaration_region"
"architecture_declarative_region"
"architecture_statements_region"
The created dictionary can be accessed by these methods:
get_positions():
This method can be called with one of the keywords defined in "VhdlParser.tag_position_list" (see below) and
will return a list of positions of all elements specified by the argument,
where each position is a list consisting of a start-index and an end-index in the parsed VHDL-string.
get():
This method can be called with one of the keywords defined in "VhdlParser.tag_position_list" and will return
a tuple of strings, containing all elements included in the VHDL string specified by the argument.
Additionally it can be called with this other argument:
"generic_definition"
"""

import re
class VhdlParser():
    # For each element of tag_list a different format (font, color) can be defined.
    tag_position_list = (
        "comment_positions"                           ,
        "keyword_positions"                           ,
        "entity_library_name_positions"               ,
        "entity_package_name_positions"               ,
        "architecture_library_name_positions"         ,
        "architecture_package_name_positions"         ,
        "entity_name_positions"                       ,
        "architecture_name_positions"                 ,
        "entity_name_used_in_architecture_positions"  ,
        "generics_interface_names_positions"          ,
        "generics_interface_init_positions"           ,
        "port_interface_names_positions"              ,
        "port_interface_direction_positions"          ,
        "port_interface_init_positions"               ,
        "component_port_interface_names_positions"    ,
        "component_port_interface_init_positions"     ,
        "component_port_interface_direction_positions",
        "component_generic_interface_names_positions" ,
        "component_generic_interface_init_positions"  ,
        "procedure_interface_names_positions"         ,
        "function_interface_names_positions"          ,
        "data_type_positions"                         ,# includes all types (for highlighting) which can also be accessed directly by:
                                                       # "type_names", "port_interface_types", "generics_interface_types",
                                                       # "component_port_interface_types", "component_generic_interface_types",
                                                       # "procedure_interface_types", "function_interface_types",
                                                       # "function_return_types", "process_locals_data_types"
        "label_positions"
        )
    def __init__(self, vhdl, region="entity_context", parse_big_files=False):
        # Regions which are handled by the multiple used "interface..." regions could be defined
        # by the correct region, but an information is needed for the return region.
        # So for example "generics" is used instead of "interface_declaration" and
        # in this way the return region is clear:
        if   region=="generics":
            self.region = "interface_declaration"
            self.return_region = "generics"
        elif region=="ports":
            self.region = "interface_declaration"
            self.return_region = "port" # This string will be modified to "port_declaration", before it is used as return-region.
        elif region=="architecture_declarative_region":
            self.region = "architecture_declarative_region" # This region starts, where "signal" declarations can be put in.
            self.return_region = ""
        elif region=="architecture_body":
            self.region = "architecture_body"               # This region starts after the "begin" keyword.
            self.return_region = ""
        else:
            self.region = region
            self.return_region = ""
        self.vhdl = vhdl.lower()
        length    = len(self.vhdl)
        reg_ex_list_for_splitting_into_words = [
                    # The order is important here.
                    # For example when a "<=" is in the VHDL code, then the search for "<=" will have a match,
                    # but also the search for "<" will have a match.
                    # They both will have the same match-start index.
                    # But the match of "<=" will be "before" the match of "<" in the match list.
                    # So when the match with the smallest match index is searched, the match index of "<=" will
                    # be stored as the smallest match and as the match-index of "<" is equal to the match-index of "<=",
                    # it cannot change the smallest match index anymore.
                       re.compile(r"\("),
                       re.compile(r"\)"),
                       re.compile(r"\n"),
                       re.compile(r"\."),
                       re.compile(r";"),
                       re.compile(r"<="),
                       re.compile(r">="),
                       re.compile(r"=>"),
                       re.compile(r":="),
                       re.compile(r":"),
                       re.compile(r"="),
                       re.compile(r"<"),
                       re.compile(r">"),
                       re.compile(r","),
                       re.compile(r"'"),
                       re.compile(r"--.*(\n|$)"),
                       re.compile(r"[ \n\r\t]|$") # White space: Blank, Return, Linefeed, Tabulator or String-End
                      ]
        self.number_of_characters_read = 0
        word_list = []
        while self.number_of_characters_read<length and (self.number_of_characters_read<100000 or parse_big_files):
            # data_word1 contains the characters from index 0 to the string searched for.
            # data_word2 contains the string searched for.
            data_word1, data_word2 = self._get_next_words(reg_ex_list_for_splitting_into_words)
            word_list.append(data_word1)
            word_list.append(data_word2)
        self.parse_result = {}
        self.parse_result["keyword_positions"                              ] = []
        self.parse_result["comment"                                        ] = []
        self.parse_result["comment_positions"                              ] = []
        self.parse_result["entity_library_name"                            ] = []
        self.parse_result["entity_library_name_positions"                  ] = []
        self.parse_result["entity_package_name"                            ] = []
        self.parse_result["entity_package_name_positions"                  ] = []
        self.parse_result["architecture_library_name"                      ] = []
        self.parse_result["architecture_library_name_positions"            ] = []
        self.parse_result["architecture_package_name"                      ] = []
        self.parse_result["architecture_package_name_positions"            ] = []
        self.parse_result["architecture_type_declarations"                 ] = [] # Contains a list of all type definitions found in the architecture declarative part.
        self.parse_result["entity_name"                                    ] = ""
        self.parse_result["entity_name_positions"                          ] = []
        self.parse_result["architecture_name"                              ] = ""
        self.parse_result["package_name"                                   ] = ""
        self.parse_result["architecture_name_positions"                    ] = []
        self.parse_result["entity_name_used_in_architecture"               ] = ""
        self.parse_result["entity_name_used_in_architecture_positions"     ] = []
        self.parse_result["type_names"                                     ] = []
        self.parse_result["type_name_positions"                            ] = []
        self.parse_result["component_names"                                ] = []
        self.parse_result["component_name_positions"                       ] = []
        self.parse_result["procedure_names"                                ] = []
        self.parse_result["procedure_name_positions"                       ] = []
        self.parse_result["function_names"                                 ] = []
        self.parse_result["function_name_positions"                        ] = []
        self.parse_result["function_return_types"                          ] = []
        self.parse_result["function_return_types_positions"                ] = []
        self.parse_result["procedure_interface_names"                      ] = []
        self.parse_result["procedure_interface_names_positions"            ] = []
        self.parse_result["procedure_interface_direction"                  ] = []
        self.parse_result["procedure_interface_direction_positions"        ] = []
        self.parse_result["procedure_interface_types"                      ] = []
        self.parse_result["procedure_interface_types_positions"            ] = []
        self.parse_result["procedure_interface_ranges"                     ] = []
        self.parse_result["procedure_interface_constraints"                ] = []
        self.parse_result["procedure_interface_init"                       ] = []
        self.parse_result["procedure_interface_init_positions"             ] = []
        self.parse_result["procedure_interface_init_range"                 ] = []
        self.parse_result["function_interface_names"                       ] = []
        self.parse_result["function_interface_names_positions"             ] = []
        self.parse_result["function_interface_direction"                   ] = []
        self.parse_result["function_interface_direction_positions"         ] = []
        self.parse_result["function_interface_types"                       ] = []
        self.parse_result["function_interface_types_positions"             ] = []
        self.parse_result["function_interface_ranges"                      ] = []
        self.parse_result["function_interface_constraints"                 ] = []
        self.parse_result["function_interface_init"                        ] = []
        self.parse_result["function_interface_init_positions"              ] = []
        self.parse_result["function_interface_init_range"                  ] = []
        self.parse_result["port_interface_names"                           ] = []
        self.parse_result["port_interface_names_positions"                 ] = []
        self.parse_result["port_interface_direction"                       ] = []
        self.parse_result["port_interface_direction_positions"             ] = []
        self.parse_result["port_interface_types"                           ] = []
        self.parse_result["port_interface_types_positions"                 ] = []
        self.parse_result["port_interface_ranges"                          ] = []
        self.parse_result["port_interface_constraints"                     ] = []
        self.parse_result["port_interface_init"                            ] = []
        self.parse_result["port_interface_init_positions"                  ] = []
        self.parse_result["port_interface_init_range"                      ] = []
        self.parse_result["generics_interface_names"                       ] = []
        self.parse_result["generics_interface_names_positions"             ] = []
        self.parse_result["generics_interface_direction"                   ] = []
        self.parse_result["generics_interface_direction_positions"         ] = []
        self.parse_result["generics_interface_types"                       ] = []
        self.parse_result["generics_interface_types_positions"             ] = []
        self.parse_result["generics_interface_ranges"                      ] = []
        self.parse_result["generics_interface_constraints"                 ] = []
        self.parse_result["generics_interface_init"                        ] = []
        self.parse_result["generics_interface_init_positions"              ] = []
        self.parse_result["generics_interface_init_range"                  ] = []
        self.parse_result["component_port_interface_names"                 ] = []
        self.parse_result["component_port_interface_names_positions"       ] = []
        self.parse_result["component_port_interface_direction"             ] = []
        self.parse_result["component_port_interface_direction_positions"   ] = []
        self.parse_result["component_port_interface_types"                 ] = []
        self.parse_result["component_port_interface_types_positions"       ] = []
        self.parse_result["component_port_interface_ranges"                ] = []
        self.parse_result["component_port_interface_constraints"           ] = []
        self.parse_result["component_port_interface_init"                  ] = []
        self.parse_result["component_port_interface_init_positions"        ] = []
        self.parse_result["component_port_interface_init_range"            ] = []
        self.parse_result["component_generic_interface_names"              ] = []
        self.parse_result["component_generic_interface_names_positions"    ] = []
        self.parse_result["component_generic_interface_direction"          ] = []
        self.parse_result["component_generic_interface_direction_positions"] = []
        self.parse_result["component_generic_interface_types"              ] = []
        self.parse_result["component_generic_interface_types_positions"    ] = []
        self.parse_result["component_generic_interface_ranges"             ] = []
        self.parse_result["component_generic_interface_constraints"        ] = []
        self.parse_result["component_generic_interface_init"               ] = []
        self.parse_result["component_generic_interface_init_positions"     ] = []
        self.parse_result["component_generic_interface_init_range"         ] = []
        self.parse_result["process_locals_data_types"                      ] = []
        self.parse_result["label_names"                                    ] = []
        self.parse_result["label_positions"                                ] = []
        self.parse_result["instance_types"                                 ] = []
        self.parse_result["configuration_instance_names"                   ] = []
        self.parse_result["configuration_module_names"                     ] = []
        self.parse_result["configuration_target_libraries"                 ] = []
        self.parse_result["configuration_target_modules"                   ] = []
        self.parse_result["configuration_target_architectures"             ] = []
        self.parse_result["signal_constant_variable_names"                 ] = []
        self.parse_result["signal_constant_variable_types"                 ] = []
        self.parse_result["signal_constant_variable_ranges"                ] = []
        self.parse_result["clocked_signals"                                ] = []
        self.parse_result["clocked_signals_generate_conditions"            ] = [] # Contains a list of conditions for each element of self.parse_result["clocked_signals")
        self.architecture_declarations = ""
        self.architecture_body         = ""
        self._analyze(word_list)

    def _get_next_words(self, reg_ex_list_for_splitting_into_words):
        match_list = []
        for reg_ex in reg_ex_list_for_splitting_into_words:
            match = reg_ex.search(self.vhdl)
            if match is not None:
                match_list.append(match)
        if len(match_list)==1:
            first_match = match_list[0]
        else:
            index_of_first_match = len(self.vhdl)
            for match in match_list:
                if match.start()<index_of_first_match:
                    first_match          = match
                    index_of_first_match = match.start()
        start_index_of_word_before_search_string = self.number_of_characters_read
        end_index_of_word_before_search_string   = self.number_of_characters_read + first_match.start()
        start_index_of_search_string_match       = end_index_of_word_before_search_string
        end_index_of_search_string_match         = self.number_of_characters_read + first_match.end()
        word1 = self.vhdl[0:first_match.start()]
        word2 = self.vhdl[first_match.start():first_match.end()]
        self.vhdl = self.vhdl[first_match.end():]
        self.number_of_characters_read = end_index_of_search_string_match
        return  [[word1, start_index_of_word_before_search_string, end_index_of_word_before_search_string], # Text
                 [word2, start_index_of_search_string_match      , end_index_of_search_string_match      ]] # Separator

    def _analyze(self, word_list):
        generic_definition = ""
        actual_library     = ""
        in_block_comment = False
        in_generate      = 0
        active_generate_conditions = []
        in_architecture_declarative_region = False
        in_architecture_body               = False
        extend_position_of_init_value      = False
        for word in word_list:
            if in_architecture_declarative_region:
                self.architecture_declarations += word[0]
            if in_architecture_body:
                self.architecture_body += word[0]
            # word[0] with value from ["", " ", "\n", "\r", "\t"] is not checked and skipped here, because especially the "returns" are needed
            # when the original VHDL code shall be extracted from all the word[0].
            # By _analyze() the VHDL is splitted up and all the single pieces are packed into self.parse_result.
            # But the generic definitions of an entity (and all the included comments) are sometimes needed in their original form.
            # So here during the parsing all peaces of the generic definition are collected and put back together.
            # Because the parsing is still in one of the relevant "interface_.." regions, when the closing bracket of the generic
            # definition is found, this closing bracket also shows in word[0] and must be excluded:
            if self.return_region=="generics" and (
                (self.region in ["interface_declaration", "interface_type", "interface_init"] and word[0]!=')') or
                 self.region in ["interface_range", "interface_init_range"]
                ):
                generic_definition += word[0]

            if word[0].startswith("/*") or in_block_comment:
                in_block_comment = True
                if word[0].startswith("*/"):
                    in_block_comment = False
                self.parse_result["comment"]           += [word[0]]
                self.parse_result["comment_positions"] += [[word[1], word[2]]]
                extend_position_of_init_value = False
            elif word[0].startswith("--"):
                self.parse_result["comment"]           += [word[0]]
                self.parse_result["comment_positions"] += [[word[1], word[2]]]
                extend_position_of_init_value = False
            elif word[0]=="\n" and extend_position_of_init_value:
                # Extending the end position of an init value (to get also the unit) ends at "return".
                # Otherwise the line-number in the "generated HDL"-tab would be included into the init-value highlighting.
                extend_position_of_init_value = False
            elif self.region=="entity_context":
                if word[0]=="library":
                    self.region = "library clause"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]=="use":
                    first_word_of_use_clause = True
                    self.region = "use clause"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]=="entity":
                    self.region = "entity_declaration_region"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]=="architecture":
                    self.region = "architecture_name_region"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]=="package":
                    self.region = "package_name_region"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="package_name_region":
                if word[0]=="body":
                    self.region = "in_package_body"
                elif word[0]=="is":
                    # From the architecture_declarative_region there is no way back to the package-region,
                    # which is not necessary, because this is only used for a single package file with not
                    # other entities, architecures following.
                    self.region = "architecture_declarative_region"
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    self.parse_result["package_name"] = word[0]
            elif self.region=="in_package_body":
                if word[0]=="body":
                    self.region = "end_of_package_body"
            elif self.region=="end_of_package_body":
                if word[0]==";":
                    self.region = "entity_context"
            elif self.region=="library clause":
                if word[0]==";":
                    self.region = "entity_context"
                elif word[0] not in [" ", "\n", "\r", "\t"]:
                    self.parse_result["entity_library_name"]           += [word[0]]
                    self.parse_result["entity_library_name_positions"] += [[word[1], word[2]]]
            elif self.region=="use clause":
                if word[0]==";":
                    self.region = "entity_context"
                elif word[0]=="all":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0] in self.parse_result["entity_library_name"]:
                    actual_library = word[0]
                    self.parse_result["entity_library_name_positions"] += [[word[1], word[2]]]
                    first_word_of_use_clause = False
                elif word[0] not in [" ", "\n", "\r", "\t"] and first_word_of_use_clause is True:
                    actual_library = word[0] # A library definition is missing in the VHDL, because word[0] is not stored in self.parse_result["entity_library_name"]
                    first_word_of_use_clause = False
                elif word[0] not in [" ", "\n", "\r", "\t", "."]:
                    self.parse_result["entity_package_name"]           += [actual_library + '.' + word[0]]
                    self.parse_result["entity_package_name_positions"] += [[word[1], word[2]]]
            elif self.region=="entity_declaration_region":
                if word[0]==";":
                    self.region = "entity_context"
                elif word[0]=="is":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "inside_entity"
                elif word[0] not in [" ", "\n", "\r", "\t"]:
                    self.parse_result["entity_name"] = word[0]
                    self.parse_result["entity_name_positions"] += [[word[1], word[2]]]
            elif self.region=="inside_entity":
                if word[0]=="generic":
                    self.region = "generics_declaration"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]=="port":
                    self.region = "port_declaration"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]=="end":
                    self.region = "entity_end"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="generics_declaration":
                if word[0]==";":
                    self.region = "inside_entity"
                elif word[0]=="(":
                    self.region = "interface_declaration"
                    self.return_region = "generics" # This string will be modified to "generics_declaration", before it is used as return-region.
            elif self.region=="port_declaration":
                if word[0]==";":
                    self.region = "inside_entity"
                elif word[0]=="(":
                    self.region = "interface_declaration"
                    self.return_region = "port" # This string will be modified to "port_declaration", before it is used as return-region.
            elif self.region=="entity_end":
                if   word[0]=="entity":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0] not in ["", " ", "\n", "\r", "\t"] and word[0]==self.parse_result["entity_name"]:
                    self.parse_result["entity_name_positions"] += [[word[1], word[2]]]
                elif word[0]==";":
                    self.region = "architecture_context"
            elif self.region=="architecture_context":
                if word[0]=="library":
                    self.region = "architecture library clause"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]=="use":
                    self.region = "architecture use clause"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]=="entity":
                    self.region = "entity_declaration_region"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]=="architecture":
                    self.region = "architecture_name_region"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="architecture library clause":
                if word[0]==";":
                    self.region = "architecture_context"
                elif word[0] not in [" ", "\n", "\r", "\t"]:
                    self.parse_result["architecture_library_name"]           += [word[0]]
                    self.parse_result["architecture_library_name_positions"] += [[word[1], word[2]]]
            elif self.region=="architecture use clause":
                if word[0]==";":
                    self.region = "architecture_context"
                elif word[0]=="all":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0] in self.parse_result["architecture_library_name"]:
                    actual_library = word[0]
                    self.parse_result["architecture_library_name_positions"] += [[word[1], word[2]]]
                elif word[0] not in [" ", "\n", "\r", "\t", "."]:
                    self.parse_result["architecture_package_name"]           += [actual_library + '.' + word[0]]
                    self.parse_result["architecture_package_name_positions"] += [[word[1], word[2]]]
            elif self.region=="architecture_name_region":
                if   word[0]=="of":
                    self.region = "entity_name_region_of_architecture"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    self.parse_result["architecture_name"] = word[0]
                    self.parse_result["architecture_name_positions"] += [[word[1], word[2]]]
            elif self.region=="entity_name_region_of_architecture":
                if   word[0]=="is":
                    self.region = "architecture_declarative_region"
                    in_architecture_declarative_region = True
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    self.parse_result["entity_name_used_in_architecture"] = word[0]
                    self.parse_result["entity_name_used_in_architecture_positions"] += [[word[1], word[2]]]
            elif self.region=="architecture_declarative_region":
                if   word[0]=="begin":
                    in_architecture_declarative_region = False
                    self.architecture_declarations = self.architecture_declarations[1:-5] # remove the first and last word ("\n" after "is", "begin" at the end).
                    in_architecture_body               = True
                    self.region = "architecture_body"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0] in ["type", "subtype"]:
                    self.region = "architecture_type_declaration"
                    architecture_type_declaration = [word[0]]
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.return_region = "architecture_declarative_region"
                elif word[0] in ["signal", "constant"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "signal_constant_variable_declaration"
                    self.return_region = "architecture_declarative_region"
                    self.parse_result["signal_constant_variable_ranges"].append("") # default value, because this info might not exist.
                elif word[0]=="procedure":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "procedure_declaration"
                    self.return_region = "architecture_declarative_region"
                elif word[0]=="function":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "function_declaration"
                    self.return_region = "architecture_declarative_region"
                elif word[0]=="component":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "component_declaration_region"
                elif word[0]=="for":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "embedded_configuration"
                    self.parse_result["configuration_instance_names"      ].append("") # default value, because this info might not exist.
                    self.parse_result["configuration_module_names"        ].append("") # default value, because this info might not exist.
                    self.parse_result["configuration_target_libraries"    ].append("") # default value, because this info might not exist.
                    self.parse_result["configuration_target_modules"      ].append("") # default value, because this info might not exist.
                    self.parse_result["configuration_target_architectures"].append("") # default value, because this info might not exist.
            elif self.region=="architecture_type_declaration":
                architecture_type_declaration.append(word[0])
                if   word[0]==";":  # When leaving by this condition, only the type-name was declared here.
                    self.parse_result["architecture_type_declarations"].append(architecture_type_declaration)
                    self.region = "architecture_declarative_region"
                elif word[0]=="is":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "architecture_type_specification"
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    self.parse_result["type_names"].append(word[0])
                    self.parse_result["type_name_positions"] += [[word[1], word[2]]]
            elif self.region=="architecture_type_specification":
                architecture_type_declaration.append(word[0])
                if   word[0]==";":
                    self.parse_result["architecture_type_declarations"].append(architecture_type_declaration)
                    self.region = "architecture_declarative_region"
                elif word[0]=="record":
                    self.region = "architecture_record_declarative_region"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]=="units":
                    self.region = "architecture_units_declarative_region"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0] in ["range", "array", "downto", "to", "access"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]=="of":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "architecture_element_subtype_region"
                elif word[0] not in ["", " ", "\n", "\r", "\t", "(", ")", "-", ".", "<", ">", ","] and not word[0].startswith(("-","0","1","2","3","4","5","6","7","8","9")):
                    self.parse_result["type_names"].append(word[0])
                    self.parse_result["type_name_positions"] += [[word[1], word[2]]]
            elif self.region=="architecture_record_declarative_region":
                architecture_type_declaration.append(word[0])
                if word[0]=="end":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "architecture_end_record_declarative_region"
                elif word[0]==":":
                    self.region = "architecture_record_member_declarative_region"
            elif self.region=="architecture_record_member_declarative_region":
                architecture_type_declaration.append(word[0])
                if word[0]==";":
                    self.parse_result["architecture_type_declarations"].append(architecture_type_declaration)
                    self.region = "architecture_record_declarative_region"
                elif word[0] not in ["", " ", "\n", "\r", "\t", "(", ")", "-", ".", "<", ">", ","] and not word[0].startswith(("-","0","1","2","3","4","5","6","7","8","9")):
                    self.parse_result["type_names"].append(word[0])
                    self.parse_result["type_name_positions"] += [[word[1], word[2]]]
                    self.region = "architecture_record_declarative_range_region"
            elif self.region=="architecture_record_declarative_range_region":
                architecture_type_declaration.append(word[0])
                if word[0]==";":
                    self.parse_result["architecture_type_declarations"].append(architecture_type_declaration)
                    self.region = "architecture_record_declarative_region"
                elif word[0] in ["downto", "to", "range"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="architecture_end_record_declarative_region":
                architecture_type_declaration.append(word[0])
                if word[0]==";":
                    self.parse_result["architecture_type_declarations"].append(architecture_type_declaration)
                    self.region = "architecture_declarative_region"
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="architecture_units_declarative_region":
                architecture_type_declaration.append(word[0])
                if word[0]=="end":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "architecture_end_units_declarative_region"
            elif self.region=="architecture_end_units_declarative_region":
                architecture_type_declaration.append(word[0])
                if word[0]==";":
                    self.parse_result["architecture_type_declarations"].append(architecture_type_declaration)
                    self.region = "architecture_declarative_region"
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="architecture_element_subtype_region":
                architecture_type_declaration.append(word[0])
                if word[0]==";":
                    self.parse_result["architecture_type_declarations"].append(architecture_type_declaration)
                    self.region = "architecture_declarative_region"
                elif word[0] not in ["", " ", "\n", "\r", "\t", "(", ")", "-", ".", "<", ">", ","] and not word[0].startswith(("-","0","1","2","3","4","5","6","7","8","9")):
                    self.parse_result["type_names"].append(word[0])
                    if word[0] in ("downto", "to"):
                        self.parse_result["type_name_positions"] += [[word[1], word[1]]] # Provide the same number of entries as in self.parse_result["type_names"]
                        self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    else:
                        self.parse_result["type_name_positions"] += [[word[1], word[2]]]
            elif self.region=="embedded_configuration":
                if word[0]==":":
                    self.region = "embedded_configuration_type"
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    self.parse_result["configuration_instance_names"][-1] = word[0]
                    self.parse_result["label_positions"] += [[word[1], word[2]]]
            elif self.region=="embedded_configuration_type":
                if word[0]=="use":
                    self.region = "embedded_configuration_rule"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    self.parse_result["configuration_module_names"][-1] = word[0]
                    self.parse_result["entity_name_positions"] += [[word[1], word[2]]]
            elif self.region=="embedded_configuration_rule":
                if word[0]=="entity":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    self.parse_result["configuration_target_libraries"][-1] = word[0]
                    self.region = "embedded_configuration_target_modules"
            elif self.region=="embedded_configuration_target_modules":
                if word[0]==";":
                    self.region = "architecture_declarative_region"
                elif word[0]=="(":
                    self.region = "embedded_configuration_target_architectures"
                elif word[0] not in ["", " ", "\n", "\r", "\t", "."]:
                    self.parse_result["configuration_target_modules"][-1] = word[0]
            elif self.region=="embedded_configuration_target_architectures":
                if word[0]==")":
                    self.region = "embedded_configuration_end"
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    self.parse_result["configuration_target_architectures"][-1] = word[0]
            elif self.region=="embedded_configuration_end":
                if word[0]==";":
                    self.region = "architecture_declarative_region"
            elif self.region=="type_declaration":
                if   word[0]==";":  # When leaving by this condition, only the type-name was declared here.
                    self.region = self.return_region
                elif word[0]=="is":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "type_specification"
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    self.parse_result["type_names"].append(word[0])
                    self.parse_result["type_name_positions"] += [[word[1], word[2]]]
            elif self.region=="type_specification":
                if   word[0]==";":
                    self.region = self.return_region
                elif word[0]=="record":
                    self.region = "record_declarative_region"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]=="units":
                    self.region = "units_declarative_region"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0] in ["range", "array", "downto", "to", "access"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]=="of":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "element_subtype_region"
                elif word[0] not in ["", " ", "\n", "\r", "\t", "(", ")", "-", ".", "<", ">", ","] and \
                     not word[0].startswith(("-","0","1","2","3","4","5","6","7","8","9")):
                    self.parse_result["type_names"].append(word[0])
                    self.parse_result["type_name_positions"] += [[word[1], word[2]]]
            elif self.region=="element_subtype_region":
                if word[0]==";":
                    self.region = self.return_region
                elif word[0] not in ["", " ", "\n", "\r", "\t", "(", ")", "-", ".", "<", ">", ","] and \
                     not word[0].startswith(("-","0","1","2","3","4","5","6","7","8","9")):
                    self.parse_result["type_names"].append(word[0])
                    self.parse_result["type_name_positions"] += [[word[1], word[2]]]
                    if word[0] in ["downto", "to"]:
                        self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="record_declarative_region":
                if word[0]=="end":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "end_record_declarative_region"
                elif word[0]==":":
                    self.region = "record_member_declarative_region"
            elif self.region=="record_member_declarative_region":
                if word[0]==";":
                    self.region = "record_declarative_region"
                elif word[0] not in ["", " ", "\n", "\r", "\t", "(", ")", "-", ".", "<", ">", ","] and not word[0].startswith(("-","0","1","2","3","4","5","6","7","8","9")):
                    self.parse_result["type_names"].append(word[0])
                    self.parse_result["type_name_positions"] += [[word[1], word[2]]]
                    self.region = "record_declarative_range_region"
            elif self.region=="record_declarative_range_region":
                if word[0]==";":
                    self.region = "record_declarative_region"
                elif word[0] in ["downto", "to", "range"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="end_record_declarative_region":
                if word[0]==";":
                    self.region = self.return_region
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="units_declarative_region":
                if word[0]=="end":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "end_units_declarative_region"
            elif self.region=="end_units_declarative_region":
                if word[0]==";":
                    self.region = self.return_region
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="signal_constant_variable_declaration":
                if word[0]==":":
                    self.region = "signal_constant_variable_declaration_type"
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    self.parse_result["signal_constant_variable_names"].append(word[0])
            elif self.region=="signal_constant_variable_declaration_type":
                if word[0]==";":
                    self.region = self.return_region
                elif word[0]=="range":
                    self.parse_result["type_name_positions"] += [[word[1], word[2]]]
                    busrange = ""
                    self.region = "signal_constant_variable_declaration_type_integer_range"
                    start_of_signal_constant_variable_declaration_type_integer_range = True
                elif word[0]=="(":
                    busrange = word[0]
                    number_of_open_brackets = 1
                    self.region = "signal_constant_variable_declaration_type_range"
                elif word[0] in [":=", ":"]: # Will only used at an initialization, where in a wrong way ':' is used instead of ":=".
                    self.region = "signal_constant_variable_init"
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    # for syntax highlighting:
                    self.parse_result["type_names"].append(word[0])
                    self.parse_result["type_name_positions"] += [[word[1], word[2]]]
                    # for getting:
                    self.parse_result["signal_constant_variable_types"].append(word[0])
            elif self.region=="signal_constant_variable_init":
                if word[0]==";":
                    self.region = self.return_region
            elif self.region=="signal_constant_variable_declaration_type_integer_range":
                if word[0]==";":
                    self.parse_result["signal_constant_variable_ranges"][-1] = busrange # Overwrite the default value
                    self.region = self.return_region
                else:
                    if start_of_signal_constant_variable_declaration_type_integer_range:
                        busrange += "range " + word[0]
                        start_of_signal_constant_variable_declaration_type_integer_range = False
                    else:
                        busrange += word[0]
            elif self.region=="signal_constant_variable_declaration_type_range":
                busrange += word[0]
                if word[0]=="(":
                    number_of_open_brackets += 1
                elif word[0]==")":
                    number_of_open_brackets -= 1
                    if number_of_open_brackets==0:
                        self.region = "signal_constant_variable_declaration_type"
                        self.parse_result["signal_constant_variable_ranges"][-1] = busrange # Overwrite the default value
                elif word[0] in ("downto", "to"):
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="component_declaration_region":
                if word[0]==";":
                    self.region = "architecture_declarative_region"
                elif word[0]=="is":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "inside_component"
                elif word[0]=="generic": # needed here for declarations with missing "is".
                    self.region = "component_generic_declaration"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]=="port": # needed here for declarations with missing "is".
                    self.region = "component_port_declaration"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    self.parse_result["component_names"].append(word[0])
                    self.parse_result["component_name_positions"] += [[word[1], word[2]]]
            elif self.region=="inside_component":
                if word[0]=="generic":
                    self.region = "component_generic_declaration"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]=="port":
                    self.region = "component_port_declaration"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]=="end":
                    self.region = "component_end"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="component_generic_declaration":
                if word[0]==";":
                    self.region = "inside_component"
                elif word[0]=="(":
                    self.region = "interface_declaration"
                    self.return_region = "component_generic" # will be modified into "component_generic_declaration"
            elif self.region=="component_port_declaration":
                if word[0]==";":
                    self.region = "inside_component"
                elif word[0]=="(":
                    self.region = "interface_declaration"
                    self.return_region = "component_port" # will be modified into "component_port_declaration"
            elif self.region=="component_end":
                if   word[0]=="component":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0] not in ["", " ", "\n", "\r", "\t"] and word[0]==self.parse_result["component_names"][-1]:
                    self.parse_result["component_name_positions"] += [[word[1], word[2]]]
                elif word[0]==";":
                    self.region = "architecture_declarative_region"
            elif self.region=="procedure_declaration": #aaa
                if   word[0]=="(":
                    #self.region = "procedure_parameter_region"
                    self.region = "interface_declaration"
                    self.return_region = "procedure" # will be modified into "procedure_declaration"
                elif word[0] == "is":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "procedure_declarative_region"
                elif word[0] == ")":
                    self.region = "architecture_declarative_region"
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    self.parse_result["procedure_names"].append(word[0])
                    self.parse_result["procedure_name_positions"] += [[word[1], word[2]]]
            elif self.region=="procedure_declarative_region":
                if   word[0]=="begin":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "sequential_statements"
                    self.return_region = "architecture_declarative_region"
                    open_if_counter = 0
                    sequential_statement_in_clocked_process = False
                elif word[0] in ["type", "subtype"]:
                    self.region = "type_declaration"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.return_region = "procedure_declarative_region"
                elif word[0] in ["constant", "variable"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "signal_constant_variable_declaration"
                    self.return_region = "procedure_declarative_region"
                    self.parse_result["signal_constant_variable_ranges"].append("") # default value, because this info might not exist.
            elif self.region=="function_declaration":
                if   word[0]=="(":
                    self.region = "interface_declaration"
                    self.return_region = "function"  # will be renamed into "function_declaration"
                elif word[0] == "return":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "function_return_type"
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    self.parse_result["function_names"].append(word[0])
                    self.parse_result["function_name_positions"] += [[word[1], word[2]]]
            elif self.region=="function_return_type":
                if   word[0]=="is":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "function_declarative_region"
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    self.parse_result["function_return_types"].append(word[0])
                    self.parse_result["function_return_types_positions"] += [[word[1], word[2]]]
            elif self.region=="function_declarative_region":
                if   word[0]=="begin":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "sequential_statements"
                    self.return_region = "architecture_declarative_region"
                    open_if_counter = 0
                    sequential_statement_in_clocked_process = False
                elif word[0] in ["type", "subtype"]:
                    self.region = "type_declaration"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.return_region = "function_declarative_region"
                elif word[0] in ["constant", "variable"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "signal_constant_variable_declaration"
                    self.return_region = "function_declarative_region"
                    self.parse_result["signal_constant_variable_ranges"].append("") # default value, because this info might not exist.
            elif self.region=="interface_declaration":    # can be reached from "procedure", "function", "port", "generics", "record definition", "component"
                if   word[0] in ["constant", "signal", "variable"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]==":":
                    self.parse_result[self.return_region + "_interface_direction"          ].append("")     # default value, because this info might not exist.
                    self.parse_result[self.return_region + "_interface_direction_positions"].append([0, 0]) # default value, because this info might not exist.
                    self.parse_result[self.return_region + "_interface_ranges"             ].append("")     # default value, because this info might not exist.
                    self.parse_result[self.return_region + "_interface_constraints"        ].append("")     # default value, because this info might not exist.
                    self.parse_result[self.return_region + "_interface_init"               ].append("")     # default value, because this info might not exist.
                    self.parse_result[self.return_region + "_interface_init_positions"     ].append([0,0])  # default value, because this info might not exist.
                    self.parse_result[self.return_region + "_interface_init_range"         ].append("")     # default value, because this info might not exist.
                    self.region = "interface_type"
                    type_is_stored = False # initialize
                elif word[0]==")": # This is the last bracket which closes the interface declaration.
                    self.extend_parse_result_for_name_list()
                    self.region = self.return_region + "_declaration"
                elif word[0] not in ["", " ", "\n", "\r", "\t", ',']:
                    self.parse_result[self.return_region + "_interface_names"].append(word[0])
                    self.parse_result[self.return_region + "_interface_names_positions"] += [[word[1], word[2]]]
            elif self.region=="interface_type":
                #print("interface_type: word[0] =", '|' + word[0] + '|')
                if word[0] in ["in", "out", "inout"]:
                    self.parse_result[self.return_region + "_interface_direction"          ][-1] = word[0] # replace the defaults
                    self.parse_result[self.return_region + "_interface_direction_positions"][-1] = [word[1], word[2]]
                elif word[0]=="(":
                    self.region = "interface_range"
                    busrange = "("
                    use_as_bus_range = True
                    number_of_words_in_range = 0
                    number_of_open_brackets  = 1
                    number_of_close_brackets = 0
                elif word[0] in [":=", ":"]: # Will only used at an initialization, where in a wrong way ':' is used instead of ":=".
                    self.region = "interface_init"
                    start_of_interface_init = True
                elif word[0]==")": # This is the last bracket which closes the interface declaration.
                    self.extend_parse_result_for_name_list()
                    self.region = self.return_region + "_declaration"
                elif word[0]==";": # This is the end of one interface definition, a next interface definition is following.
                    self.extend_parse_result_for_name_list()
                    self.region = "interface_declaration"
                elif word[0] in ["downto", "to"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]=="range":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "interface_range_range"
                    start_of_interface_range_range = True
                    number_of_open_brackets_in_interface_range_range = 0
                    busrange = ""
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    if not type_is_stored:
                        self.parse_result[self.return_region + "_interface_types"          ].append(word[0])
                        self.parse_result[self.return_region + "_interface_types_positions"].append([word[1], word[2]])
                        type_is_stored = True
            elif self.region=="interface_range":
                number_of_words_in_range += 1
                busrange += word[0]
                if word[0]=="(":
                    number_of_open_brackets += 1
                    if number_of_words_in_range==2:
                        # The range starts with: "( <name> (..."
                        # This means that this is not a range of the signal, but the range of a unconstrained array in a record.
                        use_as_bus_range = False
                elif word[0]==")":
                    if number_of_close_brackets!=number_of_open_brackets-1:
                        number_of_close_brackets += 1
                    else:
                        if use_as_bus_range:
                            busconstraint = ""
                        else:
                            busconstraint = busrange
                            busrange = ""
                        if self.parse_result[self.return_region + "_interface_ranges"][-1]=="":
                            self.parse_result[self.return_region + "_interface_ranges"][-1] = busrange # Overwrite the default value.
                        else: # There are several pairs of brackets.
                            self.parse_result[self.return_region + "_interface_ranges"][-1] += busrange # Append the next value
                        if self.parse_result[self.return_region + "_interface_constraints"][-1]=="":
                            self.parse_result[self.return_region + "_interface_constraints"][-1] = busconstraint # Overwrite the default value.
                        else: # There are several pairs of brackets.
                            self.parse_result[self.return_region + "_interface_constraints"][-1] += busconstraint # Append the next value
                        self.region = "interface_type"
                        type_is_stored = False
                elif word[0] in ("downto", "to"):
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="interface_range_range": # This is a range which did not start with a bracket but the keyword "range".
                if word[0]=="(": # Not part of the if-elif structure below, as "(" must be put in busrange below.
                    number_of_open_brackets_in_interface_range_range += 1
                if word[0]==")" and number_of_open_brackets_in_interface_range_range==0: # This is the last bracket which closes the interface declaration.
                    self.extend_parse_result_for_name_list()
                    self.region = self.return_region + "_declaration"
                    #print("interface_range_range nach ): busrange =", busrange)
                elif word[0]==";": # This is the end of a range definition ("range 0 to 7"), a next interface definition is following.
                    self.extend_parse_result_for_name_list()
                    self.region = "interface_declaration"
                elif word[0] in [":=", ":"]: # Will only used at an initialization, where in a wrong way ':' is used instead of ":=".
                    self.region = "interface_init"
                    start_of_interface_init = True
                else:
                    if start_of_interface_range_range:
                        busrange += "range" + word[0]
                        start_of_interface_range_range = False
                    else:
                        busrange += word[0]
                    # Overwrite at once, because it might be that instead of ')',';',':' no next word arrives (when only a VHDL fragment is analyzed)
                    self.parse_result[self.return_region + "_interface_ranges"][-1] = busrange # Overwrite the default value.
                if word[0]==")": # Not part of the if-elif structure above, as ")" must be put in busrange above.
                    number_of_open_brackets_in_interface_range_range -= 1
            elif self.region=="interface_init":
                if word[0]==";":
                    self.extend_parse_result_for_name_list()
                    self.region = "interface_declaration"
                elif word[0]=="(":
                    busrange = "("
                    number_of_open_brackets = 1
                    number_of_close_brackets = 0
                    self.region = "interface_init_range"
                elif word[0]==")": # This is the last bracket which closes the interface declaration.
                    self.extend_parse_result_for_name_list()
                    self.region = self.return_region + "_declaration"
                else: # because time units must be kept (and could be placed in the next line), all contents of word[0] must be accepted.
                    self.parse_result[self.return_region + "_interface_init"][-1] += word[0] # append at the default value "".
                    if start_of_interface_init:
                        self.parse_result[self.return_region + "_interface_init_positions"][-1] = [word[1], word[2]]
                        start_of_interface_init = False
                        extend_position_of_init_value = True
                    elif extend_position_of_init_value:
                        # Extend the _interface_init_positions with each new word (even with blanks) to get also units into the init-value-highlighting.
                        # This causes problems because there might be a comment (at the end of the line) in the stream of word[0]-elements.
                        # This comment splits the init value in 2 or more parts, if the init value is continued in the next line (after the comment).
                        # These additional parts are ignored and not highlighted by the use of the variable extend_position_of_init_value:
                        # When a comment or a return is found, then the variable extend_position_of_init_value is set to false.
                        self.parse_result[self.return_region + "_interface_init_positions"][-1][1] = word[2]
            elif self.region=="interface_init_range":
                busrange += word[0]
                if word[0]=="(":
                    number_of_open_brackets += 1
                elif word[0]==")":
                    if number_of_close_brackets!=number_of_open_brackets-1:
                        number_of_close_brackets += 1
                    else:
                        self.parse_result[self.return_region + "_interface_init_range"][-1] = busrange # Overwrite the default value.
                        self.region = "interface_type"
                        type_is_stored = False
            elif self.region=="sequential_statements": # "begin"  in process, function, procedure has been found.
                if word[0]=="end":
                    #print("end wird markiert", word[0])
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "sequential_statements_end" # Check for "end process"
                elif word[0] in ["wait"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "sequential_statement_wait_statement"
                elif word[0] in ["if", "elsif"]:
                    if word[0]=="if":
                        open_if_counter += 1
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "sequential_statement_if_condition"
                elif word[0] in ["for", "while"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "sequential_statement_loop_condition"
                elif word[0] in ["case"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "sequential_statement_case_condition"
                elif word[0] in ["when"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "sequential_statement_case_when"
                elif word[0] in ["else", "downto", "to", "after",
                                 "or", "and", "xor", "nor", "nand", "not", "rem",
                                 "others", "note", "warning", "error", "failure",
                                 "severity", "null"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0] in ["exit", "continue", "break", "return", "assert", "report"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "sequential_statement_wait_for_semicolon"
                elif word[0] not in ["", " ", "\n", "\r", "\t", ";"]: # Label oder Signal (";" is checked here, because "null;" is a valid statement)
                    self.region = "sequential_statement_after_label/signalname"
            elif self.region=="sequential_statement_after_label/signalname":
                if word[0]=='(': # previous word was a signalname with a range
                    if sequential_statement_in_clocked_process and previous_word[0] not in self.parse_result["clocked_signals"]:
                        self.parse_result["clocked_signals"].append(previous_word[0])
                        if not active_generate_conditions:
                            self.parse_result["clocked_signals_generate_conditions"].append([])
                        else:
                            copied_list = list(active_generate_conditions)
                            self.parse_result["clocked_signals_generate_conditions"].append(copied_list)
                    self.region = "sequential_statement_wait_for_semicolon"
                elif word[0]==':':
                    self.parse_result["label_names"].append(previous_word[0])
                    self.parse_result["label_positions"] += [[previous_word[1], previous_word[2]]]
                    self.region = "sequential_statement_signal_name"
                elif word[0] in ["<=", ":="]: # previous word was a signalname
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    if sequential_statement_in_clocked_process and previous_word[0] not in self.parse_result["clocked_signals"]:
                        self.parse_result["clocked_signals"].append(previous_word[0])
                        if not active_generate_conditions:
                            self.parse_result["clocked_signals_generate_conditions"].append([])
                        else:
                            copied_list = list(active_generate_conditions)
                            self.parse_result["clocked_signals_generate_conditions"].append(copied_list)
                    self.region = "sequential_statement_wait_for_semicolon"
                elif word[0] not in ["", " ", "\n", "\r", "\t"]: # No label, no assignment, so it must be a signalname
                    if sequential_statement_in_clocked_process and word[0] not in self.parse_result["clocked_signals"]:
                        self.parse_result["clocked_signals"].append(word[0])
                        if not active_generate_conditions:
                            self.parse_result["clocked_signals_generate_conditions"].append([])
                        else:
                            copied_list = list(active_generate_conditions)
                            self.parse_result["clocked_signals_generate_conditions"].append(copied_list)
                    self.region = "sequential_statement_before_assignment"
            elif self.region=="sequential_statement_before_assignment":
                if word[0]=='<=':
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "sequential_statement_wait_for_semicolon"
                elif word[0] in ("downto", "to", "null"):
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="sequential_statement_wait_for_semicolon":
                if word[0]==';':
                    self.region = "sequential_statements"
                elif word[0] in ("downto", "to", "others"):
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="sequential_statement_signal_name":
                if sequential_statement_in_clocked_process:
                    #print("clocked signal =", word[0])
                    if word[0] not in self.parse_result["clocked_signals"]:
                        self.parse_result["clocked_signals"].append(word[0])
                        if not active_generate_conditions:
                            self.parse_result["clocked_signals_generate_conditions"].append([])
                        else:
                            copied_list = list(active_generate_conditions)
                            self.parse_result["clocked_signals_generate_conditions"].append(copied_list)
                self.region = "sequential_statement_after_signal_name"
            elif self.region=="sequential_statement_after_signal_name":
                if word[0]==';':
                    self.region = "sequential_statements"
                elif word[0]=='<=':
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="sequential_statement_wait_statement":
                if word[0] in ["for", "until"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]==';':
                    self.region = "sequential_statements"
            elif self.region=="sequential_statement_if_condition":
                if word[0] in ["then"]:
                    #print("then found after:", previous_word[0])
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "sequential_statements"
                elif word[0] in ["event", "rising_edge", "falling_edge"]:
                    sequential_statement_in_clocked_process = True
                elif word[0] in ["not", "or", "and", "rem", "mod", "downto", "to"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="sequential_statement_loop_condition":
                if word[0] in ["loop"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "sequential_statements"
                elif word[0] in ["in", "downto", "to", "range"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="sequential_statement_case_condition":
                if word[0] in ["is"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "sequential_statements"
            elif self.region=="sequential_statement_case_when":
                if word[0] in ["=>"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "sequential_statements"
                elif word[0] in ["others"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="sequential_statements_end":
                if word[0] in ["if"]: # This hit is from "end if".
                    #print("if of end if found")
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "sequential_statements_wait_for_semicolon"
                    open_if_counter -= 1
                    if open_if_counter==0:
                        sequential_statement_in_clocked_process = False
                elif word[0] in ["case", "loop"]: # These hits are from "end case"/"end loop"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "sequential_statements_wait_for_semicolon"
                elif word[0] in ["process", "function", "procedure"]: # These hits are from "end process/function/procedure;".
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]==";": # This semicolon has followed "end process/function/procedure, sometimes with a name inbetween "end [<name>];"
                    self.region = self.return_region
            elif self.region=="sequential_statements_wait_for_semicolon":
                self.region = "sequential_statements"
            elif self.region=="architecture_body":
                if word[0]=="process":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "process" # A process may have no label.
                elif word[0]=="with":
                    self.region = "with_selector"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0] in ["note","warning","error","failure","report","assert","severity"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0] in ["<=", ":="]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "inlineprocess"
                elif word[0]==":":
                    self.parse_result["label_names"].append(previous_word[0])
                    self.parse_result["label_positions"] += [[previous_word[1], previous_word[2]]]
                    self.region = "process_or_instance_or_generate" # A generate and an instance must have a label
                elif word[0]=="end":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    if in_generate==0:
                        self.region = "architecture_body_end"
                        in_architecture_body = False
                        self.architecture_body = self.architecture_body[1:-3] # remove the first and last word ("\n" after "begin", "end" at the end).
                    else:
                        self.region = "generate_end"
                        in_generate -= 1
            elif self.region=="generate_end":
                #print("generate_end: in_generate =", in_generate)
                if word[0]=="generate":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]==";":
                    self.region = "architecture_body"
                    del active_generate_conditions[-1]
            elif self.region=="with_selector":
                if word[0]=="select":
                    self.region = "with_assignment"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="with_assignment":
                if word[0]=="<":
                    self.region = "with_alternative"
            elif self.region=="with_alternative":
                if word[0]=="when":
                    self.region = "with_condition"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="with_condition":
                if word[0]==",":
                    self.region = "with_alternative"
                elif word[0]==";":
                    self.region = "architecture_body"
                elif word[0]=="others":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="process_or_instance_or_generate":
                if  word[0]=="process":
                    self.region = "process"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.parse_result["instance_types"].append("process")
                elif word[0] in ["for"]:
                    self.region = "for_generate"
                    in_generate += 1
                    generate_if_condition_string = ""
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0] in ["if"]:
                    self.region = "if_generate"
                    in_generate += 1
                    generate_if_condition_string = ""
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]=="entity":
                    self.region = "instance_configuration_library"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    self.parse_result["instance_types"].append(word[0])
                    self.region = "instance"
            elif self.region=="instance_configuration_library":
                if word[0]==".":
                    self.region = "instance_configuration_module_name"
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    self.parse_result["configuration_instance_names"      ].append(self.parse_result["label_names"][-1])
                    self.parse_result["configuration_target_libraries"    ].append(word[0])
                    self.parse_result["configuration_target_architectures"].append("") # default value, because this info might not exist.
            elif self.region=="instance_configuration_module_name":
                if word[0]=="(":
                    self.region = "instance_configuration_architecture_name"
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    self.parse_result["instance_types"].append(word[0])
                    self.parse_result["configuration_module_names"        ].append(word[0])
                    self.parse_result["configuration_target_modules"      ].append(word[0])
                    self.region = "instance"
            elif self.region=="instance_configuration_architecture_name":
                if word[0]==")":
                    self.region = "instance"
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    self.parse_result["configuration_target_architectures"][-1] = word[0]
            elif self.region=="for_generate":
                if  word[0]=="generate":
                    self.region = "architecture_body"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    active_generate_conditions.append(generate_if_condition_string)
                elif word[0] not in ["", "\n", "\r", "\t"]: # Blanks must be put into generate_if_condition_string to keep "and", "or", "not" separated.
                    generate_if_condition_string += word[0]
            elif self.region=="if_generate":
                if  word[0]=="generate":
                    self.region = "architecture_body"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    active_generate_conditions.append(generate_if_condition_string)
                elif word[0] not in ["", "\n", "\r", "\t"]: # Blanks must be put into generate_if_condition_string to keep "and", "or", "not" separated.
                    generate_if_condition_string += word[0]
            elif self.region=="instance":
                if  word[0] in ["port", "generic"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif  word[0]=="map":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "map"
                elif  word[0]==";":
                    self.region = "architecture_body"
            elif self.region=="map":
                if  word[0]=="(":
                    self.region = "connections"
            elif self.region=="connections":
                if word[0]=="open":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]=="(":
                    number_of_open_brackets = 1
                    number_of_close_brackets = 0
                    self.region = "range_in_map"
                elif word[0]==")":
                    self.region = "instance"
            elif self.region=="range_in_map":
                if word[0]=="(":
                    number_of_open_brackets += 1
                elif word[0]==")":
                    if number_of_close_brackets!=number_of_open_brackets-1:
                        number_of_close_brackets += 1
                    else:
                        self.region = "connections"
            elif self.region=="inlineprocess":
                if  word[0]==";":
                    self.region = "architecture_body"
                elif word[0]=="rem":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="process":
                if  word[0]=="(":
                    self.region = "sensitivity_list"
                elif word[0]=="begin":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.return_region = "architecture_body"
                    self.region = "sequential_statements"
                    open_if_counter = 0
                    sequential_statement_in_clocked_process = False
                elif word[0] in ["signal", "variable", "constant"]:
                    self.region = "process_local_declaration"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="sensitivity_list":
                if word[0]=="(":
                    number_of_open_brackets = 1
                    number_of_close_brackets = 0
                    self.region = "range_in_sensitivity_list"
                elif word[0]==")":
                    self.region = "process"
            elif self.region=="range_in_sensitivity_list":
                if word[0]=="(":
                    number_of_open_brackets += 1
                elif word[0]==")":
                    if number_of_close_brackets!=number_of_open_brackets-1:
                        number_of_close_brackets += 1
                    else:
                        self.region = "sensitivity_list"
            elif self.region=="process_local_declaration":
                if word[0]==":":
                    self.region = "process_local_declaration_type"
            elif self.region=="process_local_declaration_type":
                if word[0]==";":
                    self.region = "process"
                elif word[0] in ["range", "array", "downto", "to", "access"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]=="(":
                    number_of_open_brackets = 1
                    number_of_close_brackets = 0
                    self.region = "range_in_process_local_declaration_type"
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    self.parse_result["process_locals_data_types"] += [[word[1], word[2]]]
            elif self.region=="range_in_process_local_declaration_type":
                if word[0]=="(":
                    number_of_open_brackets += 1
                elif word[0]==")":
                    if number_of_close_brackets!=number_of_open_brackets-1:
                        number_of_close_brackets += 1
                    else:
                        self.region = "process_local_declaration_type"
                elif word[0] in("downto", "to"):
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="architecture_body_end":
                if word[0]=="architecture":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]==";":
                    self.region = "entity_context"
            if word[0] not in ["", " ", "\n", "\r", "\t"]:
                previous_word = word

        generic_definition = re.sub("^\n"      , "", generic_definition) # remove empty lines
        generic_definition = re.sub(r"(?m)^\s*", "", generic_definition) # remove leading blanks, multiline flag is set
        self.parse_result["generic_definition" ]  = generic_definition
        self.parse_result["data_type"          ]  = []
        self.parse_result["data_type"          ] += self.parse_result["type_names"]
        self.parse_result["data_type"          ] += self.parse_result["port_interface_types"]
        self.parse_result["data_type"          ] += self.parse_result["generics_interface_types"]
        self.parse_result["data_type"          ] += self.parse_result["component_port_interface_types"]
        self.parse_result["data_type"          ] += self.parse_result["component_generic_interface_types"]
        self.parse_result["data_type"          ] += self.parse_result["procedure_interface_types"]
        self.parse_result["data_type"          ] += self.parse_result["function_interface_types"]
        self.parse_result["data_type"          ] += self.parse_result["function_return_types"]
        self.parse_result["data_type"          ] += self.parse_result["process_locals_data_types"]
        self.parse_result["data_type_positions"]  = []
        self.parse_result["data_type_positions"] += self.parse_result["type_name_positions"]
        self.parse_result["data_type_positions"] += self.parse_result["port_interface_types_positions"]
        self.parse_result["data_type_positions"] += self.parse_result["generics_interface_types_positions"]
        self.parse_result["data_type_positions"] += self.parse_result["component_port_interface_types_positions"]
        self.parse_result["data_type_positions"] += self.parse_result["component_generic_interface_types_positions"]
        self.parse_result["data_type_positions"] += self.parse_result["procedure_interface_types_positions"]
        self.parse_result["data_type_positions"] += self.parse_result["function_interface_types_positions"]
        self.parse_result["data_type_positions"] += self.parse_result["function_return_types_positions"]
        self.parse_result["data_type_positions"] += self.parse_result["process_locals_data_types"]

    def extend_parse_result_for_name_list(self):
        list_of_parse_results_to_adapt = ["_interface_direction", "_interface_direction_positions", "_interface_types", "_interface_types_positions",
                                          "_interface_ranges", "_interface_constraints", "_interface_init", "_interface_init_positions", "_interface_init_range"]
        for entry in list_of_parse_results_to_adapt:
            if len(self.parse_result[self.return_region + entry])!=0: # When the syntax is wrong or incomplete, this list may be empty
                while len(self.parse_result[self.return_region + entry])<len(self.parse_result[self.return_region + "_interface_names"]):
                    self.parse_result[self.return_region + entry].append(self.parse_result[self.return_region + entry][-1])

    def get(self, tag_name):
        if tag_name in self.parse_result:
            return self.parse_result[tag_name]
        #print("VHDL-Parsing: did not find tag ", tag_name)
        return ""

    def get_positions(self, tag_name):
        return self.parse_result[tag_name]

    def get_architecture_declarations(self):
        return self.architecture_declarations

    def get_architecture_body(self):
        return self.architecture_body
