"""
This class is executed when the user starts the compile of a flat or hierarchical design.
If the design is hierarchical, then first a file named hdl_file_list.txt file is generated,
from which the compile command (provided by the user) can extract the names of all the files
which have to be compiled.
If the design is flat, then the user can provide the filenames of all the files, which
have to be compiled, in the compile command.
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

class CompileHDL():
    def __init__(self,
                 window,
                 notebook : notebook_top.NotebookTop,
                 log_tab  : notebook_log_tab.NotebookLogTab,
                 design   : design_data.DesignData,
                 compile_through_hierarchy
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
        if self.compile_through_hierarchy:
            hdl_create_file_list.HdlCreateFileList(self, window, self.log_tab)
        if self.run_compile: # Can be set to False by HdlCreateFileList.
            commands = self.__get_commands_as_list()
            # Run the commands in a asynchronous task, so that the GUI remains responsive:
            runjob = Thread(target=self.__run_commands, args=[commands])
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
            messagebox.showerror("Error in HDL-SCHEM-Editor", "The design was modified.\nHDL must be generated again before compile can run")
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
        if working_directory=="" or working_directory.isspace():
            # The user does not use the working_directory, so no "change directory" command is used and
            # all the results are placed in the current directory.
            return False
        try:
            os.chdir(working_directory)
            return False
        except FileNotFoundError:
            messagebox.showerror("Error in HDL-SCHEM-Editor", "The working directory\n" + working_directory + "\ndoes not exist.")
            return True

    def __put_header_in_message_tab(self):
        self.log_tab.insert_line_in_log("\n+++++++++++++++++++++++++++++++++ " + datetime.today().ctime() +" ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n",
                                                state_after_insert="disabled")
        self.start_time = datetime.now()
        self.log_tab.insert_line_in_log("Working Directory: " + self.window.design.get_working_directory() + "\n",
                                                state_after_insert="disabled")

    def __run_commands(self, commands):
        self.window.config(cursor="watch")
        for command in commands:
            success = self.__execute(command)
            if not success:
                break
        end_time = datetime.now()
        self.log_tab.insert_line_in_log("Finished user commands from Control-Tab after " + str(end_time - self.start_time) + ".\n", state_after_insert="disabled")
        self.window.config(cursor="arrow")

    def __execute(self, command):
        command_array = shlex.split(command) # Does not split quoted sub-strings with blanks.
        self.__replace_variables(command_array)
        if not command_array:
            return False
        for command_part in command_array:
            self.log_tab.insert_line_in_log(command_part+" ", state_after_insert="disabled")
        self.log_tab.insert_line_in_log("\n", state_after_insert="disabled")
        try:
            process = subprocess.Popen(command_array,
                                        text=True, # Decoding is done by Popen.
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT)
            for line in process.stdout: # Terminates when process.stdout is closed.
                if line!="\n": # VHDL report-statements cause empty lines which mess up the protocol.
                    #print("line =", line)
                    self.log_tab.insert_line_in_log(line, state_after_insert="disabled")
        except FileNotFoundError:
            command_string = ""
            for word in command_array:
                command_string += word + " "
            messagebox.showerror("Error in HDL-SCHEM-Editor", "FileNotFoundError caused by compile command:\n" + command_string)
            return False
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
