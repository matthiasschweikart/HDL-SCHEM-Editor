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
        "library_name_positions"                      ,
        "package_name_positions"                      ,
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
    def __init__(self, vhdl, region="entity_context"):
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
                       re.compile(r"\("),
                       re.compile(r"\)"),
                       re.compile(r"\n"),
                       re.compile(r"\."),
                       re.compile(r";"),
                       re.compile(r":"),
                       re.compile(r"="),
                       re.compile(r"<"),
                       re.compile(r">"),
                       re.compile(r","),
                       re.compile(r"--.*(\n|$)"),
                       re.compile(r"[ \n\r\t]|$") # White space: Blank, Return, Linefeed, Tabulator or String-End
                      ]
        self.number_of_characters_read = 0
        word_list = []
        if length<100000: # If the text has more than 100000 characters, then creating word_list takes too much time.
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
        self.parse_result["library_name"                                   ] = []
        self.parse_result["library_name_positions"                         ] = []
        self.parse_result["architecture_library_name"                      ] = []
        self.parse_result["architecture_library_name_positions"            ] = []
        self.parse_result["package_name"                                   ] = []
        self.parse_result["package_name_positions"                         ] = []
        self.parse_result["architecture_package_name"                      ] = []
        self.parse_result["architecture_package_name_positions"            ] = []
        self.parse_result["entity_name"                                    ] = ""
        self.parse_result["entity_name_positions"                          ] = []
        self.parse_result["architecture_name"                              ] = ""
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
        return   [word1, start_index_of_word_before_search_string, end_index_of_word_before_search_string
               ],[word2, start_index_of_search_string_match, end_index_of_search_string_match]

    def _analyze(self, word_list):
        generic_definition = ""
        actual_library     = ""
        in_block_comment = False
        in_generate      = 0
        for word in word_list:
            # By _analyze() the VHDL is splitted up and all the single pieces are packed into self.parse_result.
            # But the generic definitions of an entity (and all the included comments) are sometimes needed in their original form.
            # So here during the parsing all peaces of the generic definition are collected and put back together.
            # Because the parsing is still in one of the relevant "interface_.." regions, when the closing bracket of the generic
            # definition is found, this closing bracket also shows in word[0] and must be excluded:
            if self.return_region=="generics" and (
                (self.region in ["interface_declaration", "interface_type", "interface_init"] and word[0]!=')') or
                 self.region in ["interface_range", "interface_init1", "interface_init_range"]
                ):
                generic_definition += word[0]
            if word[0].startswith("/*") or in_block_comment:
                in_block_comment = True
                if word[0].startswith("*/"):
                    in_block_comment = False
                self.parse_result["comment"]           += [word[0]]
                self.parse_result["comment_positions"] += [[word[1], word[2]]]
            elif word[0].startswith("--"):
                self.parse_result["comment"]           += [word[0]]
                self.parse_result["comment_positions"] += [[word[1], word[2]]]
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
            elif self.region=="library clause":
                if word[0]==";":
                    self.region = "entity_context"
                elif word[0] not in [" ", "\n", "\r", "\t"]:
                    self.parse_result["library_name"]           += [word[0]]
                    self.parse_result["library_name_positions"] += [[word[1], word[2]]]
            elif self.region=="use clause":
                if word[0]==";":
                    self.region = "entity_context"
                elif word[0]=="all":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0] in self.parse_result["library_name"]:
                    actual_library = word[0]
                    self.parse_result["library_name_positions"] += [[word[1], word[2]]]
                    first_word_of_use_clause = False
                elif word[0] not in [" ", "\n", "\r", "\t"] and first_word_of_use_clause is True:
                    actual_library = word[0] # A library definition is missing in the VHDL, because word[0] is not stored in self.parse_result["library_name"]
                    first_word_of_use_clause = False
                elif word[0] not in [" ", "\n", "\r", "\t", "."]:
                    self.parse_result["package_name"]           += [actual_library + '.' + word[0]]
                    self.parse_result["package_name_positions"] += [[word[1], word[2]]]
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
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    self.parse_result["entity_name_used_in_architecture"] = word[0]
                    self.parse_result["entity_name_used_in_architecture_positions"] += [[word[1], word[2]]]
            elif self.region=="architecture_declarative_region":
                if   word[0]=="begin":
                    self.region = "architecture_body"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0] in ["type", "subtype"]:
                    self.region = "type_declaration"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.return_region = "architecture_declarative_region"
                elif word[0] in ["signal", "constant"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "signal_declaration"
                    self.return_region = "architecture_declarative_region"
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
                elif word[0] not in ["", " ", "\n", "\r", "\t", "(", ")", "-", ".", "<", ">", ","] and not word[0].startswith(("-","0","1","2","3","4","5","6","7","8","9")):
                    self.parse_result["type_names"].append(word[0])
                    self.parse_result["type_name_positions"] += [[word[1], word[2]]]
            elif self.region=="element_subtype_region":
                if word[0]==";":
                    self.region = self.return_region
                elif word[0] not in ["", " ", "\n", "\r", "\t", "(", ")", "-", ".", "<", ">", ","] and not word[0].startswith(("-","0","1","2","3","4","5","6","7","8","9")):
                    self.parse_result["type_names"].append(word[0])
                    self.parse_result["type_name_positions"] += [[word[1], word[2]]]
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
                else:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="units_declarative_region":
                if word[0]=="end":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "end_units_declarative_region"
            elif self.region=="end_units_declarative_region":
                if word[0]==";":
                    self.region = self.return_region
                else:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="signal_declaration":
                if word[0]==":":
                    self.region = "signal_declaration_signal_type"
            elif self.region=="signal_declaration_signal_type":
                if word[0]==";":
                    self.region = self.return_region
                elif word[0]=="(":
                    self.region = "signal_declaration_signal_type_range"
                else:
                    self.parse_result["type_names"].append(word[0])
                    self.parse_result["type_name_positions"] += [[word[1], word[2]]]
            elif self.region=="signal_declaration_signal_type_range":
                if word[0]==")":
                    self.region = "signal_declaration_signal_type"
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
                elif word[0] in ["type", "subtype"]:
                    self.region = "type_declaration"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.return_region = "procedure_declarative_region"
                elif word[0] in ["constant", "signal", "variable"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "signal_declaration"
                    self.return_region = "procedure_declarative_region"
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
                elif word[0] in ["type", "subtype"]:
                    self.region = "type_declaration"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.return_region = "function_declarative_region"
                elif word[0] in ["constant", "signal", "variable"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "signal_declaration"
                    self.return_region = "function_declarative_region"
            elif self.region=="interface_declaration":    # can be reached from "procedure", "function", "port", "generics", "record definition", "component"
                if   word[0] in ["constant", "signal", "variable"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]==":":
                    self.parse_result[self.return_region + "_interface_direction"          ].append("")     # default value, because this info might not exist.
                    self.parse_result[self.return_region + "_interface_direction_positions"].append([0, 0]) # default value, because this info might not exist.
                    self.parse_result[self.return_region + "_interface_ranges"             ].append("")     # default value, because this info might not exist.
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
                    number_of_open_brackets = 1
                    number_of_close_brackets = 0
                elif word[0]==":":
                    self.region = "interface_init1"
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
                    busrange = " range"
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    if type_is_stored is False:
                        self.parse_result[self.return_region + "_interface_types"          ].append(word[0])
                        self.parse_result[self.return_region + "_interface_types_positions"].append([word[1], word[2]])
                        type_is_stored = True
            elif self.region=="interface_range":
                busrange += word[0]
                if word[0]=="(":
                    number_of_open_brackets += 1
                elif word[0]==")":
                    if number_of_close_brackets!=number_of_open_brackets-1:
                        number_of_close_brackets += 1
                    else:
                        self.parse_result[self.return_region + "_interface_ranges"][-1] = busrange # Overwrite the default value.
                        self.region = "interface_type"
                        type_is_stored = False
            elif self.region=="interface_range_range":
                if word[0]==")": # This is the last bracket which closes the interface declaration.
                    #self.parse_result[self.return_region + "_interface_ranges"][-1] = busrange # Overwrite the default value.
                    self.extend_parse_result_for_name_list()
                    self.region = self.return_region + "_declaration"
                    #print("interface_range_range nach ): busrange =", busrange)
                elif word[0]==";": # This is the end of a range definition ("range 0 to 7"), a next interface definition is following.
                    #self.parse_result[self.return_region + "_interface_ranges"][-1] = busrange # Overwrite the default value.
                    self.extend_parse_result_for_name_list()
                    self.region = "interface_declaration"
                    #print("interface_range_range nach ;: busrange =", busrange)
                elif word[0]==":":
                    #print("interface_range_range nach : busrange =", busrange)
                    #self.parse_result[self.return_region + "_interface_ranges"][-1] = busrange # Overwrite the default value.
                    self.region = "interface_init1"
                else:
                    busrange += word[0]
                    # Overwrite at once, because it might be that instead of ')',';',':' no next word arrives (when only a VHDL fragment is analyzed)
                    self.parse_result[self.return_region + "_interface_ranges"][-1] = busrange # Overwrite the default value.
            elif self.region=="interface_init1":
                if word[0]=="=":
                    self.region = "interface_init"
                elif word[0] not in ["", " ", "\n", "\r", "\t"]:
                    # Will only used at an initialization, where ':' is used instead of ":=":
                    self.extend_parse_result_for_name_list()
                    self.region = "interface_declaration"
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
                elif word[0] not in ["", " ", "\n", "\r", "\t", "fs", "ps", "ns", "us", "ms", "sec", "min", "hr"]:
                    self.parse_result[self.return_region + "_interface_init"]          [-1] = word[0] # Overwrite the default value.
                    self.parse_result[self.return_region + "_interface_init_positions"][-1] = [word[1], word[2]]
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
            elif self.region=="sequential_statements":
                if word[0]=="end":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "sequential_statements_end"
                elif word[0] in ["if", "then", "elsif", "else", "downto", "to", "for", "in", "loop", "while",
                                 "or", "and", "xor", "nor", "nand", "not", "rem", "wait",
                                 "return", "others", "note", "warning", "error", "failure",
                                 "severity", "assert", "report"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
            elif self.region=="sequential_statements_end":
                if word[0] in ["if", "case", "loop"]: # Obvious we are still in "sequential_statements", and not at the end.
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    self.region = "sequential_statements"
                elif word[0] in ["process", "function", "procedure"]: # From "end process/function/procedure;".
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]==";": # This semicolon has followed "end", sometimes with a name inbetween "end [<name>];"
                    self.region = self.return_region
            elif self.region=="architecture_body":
                if word[0]=="process":
                    self.region = "process"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]=="with":
                    self.region = "with_selector"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0] in ["note","warning","error","failure","report","assert","severity"]:
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]=="<":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]+1]] # Increment word[2] in order to highlight "<="
                    self.region = "inlineprocess"
                elif word[0]==":":
                    self.parse_result["label_names"].append(previous_word[0])
                    self.parse_result["label_positions"] += [[previous_word[1], previous_word[2]]]
                    self.region = "process_or_instance_or_generate"
                elif word[0]=="end":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                    if in_generate==0:
                        self.region = "architecture_body_end"
                    else:
                        self.region = "generate_end"
                        in_generate -= 1
            elif self.region=="generate_end":
                if word[0]=="generate":
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif word[0]==";":
                    self.region = "architecture_body"
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
                elif  word[0] in ["for", "if"]:
                    self.region = "generate_condition"
                    in_generate += 1
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
                elif  word[0]=="entity":
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
            elif self.region=="generate_condition":
                if  word[0]=="generate":
                    self.region = "architecture_body"
                    self.parse_result["keyword_positions"] += [[word[1], word[2]]]
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
                elif word[0] in ["signal", "variable", "constant"]:
                    self.region = "process_local_declaration"
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
                else:
                    self.parse_result["process_locals_data_types"] += [[word[1], word[2]]]
            elif self.region=="range_in_process_local_declaration_type":
                if word[0]=="(":
                    number_of_open_brackets += 1
                elif word[0]==")":
                    if number_of_close_brackets!=number_of_open_brackets-1:
                        number_of_close_brackets += 1
                    else:
                        self.region = "process_local_declaration_type"
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
                                          "_interface_ranges", "_interface_init", "_interface_init_positions", "_interface_init_range"]
        for entry in list_of_parse_results_to_adapt:
            if len(self.parse_result[self.return_region + entry])!=0: # Wenn the syntax is wrong or incomplete, this list may be empty
                while len(self.parse_result[self.return_region + entry])<len(self.parse_result[self.return_region + "_interface_names"]):
                    self.parse_result[self.return_region + entry].append(self.parse_result[self.return_region + entry][-1])

    def get(self, tag_name):
        if tag_name in self.parse_result:
            return self.parse_result[tag_name]
        return ""

    def get_positions(self, tag_name):
        return self.parse_result[tag_name]
