"""
This class is executed when the user starts the compile of a flat or hierarchical design.
If the design is hierarchical, then first a file named hdl_file_list.txt file is generated,
from which the compile command (provided by the user) can extract the names of all the files
which have to be compiled.
If the design is flat, then the user can provide the filenames of all the files, which
have to be compiled, in the compile command.
If the parameter flipflop_stat is true, then the class GenerateFlipflopStat is used to create
new HDL-files and a modified hdl-file-list. When the simulation runs, the messages regarding
the flipflop statistic are stored in a file and are not shown at STDOUT.
From these messages a statistic table is generated and printed at STDOUT.
"""
import subprocess
from tkinter   import messagebox
from datetime  import datetime
from threading import Thread
import re
import os
import shlex

import notebook_top
import notebook_log_tab
import design_data
import hdl_create_file_list
import hdl_generate_functions
import hdl_generate_flipflop_stat

class CompileHDL():
    def __init__(self,
                 window,
                 notebook : notebook_top.NotebookTop,
                 log_tab  : notebook_log_tab.NotebookLogTab,
                 design   : design_data.DesignData,
                 compile_through_hierarchy,
                 flipflop_stat
                 ):
        self.window                    = window
        self.compile_through_hierarchy = compile_through_hierarchy
        self.design                    = design
        self.log_tab                   = log_tab
        self.run_compile               = True
        self.start_time                = None
        if (self.__change_directory_to_working_directory_is_not_possible() or
            self.__hdl_is_not_up_to_date()                                 or
            self.__design_changes_are_not_saved()):
            return
        notebook.show_tab("Messages")
        self.__put_header_in_message_tab()
        if self.compile_through_hierarchy or flipflop_stat:
            hdl_file_list_creator = hdl_create_file_list.HdlCreateFileList(self, window, self.log_tab)
            if flipflop_stat:
                hdl_file_list_name, hdl_file_list = hdl_file_list_creator.get_hdl_file_list()
                hdl_generate_flipflop_stat.GenerateFlipflopStat(hdl_file_list_name, hdl_file_list)
        if self.run_compile: # Can be set to False by HdlCreateFileList.
            commands = self.__get_commands_as_list()
            # Run the commands in a asynchronous task, so that the GUI remains responsive:
            runjob = Thread(target=self.__run_commands, args=[commands, flipflop_stat])
            runjob.start()

    def __hdl_is_not_up_to_date(self):
        if self.design.get_language()!="VHDL":
            hdlfilename = self.design.get_generate_path_value() + '/' + self.design.get_module_name() + ".v"
            hdlfilename_architecture = None
        else:
            if self.design.get_number_of_files()==1:
                hdlfilename = self.design.get_generate_path_value() + '/' + self.design.get_module_name() + ".vhd"
                hdlfilename_architecture = None
            else:
                hdlfilename = self.design.get_generate_path_value() + '/' + self.design.get_module_name() + "_e.vhd"
                hdlfilename_architecture = self.design.get_generate_path_value() + '/' + self.design.get_module_name() + '_' + self.design.get_architecture_name() + ".vhd"
        return hdl_generate_functions.HdlGenerateFunctions.hdl_must_be_generated(self.design.get_path_name(), hdlfilename, hdlfilename_architecture, show_message=True)

    def __design_changes_are_not_saved(self):
        if self.window.title().endswith("*"):
            messagebox.showerror("Error in HDL-SCHEM-Editor", "The design was modified.\nHDL must be generated again before compile can run.")
            return True
        return False

    def __get_commands_as_list(self):
        if self.compile_through_hierarchy:
            compile_command = self.design.get_compile_hierarchy_cmd()
            message_for_error = "The compile through hierarchy command is not specified.\nSpecify it in the Control-Tab."
        else:
            compile_command = self.design.get_compile_cmd()
            message_for_error = "The compile command for a single module is not specified.\nSpecify it in the Control-Tab."
        if compile_command=="" or compile_command.isspace():
            messagebox.showerror("Error in HDL-SCHEM-Editor", message_for_error)
        return compile_command.split(";")

    def __change_directory_to_working_directory_is_not_possible(self):
        working_directory = self.window.design.get_working_directory()
        module_name       = self.window.design.get_module_name()
        if working_directory=="" or working_directory.isspace():
            # The user does not use the working_directory, so no "change directory" command is used and
            # all the results are placed in the current directory.
            return False
        if not os.path.isdir(working_directory):
            os.mkdir(working_directory)
        if not os.path.isdir(working_directory + '/' + module_name):
            if os.path.isfile(working_directory + '/' + module_name):
                messagebox.showerror("Error in HDL-SCHEM-Editor", "Could not create working directory:\n" + working_directory + '/' + module_name +
                                     " as there is already a file with the same name.")
                return True
            else:
                os.mkdir(working_directory + '/' + module_name)
        try:
            os.chdir(working_directory + '/' + module_name)
            return False
        except FileNotFoundError:
            messagebox.showerror("Error in HDL-SCHEM-Editor", "Could not change to working directory:\n" + working_directory + '/' + module_name)
            return True

    def __put_header_in_message_tab(self):
        self.log_tab.insert_line_in_log("\n+++++++++++++++++++++++++++++++++ " + datetime.today().ctime() +" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n",
                                                state_after_insert="disabled")
        self.start_time = datetime.now()
        self.log_tab.insert_line_in_log("Working Directory: " + self.window.design.get_working_directory() + "\n",
                                                state_after_insert="disabled")

    def __run_commands(self, commands, flipflop_stat):
        self.window.config(cursor="watch")
        for command in commands:
            success = self.__execute(command, flipflop_stat)
            if not success:
                break
        end_time = datetime.now()
        self.log_tab.insert_line_in_log("Finished user commands from Control-Tab after " + str(end_time - self.start_time) + ".\n", state_after_insert="disabled")
        self.window.config(cursor="arrow")

    def __execute(self, command, flipflop_stat):
        command_array = shlex.split(command) # Does not split quoted sub-strings with blanks.
        self.__replace_variables(command_array)
        if not command_array:
            return False
        for command_part in command_array:
            self.log_tab.insert_line_in_log(command_part+" ", state_after_insert="disabled")
        self.log_tab.insert_line_in_log("\n", state_after_insert="disabled")
        flipflop_stat_list = []
        try:
            process = subprocess.Popen(command_array,
                                        text=True, # Decoding is done by Popen.
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT)
            self.log_tab.activate_kill_button(process)
            for line in process.stdout: # Terminates when process.stdout is closed.
                if flipflop_stat and "flipflop_statistics for instance" in line:
                    flipflop_stat_list.append(line)
                elif line!="\n": # VHDL report-statements cause empty lines which mess up the protocol.
                    #print("line =", line)
                    self.log_tab.insert_line_in_log(line, state_after_insert="disabled")
            self.log_tab.deactivate_kill_button()
        except FileNotFoundError:
            command_string = ""
            for word in command_array:
                command_string += word + " "
            messagebox.showerror("Error in HDL-SCHEM-Editor", "FileNotFoundError caused by compile command:\n" + command_string)
            return False
        except PermissionError:
            command_string = ""
            for word in command_array:
                command_string += word + " "
            messagebox.showerror("Error in HDL-SCHEM-Editor", "PermissionError caused by compile command:\n" + command_string)
            return False
        if (flipflop_stat and
            flipflop_stat_list): # When several commands are concatenated in "compile through hierarchy command", then flipflop_stat_list is filled only by 1 command.
            self.__write_simulator_messages_into_file(flipflop_stat_list)
            flipflop_dict    = self.__create_flipflop_dict_from_simulator_messages(flipflop_stat_list)
            sum_of_flipflops = self.__calculate_sum_of_flipflops(flipflop_dict)
            table_for_log    = self.__create_table_for_log_tab(flipflop_dict, sum_of_flipflops)
            self.__put_table_into_messages_tab(table_for_log)
        return True

    def __replace_variables(self, command_array):
        module_name = self.design.get_module_name()
        generate_path_value = self.design.get_generate_path_value()
        file_name1     = generate_path_value + "/" + module_name + "_e.vhd"
        file_name2     = generate_path_value + "/" + module_name + '_' + self.window.notebook_top.diagram_tab.architecture_name + ".vhd"
        file_name3     = generate_path_value + "/" + module_name + ".vhd"
        if self.design.get_language()=="Verilog":
            file_name4 = generate_path_value + "/" + module_name + ".v"
        elif self.design.get_language()=="SystemVerilog":
            file_name4 = generate_path_value + "/" + module_name + ".sv"
        else:
            file_name4 = ""
        for index, _ in enumerate(command_array):
            command_array[index] = re.sub(r"\$file1"        , file_name1         , command_array[index])
            command_array[index] = re.sub(r"\$file2"        , file_name2         , command_array[index])
            command_array[index] = re.sub(r"\$file3"        , file_name3         , command_array[index])
            command_array[index] = re.sub(r"\$file"         , file_name4         , command_array[index])
            command_array[index] = re.sub(r"\$name"         , module_name        , command_array[index])
            command_array[index] = re.sub(r"\$hdl-file-list", "hdl_file_list_" + module_name + ".txt", command_array[index])

    def __write_simulator_messages_into_file(self, flipflop_stat_list):
        # The file is written into the current working directory, which is the directory set in the Control-tab, or the directory where HSE was started.
        fileobject = open("flipflop_statistic_simulator_messages.txt", 'w', encoding="utf-8")
        for flipflop_stat_list_line in flipflop_stat_list:
            fileobject.write(flipflop_stat_list_line)
        fileobject.close()
        return

    def __create_flipflop_dict_from_simulator_messages(self, flipflop_stat_list):
        flipflop_dict = {}
        for flipflop_stat_list_line in flipflop_stat_list:
            # The instance name has the HDL-simulator naming style. When GHDL is used, this means the name looks like ":top-module:sub-module:".
            if "no clocked signals found" in flipflop_stat_list_line:
                instance_name = re.sub(r".*flipflop_statistics for instance (.*) no clocked signals found.*", r"\1", flipflop_stat_list_line, flags=re.DOTALL)
                signal_name   = "no-clocked-signal-existent"
            else:
                instance_name = re.sub(r".*flipflop_statistics for instance (.*) signal .*", r"\1", flipflop_stat_list_line, flags=re.DOTALL)
                signal_name   = re.sub(r".* signal (.*?) .*"                               , r"\1", flipflop_stat_list_line, flags=re.DOTALL)
                signal_name   = re.sub(r"\(.*", "", signal_name) # Remove sub-indices from signal name.
            generate_condition = ""
            flipflops          = ""
            factor             = ""
            if "element-length" in flipflop_stat_list_line:
                factor = int(re.sub(r".*=", "", flipflop_stat_list_line))
            if "generate-condition" in flipflop_stat_list_line:
                generate_condition = re.sub(r".*==", "", flipflop_stat_list_line).strip()
            if " uses " in flipflop_stat_list_line:
                flipflops = re.sub(r".* uses (.*) flipflop.*"   , r"\1", flipflop_stat_list_line, flags=re.DOTALL).strip()
            if " unknown " in flipflop_stat_list_line:
                flipflops = '?'
            if instance_name not in flipflop_dict:
                flipflop_dict[instance_name] = {}
            if signal_name not in flipflop_dict[instance_name]:
                flipflop_dict[instance_name][signal_name] = {}
            if generate_condition!="":
                flipflop_dict[instance_name][signal_name]["generate_condition"] = generate_condition
            if flipflops!="":
                flipflop_dict[instance_name][signal_name]["flipflops"] = flipflops
            if factor!="":
                if "factor" not in flipflop_dict[instance_name][signal_name]:
                    flipflop_dict[instance_name][signal_name]["factor"] = factor
                else:
                    flipflop_dict[instance_name][signal_name]["factor"] *= factor
        self.__fix_flipflop_numbers_by_generates(flipflop_dict)
        self.__fix_flipflop_numbers_by_factors(flipflop_dict)
        return flipflop_dict

    def __fix_flipflop_numbers_by_generates(self, flipflop_dict):
        for _, signal_name_dict in flipflop_dict.items():
            for _, signal_prop_dict in signal_name_dict.items():
                if "generate_condition" in signal_prop_dict and (
                   signal_prop_dict["generate_condition"]=="false" or # VHDL simulator
                   signal_prop_dict["generate_condition"]=='0'):      # Verilog simulator
                    signal_prop_dict["flipflops"] = '0'

    def __fix_flipflop_numbers_by_factors(self, flipflop_dict):
        for _, signal_name_dict in flipflop_dict.items():
            for _, signal_prop_dict in signal_name_dict.items():
                if "factor" in signal_prop_dict:
                    signal_prop_dict["flipflops"] = str(int(signal_prop_dict["flipflops"]) * int(signal_prop_dict["factor"]))

    def __calculate_sum_of_flipflops(self, flipflop_dict):
        sum_of_flipflops = 0 # Sum of flipflops in complete design
        for _, signal_name_dict in flipflop_dict.items():
            if not "no-clocked-signal-existent" in signal_name_dict:
                for _, signal_prop_dict in signal_name_dict.items():
                    if signal_prop_dict["flipflops"]!="" and signal_prop_dict["flipflops"]!="?":
                        sum_of_flipflops += int(signal_prop_dict["flipflops"])
        return sum_of_flipflops

    def __create_table_for_log_tab(self, flipflop_dict, sum_of_flipflops):
        instance_names = sorted(list(flipflop_dict.keys()))
        table = []
        # The characters '§', '#', '%' will later all be replaced by the character '|' in self.__indent_equal().
        # Using these characters instead makes it easy to align them:
        table.append("    | Instance-Name § Signal-Name # Flipflops %")
        if self.design.get_language()=="VHDL":
            separator_character = ':'
            index_of_instance_name = -2
        else:
            separator_character = '.'
            index_of_instance_name = -1
        if instance_names:
            indent_init = instance_names[0].count(separator_character)
            for instance_name in instance_names:
                indent_new = instance_name.count(separator_character)
                if separator_character in instance_name:
                    instance_name_short = instance_name.split(separator_character)[index_of_instance_name]
                else:  # This is for simulators which use a different character as separator.
                    instance_name_short = instance_name
                for signal_name in flipflop_dict[instance_name]:
                    if signal_name!="no-clocked-signal-existent":
                        table.append('    | ' + ' '*4*(indent_new - indent_init) + instance_name_short +
                                    " § " + signal_name + " # " + flipflop_dict[instance_name][signal_name]["flipflops"] + " %")
                    else:
                        table.append('    | ' +' '*4*(indent_new - indent_init) + instance_name_short + " § " + " # "  + "          %")
        index_separator1 = self.__indent_equal(table, '§')
        index_separator2 = self.__indent_equal(table, '#')
        index_separator3 = self.__indent_equal(table, '%')
        table_for_log = "\n"
        table_for_log += "    " + '-'*(index_separator3+1-4) + "\n"
        table_for_log += table[0] + "\n"
        table_for_log += "    " + '-'*(index_separator1-4) + '+' + '-'*(index_separator2-index_separator1-1) + '+' + '-'*(index_separator3-index_separator2) + "\n"
        for line_index, line in enumerate(table):
            if line_index!=0:
                table_for_log += line + "\n"
        table_for_log += "    " + '-'*(index_separator3+1-4) + "\n"
        table_for_log += ' '*(index_separator2-19) + "Total flipflop sum:  " + ' '*(index_separator3-index_separator2-len(str(sum_of_flipflops))-3) +str(sum_of_flipflops) +"\n"
        return table_for_log

    def __indent_equal(self, table, separator_character):
        max_index = 0
        for line in table:
            index_of_separator = line.find(separator_character)
            if index_of_separator>max_index:
                max_index = index_of_separator
        for line_index, line in enumerate(table):
            index_of_separator = line.find(separator_character)
            delta = max_index - index_of_separator
            table[line_index] = re.sub(separator_character, ' '*delta + '|', line)
            if separator_character=='%':
                table[line_index] = re.sub(r"\|(\s*)([0-9]+)(\s*)", r"|\3\2\1", table[line_index])
        return max_index

    def __put_table_into_messages_tab(self, table_for_log):
        self.log_tab.insert_line_in_log(table_for_log, state_after_insert="disabled")
        current_working_directory = self.design.get_working_directory()
        if '/' in current_working_directory:
            current_working_directory += '/'
        else:
            current_working_directory += '\\'
        self.log_tab.insert_line_in_log("File with all simulator messages regarding flipflop statistic:\n" +
                                        current_working_directory + "flipflop_statistic_simulator_messages.txt\n\n", state_after_insert="disabled")
