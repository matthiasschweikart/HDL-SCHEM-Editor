"""
This class creates HDL for a hierachical design through all hierarchies.
"""

import json
import subprocess
from datetime import datetime
from tkinter import messagebox

from codegen import hdl_generate, hdl_generate_functions
from data_io import file_write
from gui import schematic_window


class HdlGenerateHierarchy:  # Called by menu_bar (for generate HDL) or by update_hdl_tab_from().
    """This class creates HDL for a hierachical design through all hierarchies."""

    def __init__(self, root, window, force, write_to_file):
        self.window = window
        self.root = root
        self.force = force
        self.write_to_file = write_to_file
        self.generation_failed = False
        self.sensitivity_message = ""
        if write_to_file:
            self.window.notebook_top.show_tab("Messages")
            self.window.notebook_top.log_tab.log_frame_text.insert_line(
                "\n+++++++++++++++++++++++++++++++++ "
                + datetime.today().ctime()
                + " ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n",
                state_after_insert="disabled",
            )
            self.window.update_idletasks()  # Update to show the messages-tab before the generation starts.

        self.opened_designs_list = []  # Prepare a list to be able to handle recursive hierarchies.
        self._generate_for_window(window)

        if write_to_file:
            self.window.notebook_top.log_tab.log_frame_text.insert_line(
                "HDL generation ready.\n", state_after_insert="disabled"
            )
            self.window.lift()  # Keeps the correct window at top

    def _generate_for_window(self, sub_window):
        self._generate_hdl_for_this_schematic(sub_window)
        self._generate_hdl_for_all_symbols_in_this_schematic(sub_window)

    def _generate_hdl_for_this_schematic(self, sub_window):
        generate_path_value = sub_window.design.get_generate_path_value()
        module_name = sub_window.design.get_module_name()
        architecture_name = sub_window.design.get_architecture_name()
        path_name = sub_window.design.get_path_name()
        if sub_window.design.get_language() == "VHDL":
            if sub_window.design.get_number_of_files() == 1:
                hdlfilename = generate_path_value + "/" + module_name + ".vhd"
                hdlfilename_architecture = None
            else:
                hdlfilename = generate_path_value + "/" + module_name + "_e.vhd"
                hdlfilename_architecture = generate_path_value + "/" + module_name + "_" + architecture_name + ".vhd"
        else:
            hdlfilename = generate_path_value + "/" + module_name + ".v"
            hdlfilename_architecture = None
        if (
            self.force
            or not self.write_to_file  # independent from the following check in the next line
            or hdl_generate_functions.HdlGenerateFunctions.hdl_must_be_generated(
                path_name, hdlfilename, hdlfilename_architecture, show_message=False
            )
            or sub_window.title().endswith("*")
        ):
            hdl_generate.GenerateHDL(
                self,
                sub_window.notebook_top,
                sub_window.design,
                sub_window.notebook_top.hdl_tab,
                self.write_to_file,
                write_message=False,
                hierarchical_generate=True,
            )
            if not self.generation_failed and self.write_to_file:
                self.window.notebook_top.log_tab.log_frame_text.insert_line(
                    "HDL was generated: " + module_name + "\n", state_after_insert="disabled"
                )
                self.window.notebook_top.log_tab.insert_line_in_log(
                    self.sensitivity_message, state_after_insert="disabled"
                )
            else:
                self.generation_failed = False  # Reset the flag when it was set to True.
        else:
            self.window.notebook_top.log_tab.log_frame_text.insert_line(
                "HDL is up to date: " + module_name + "\n", state_after_insert="disabled"
            )

    def _generate_hdl_for_all_symbols_in_this_schematic(self, sub_window):
        symbol_definitions = sub_window.design.get_symbol_definitions()
        symbol_generation_ready = []
        for symbol_definition in symbol_definitions:
            if (
                symbol_definition["filename"] not in symbol_generation_ready
            ):  # Avoid multiple generation of the same symbol, when it is used more than once in the schematic.
                if symbol_definition["filename"].endswith(".hse"):
                    if (
                        symbol_definition["entity_name"]["name"] != sub_window.design.get_module_name()
                    ):  # Break generation loop at recursive instantiations.
                        self._generate_hdl_for_hse_symbol(symbol_definition)
                elif symbol_definition["filename"].endswith(".hfe") and self.write_to_file:
                    self._generate_hdl_for_hfe_symbol(sub_window, symbol_definition)
                symbol_generation_ready.append(symbol_definition["filename"])

    def _generate_hdl_for_hse_symbol(self, symbol_definition):
        sub_window = None
        for opened_window in schematic_window.SchematicWindow.open_window_dict:
            if opened_window.design.get_path_name() == symbol_definition["filename"]:
                sub_window = opened_window
                # The method _generate_hdl_for_hse_symbol is called also
                # when schematic_window._restore_to_version_before_changes is called.
                # In this case no HDL is generated but only the link-dictionary is filled and
                # therefore write_to_file=False.
                # FileWrite is needed, when HDL is generated, so that all submodules are also saved.
                # But when filling the link-dictionary, the sub-modules are not allowed to be written,
                # because it is not clear if the changes shall be kept.
                if sub_window.title().endswith("*") and self.write_to_file:
                    file_write.FileWrite(
                        sub_window, sub_window.design, "save"
                    )  # Write to guarantee consistency between source and HDL.
        if not sub_window:  # will happen when link-dictionary is filled the first time.
            architecture_name = symbol_definition["architecture_name"]
            sub_window = schematic_window.SchematicWindow.open_subwindow(
                self.root, symbol_definition["filename"], architecture_name
            )
        sub_module_name = sub_window.design.get_module_name()
        if (
            sub_module_name != ""  # File Read was a success, so HDL can be generated.
            and sub_module_name not in self.opened_designs_list  # Continue only if no recursive loop exists.
        ):
            self.opened_designs_list.append(sub_module_name)
            self._generate_for_window(sub_window)

    def _generate_hdl_for_hfe_symbol(self, sub_window, symbol_definition):
        # Update parameters which might have been changed since instantiation of the symbol:
        try:
            with open(symbol_definition["filename"], encoding="utf-8") as fileobject:
                data_read = fileobject.read()
            hdl_fsm_editor_design_dictionary_sub = json.loads(data_read)
            generate_path_value_of_fsm = hdl_fsm_editor_design_dictionary_sub["generate_path"]
            number_of_files_of_fsm = hdl_fsm_editor_design_dictionary_sub["number_of_files"]
        except FileNotFoundError:
            messagebox.showerror(
                "Warning",
                "File " + symbol_definition["filename"] + " could not be found.\nCheck if HDL already exists may fail.",
            )
            generate_path_value_of_fsm = symbol_definition["generate_path_value"]
            number_of_files_of_fsm = symbol_definition["number_of_files"]
        if symbol_definition["language"] == "VHDL":
            if number_of_files_of_fsm == 1:
                hdlfilename = generate_path_value_of_fsm + "/" + symbol_definition["entity_name"]["name"] + ".vhd"
            else:
                hdlfilename = generate_path_value_of_fsm + "/" + symbol_definition["entity_name"]["name"] + "_e.vhd"
        else:
            hdlfilename = generate_path_value_of_fsm + "/" + symbol_definition["entity_name"]["name"] + ".v"
        path_name = symbol_definition["filename"]
        if (
            self.force
            or hdl_generate_functions.HdlGenerateFunctions.hdl_must_be_generated(
                path_name, hdlfilename, hdlfilename_architecture=None, show_message=False
            )
            or sub_window.title().endswith("*")
        ):
            command_array = [
                self.window.design.get_hfe_cmd(),
                "--generate-hdl",
                "--no-version-check",
                "--no-message",
                path_name,
            ]
            try:
                self.window.notebook_top.log_tab.log_frame_text.insert_line(
                    "Run HDL-FSM-Editor ...\n", state_after_insert="disabled"
                )
                # For not clear reasons update_idletasks() did not fill the message-tab in a continuous manner:
                self.window.notebook_top.log_tab.log_frame_text.update()
                process = subprocess.Popen(
                    command_array,
                    text=True,  # Decoding is done by Popen.
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
                for line in process.stdout:  # Terminates when process.stdout is closed.
                    if line != "\n":  # VHDL report-statements cause empty lines which mess up the protocol.
                        # print("line =", line)
                        self.window.notebook_top.log_tab.log_frame_text.insert_line(line, state_after_insert="disabled")
                    self.window.notebook_top.log_tab.log_frame_text.update_idletasks()
            except FileNotFoundError:
                command_string = ""
                for word in command_array:
                    command_string += word + " "
                messagebox.showerror(
                    "Error in HDL-SCHEM-Editor", "FileNotFoundError caused by compile command:\n" + command_string
                )
                return
            except PermissionError:
                command_string = ""
                for word in command_array:
                    command_string += word + " "
                messagebox.showerror(
                    "Error in HDL-SCHEM-Editor", "PermissionError caused by compile command:\n" + command_string
                )
                return
            self.window.notebook_top.log_tab.log_frame_text.insert_line(
                "HDL was generated: " + symbol_definition["entity_name"]["name"] + "\n", state_after_insert="disabled"
            )
        else:
            self.window.notebook_top.log_tab.log_frame_text.insert_line(
                "HDL is up to date: " + symbol_definition["entity_name"]["name"] + "\n", state_after_insert="disabled"
            )
