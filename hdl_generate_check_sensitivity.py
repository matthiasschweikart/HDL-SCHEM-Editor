"""
    This class checks if all sensitivity lists of a module are correct.
    First a list of all readable signal names is created (outputs are not readable).
    Then all non clocked processes are copied into a list.
    All processes in this list are separated into its sensitivity_list and the remaining part.
    Then each readable signal name is searched in a sensitivity list and its remaining part.
    If the name is found in both, or not found in either, then everything is ok.
    If it is only found in the remaining process, then the name is missing in the sensitivity list.
    If it is only found in the sensitivity list, then the name is not needed in the sensitivity list.
    In both erroneous situations, a message is created.
"""
import re

class CheckSensitivity():
    def __init__(self, input_decl, inout_decl, signal_decl, block_list, language, module_name, hdl_file_name, hdl_code, log_tab):
        self.module_name = module_name
        self.sensitivity_message = "" # Not only read here, but also by hdl_generate.HdlGenerate
        list_of_readable_signals =      self.__extract_names_from_declarations(input_decl , language)
        list_of_readable_signals.extend(self.__extract_names_from_declarations(inout_decl , language))
        list_of_readable_signals.extend(self.__extract_names_from_declarations(signal_decl, language))
        list_of_processes = self.__get_list_of_processes(block_list, language)
        list_of_processes = self.__remove_targets_from_processes(list_of_processes, language)
        list_of_processes, list_of_sensitivity_lists = self.__separate_sensitivity_lists_from_processes(list_of_processes, language)
        self.__check_for_bug_in_sensitivity_list(list_of_processes, list_of_sensitivity_lists, list_of_readable_signals, language,
                                                 self.module_name, hdl_file_name, hdl_code)
        log_tab.insert_line_in_log(self.sensitivity_message, state_after_insert="disabled")

    def __extract_names_from_declarations(self, declarations, language):
        list_of_names = []
        for declaration in declarations:
            if language=="VHDL":
                list_of_names.append(re.sub(r":.*", "", declaration).strip().lower())
            else:
                declaration_without_ranges = re.sub(r"\[.*?\]", "", declaration) # remove range from type and from signal-name
                list_of_strings = declaration_without_ranges.split(' ')
                list_of_names.append(list_of_strings[-1])
        return list_of_names

    def __get_list_of_processes(self, block_list, language):
        list_of_processes = []
        for canvas_id in block_list:
            block_without_comments = self.__remove_comments_at_line_end(block_list[canvas_id], language)
            block_without_comments = self.__remove_block_comments(block_without_comments)
            list_of_processes.extend(self.__extract_processes(block_without_comments, language))
        return list_of_processes

    def __remove_comments_at_line_end(self, hdl_text, language):
        hdl_text += '\n' # Add a last return for the search-expression
        if language=="VHDL":
            hdl_text = re.sub(r"--.*?\n", "\n", hdl_text)
        else:
            hdl_text = re.sub(r"//.*?\n", "\n", hdl_text)
        return hdl_text

    def __remove_block_comments(self, hdl_text):
        hdl_text = re.sub(r"/\*.*?\*/", "", hdl_text, flags=re.DOTALL)
        return hdl_text

    def __extract_processes(self, block_without_comments, language):
        process_list = []
        block_without_comments = re.sub(r"\["      , r" [ " , block_without_comments) # Surround with blanks.
        block_without_comments = re.sub(r"\]"      , r" ] " , block_without_comments) # Surround with blanks.
        block_without_comments = re.sub(r","       , r" , " , block_without_comments) # Separate list elements.
        block_without_comments = re.sub(r":"       , r" : " , block_without_comments) # Separate labels (VHDL: from "process"; Verilog: from "begin")
        block_without_comments = re.sub(r"<"       , r" < " , block_without_comments) # Surround with blanks.
        block_without_comments = re.sub(r">"       , r" > " , block_without_comments) # Surround with blanks.
        block_without_comments = re.sub(r"="       , r" = " , block_without_comments) # Surround with blanks.
        block_without_comments = re.sub(r" =\s*= " , r" == ", block_without_comments) # Restore ==.
        block_without_comments = re.sub(r" :\s*= " , r" := ", block_without_comments) # Restore :=.
        block_without_comments = re.sub(r" <\s*= " , r" <= ", block_without_comments) # Restore <=.
        block_without_comments = re.sub(r" >\s*= " , r" >= ", block_without_comments) # Restore >=.
        block_without_comments = re.sub(r"\("      , r" ( " , block_without_comments) # Surround brackets with blanks
        block_without_comments = re.sub(r"\)"      , r" ) " , block_without_comments) # (VHDL: separate "process" from sensitivity; Verilog: separate conditions).
        block_without_comments = re.sub(r";"       , r" ; " , block_without_comments) # Surround assignment end with blanks.
        block_without_comments = re.sub(r"\+"      , r" + " , block_without_comments) # Surround '+' with blanks.
        block_without_comments = re.sub(r"-"       , r" - " , block_without_comments) # Surround '-' with blanks.
        block_without_comments = re.sub(r"'.*?'"   , r"   " , block_without_comments) # Remove any string
        block_without_comments = re.sub(r'".*?"'   , r"   " , block_without_comments) # Remove any string
        if language=="VHDL":
            block_without_comments = block_without_comments.lower()
            block_without_comments = re.sub(r"'event"  , r"' event" , block_without_comments, flags=re.IGNORECASE|re.MULTILINE)
            block_without_comments = re.sub(r"^process", r" process", block_without_comments, flags=re.IGNORECASE|re.MULTILINE)
            block_without_comments = re.sub(r"process$", r"process ", block_without_comments, flags=re.IGNORECASE|re.MULTILINE)
            match_object_without_sensitivity_list = re.search(r"^\s+process\s+?[^(]", block_without_comments, flags=re.DOTALL) # Check the opening bracket of the sensitivity list
            match_object = re.search(r" process .*?end\s+process", block_without_comments, flags=re.DOTALL) # Separate each process
            while match_object:
                if (not match_object_without_sensitivity_list   and
                    "rising_edge"  not in match_object.group(0) and
                    "falling_edge" not in match_object.group(0) and
                    "event"        not in match_object.group(0)):
                    process_list.append(match_object.group(0).split())
                block_without_comments = re.sub(r" process .*?end\s+process", "", block_without_comments, count=1, flags=re.DOTALL|re.IGNORECASE)
                match_object = re.search(r" process .*?end\s+process", block_without_comments, flags=re.DOTALL|re.IGNORECASE)
        else: # Verilog
            block_without_comments = re.sub(r"@", r" @ ", block_without_comments) # Separate @ from string "always"
            list_of_words  =  block_without_comments.split()
            process        = []
            in_process     = False
            wait_for_begin = False
            begin_counter  = 0
            for word in list_of_words:
                if word=="always":
                    in_process     = True
                    wait_for_begin = True
                    process.append(word)
                elif in_process:
                    process.append(word)
                    if word=="begin":
                        begin_counter += 1
                        wait_for_begin = False
                    elif not wait_for_begin and word=="end":
                        begin_counter -= 1
                    if not wait_for_begin and begin_counter==0:
                        if ("posedge" not in process and
                            "negedge" not in process):
                            process_list.append(process)
                        in_process = False
                        process = []
        return process_list

    def __remove_targets_from_processes(self, list_of_processes, language):
        list_of_processes_mod = []
        for process in list_of_processes:
            remove_target = False
            line_end_hit  = False
            in_bracket    = 0
            process_mod   = []
            if language=="VHDL":
                for word in reversed(process):
                    if word==')': # jump over index-bracket
                        in_bracket += 1
                    elif word=='(':
                        in_bracket -= 1
                    elif in_bracket==0:
                        if word==';':
                            line_end_hit = True
                        elif line_end_hit and word=="<=":
                            remove_target = True
                        elif remove_target:
                            word = "t-a-r-g-e-t"
                            remove_target = False
                            line_end_hit = False
                    process_mod.append(word)
            else: # Verilog
                in_square_bracket = 0
                for word in reversed(process):
                    if word==')': # jump over condition-bracket
                        in_bracket += 1
                    elif word=='(':
                        in_bracket -= 1
                    if word==']': # jump over index-bracket
                        in_square_bracket += 1
                    elif word=='[':
                        in_square_bracket -= 1
                    elif in_bracket==0 and in_square_bracket==0:
                        if remove_target:
                            word = "t-a-r-g-e-t"
                            line_end_hit = False
                            remove_target = False
                        elif word==';':
                            line_end_hit = True
                        elif line_end_hit and word=="<=":
                            remove_target = True
                    process_mod.append(word)
            list_of_processes_mod.append(list(reversed(process_mod)))
        return list_of_processes_mod

    def  __separate_sensitivity_lists_from_processes(self, list_of_processes, language):
        list_of_sensitivity_lists                  = []
        list_of_processes_without_sensitivity_list = []
        for process in list_of_processes:
            in_sensitivity_list              = False
            sensitivity_list                 = []
            process_without_sensitivity_list = []
            for word in process:
                if (language=="VHDL" and word=="process") or (language!="VHDL" and word=="@"):
                    in_sensitivity_list = True
                    process_without_sensitivity_list.append(word)
                elif word=="begin":
                    in_sensitivity_list = False
                    process_without_sensitivity_list.append(word)
                elif in_sensitivity_list:
                    sensitivity_list.append(word)
                else:
                    process_without_sensitivity_list.append(word)
            list_of_sensitivity_lists.append(sensitivity_list)
            list_of_processes_without_sensitivity_list.append(process_without_sensitivity_list)
        return list_of_processes_without_sensitivity_list, list_of_sensitivity_lists

    def __check_for_bug_in_sensitivity_list(self, list_of_processes, list_of_sensitivity_lists, list_of_readable_signals, language, module_name, hdl_file_name, hdl_code):
        self.sensitivity_message = ""
        for index, process in enumerate(list_of_processes):
            regex_for_finding_sensitivity = ""
            for word in list_of_sensitivity_lists[index]:
                if word not in ['(', ')']:
                    regex_for_finding_sensitivity += word + r"\s*"
                else:
                    regex_for_finding_sensitivity += '\\' + word + r"\s*"
            if ((language=="VHDL" and not "all" in list_of_sensitivity_lists[index]) or
                (language!="VHDL" and not "*"   in list_of_sensitivity_lists[index])):
                for readable_signal in list_of_readable_signals:
                    hit_dict = {"sensitivity": "", "process": ""}
                    if readable_signal in list_of_sensitivity_lists[index]:
                        hit_dict["sensitivity"] = readable_signal
                    if readable_signal in process:
                        hit_dict["process"    ] = readable_signal
                    #print("hdl_code =", list_of_sensitivity_lists[index], readable_signal)
                    if hit_dict["sensitivity"]!=hit_dict["process"]:
                        match_object = re.search(regex_for_finding_sensitivity, hdl_code)
                        sensitivity_list = hdl_code[match_object.start():match_object.end()].strip()
                        line_number      = hdl_code[0                   :match_object.end()].count('\n')
                        if hit_dict["sensitivity"]=="":
                            self.sensitivity_message += "HDL Sensitivity  : Warning in module " + module_name     +\
                                                        ": The signal " + readable_signal                         +\
                                                        " is missing in the sensitivity-list " + sensitivity_list +\
                                                        " in line " + str(line_number) + ' of file ' + hdl_file_name + '.\n'
                        else:
                            self.sensitivity_message += "HDL Sensitivity  : Warning in module " + module_name        +\
                                                        ": The signal " + readable_signal                            +\
                                                        " is not needed in the sensitivity-list " + sensitivity_list +\
                                                        " in line " + str(line_number) + ' of file ' + hdl_file_name + '.\n'
        # if self.sensitivity_message=="":
        #     self.sensitivity_message = "HDL Sensitivity  : The sensitivity lists of the " + module_name + " module is okay.\n"
        # else:
        #     print("Fehler in Sensi:", self.sensitivity_message)
