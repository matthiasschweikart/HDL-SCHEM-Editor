"""
HDL Generation and Link-Dictionary Filling
"""

import os
import re
from datetime import datetime
from pathlib import Path
from tkinter import messagebox

from codegen import (
    hdl_generate_architecture,
    hdl_generate_entity,
    hdl_generate_functions,
    hdl_generate_module_content,
    hdl_generate_module_interface,
    hdl_generate_sort_elements,
    sensitivity_check_hse,
)
from elements import generate_frame
from gui import notebook_hdl_tab


class GenerateHDL:
    """This class generates the HDL-code for a design and fills the link-dictionary with the HDL-line-numbers."""

    def __init__(
        self,
        parent,
        notebook,  # : notebook_top.NotebookTop,
        design,  # : design_data.DesignData,
        hdl_tab: notebook_hdl_tab.NotebookHdlTab,
        write_to_file,  # write_to_file=False, when GenerateHDL is used for building the link-dictionary.
        write_message=False,
        hierarchical_generate=False,
    ):
        self.notebook = notebook
        self.design = design
        self.hdl_tab = hdl_tab
        if write_to_file and self._information_in_control_tab_is_missing_or_wrong():
            parent.generation_failed = True
            return
        if self._edits_are_running():
            parent.generation_failed = True
            return
        file_name, file_name_architecture = self.design.get_file_names()
        sorted_canvas_ids_for_hdl = hdl_generate_sort_elements.SortElements(
            notebook, self.design, write_to_file
        ).get_sorted_list_of_schematic_elements()
        [
            input_decl,
            output_decl,
            inout_decl,
            signal_decl,
            instance_connection_definitions,
            block_list,
            component_declarations_dict,
            embedded_configurations,
            generic_mapping_dict,
            generate_dictionary,
            libraries_from_instance_configuration,
        ] = self._get_data_from_graphic()
        if self.design.get_language() == "VHDL":
            header, entity, architecture = self._generate_vhdl(
                input_decl,
                output_decl,
                inout_decl,
                signal_decl,
                instance_connection_definitions,
                block_list,
                component_declarations_dict,
                embedded_configurations,
                libraries_from_instance_configuration,
                generic_mapping_dict,
                sorted_canvas_ids_for_hdl,
                generate_dictionary,
                file_name,
                file_name_architecture,
            )
        else:  # "SystemVerilog" or "Verilog"
            header, entity, architecture = self._generate_verilog(
                input_decl,
                output_decl,
                inout_decl,
                signal_decl,
                instance_connection_definitions,
                block_list,
                component_declarations_dict,
                generic_mapping_dict,
                sorted_canvas_ids_for_hdl,
                generate_dictionary,
                file_name,
            )
        if write_to_file:
            self._write_hdl_file(file_name, file_name_architecture, header, entity, architecture)
            hdl_file_name = file_name if file_name_architecture == "" else file_name_architecture
            self.hdl_tab.update_hdl_tab_from(self.design.create_design_dictionary_of_active_architecture())
            if write_message:
                notebook.log_tab.log_frame_text.insert_line(
                    "\n+++++++++++++++++++++++++++++++++ "
                    + datetime.today().ctime()
                    + " ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n",
                    state_after_insert="disabled",
                )
                notebook.log_tab.log_frame_text.insert_line(
                    "HDL was generated: " + self.design.get_module_name() + "\n", state_after_insert="disabled"
                )
                if hierarchical_generate:
                    notebook.show_tab("Messages")
                else:
                    notebook.show_tab("generated HDL")
            messages = sensitivity_check_hse.SensitivityCheckHse(
                hdl_file_name, input_decl, inout_decl, signal_decl, self.design
            ).get_messages()
            message_string = ""
            if messages:
                for message in messages:
                    message_string += message + "\n"
                notebook.log_tab.insert_line_in_log(message_string, state_after_insert="disabled")
                notebook.show_tab("Messages")
            parent.sensitivity_message = message_string  # Message for the toplevel window

    def _information_in_control_tab_is_missing_or_wrong(self):
        module_name = self.design.get_module_name()
        generate_path_value = self.design.get_generate_path_value()
        if module_name.isspace() or module_name == "":
            messagebox.showerror(
                "Error in HDL-SCHEM-Editor",
                "HDL-generation is not possible,\nbecause no module name is specified in the Control-Tab.",
            )
            return True
        if generate_path_value.isspace() or generate_path_value == "":
            messagebox.showerror(
                "Error in HDL-SCHEM-Editor",
                "HDL-generation for module "
                + module_name
                + " is not possible,\n"
                + "because no path for the generation of the HDL-files is specified in the Control-Tab.",
            )
            return True
        path = Path(generate_path_value)
        if not path.exists():
            messagebox.showerror(
                "Error in HDL-SCHEM-Editor",
                "HDL-generation for module "
                + module_name
                + " is not possible, because the specified path\n"
                + generate_path_value
                + "\nfor the generation of the HDL-files does not exist.\n"
                + 'See "Path for generated HDL" in the Control-Tab.',
            )
            return True
        return False

    def _edits_are_running(self):
        if self.design.get_block_edit_list():
            messagebox.showerror(
                "Error in HDL-SCHEM-Editor",
                "HDL-generation is not possible,\nbecause a block edit of module "
                + self.design.get_module_name()
                + " is still open.",
            )
            return True
        if self.design.get_signal_name_edit_list():
            messagebox.showerror(
                "Error in HDL-SCHEM-Editor",
                "HDL-generation is not possible,\nbecause a signal name edit of module "
                + self.design.get_module_name()
                + " is still open.",
            )
            return True
        if self.design.get_edit_line_edit_list():
            messagebox.showerror(
                "Error in HDL-SCHEM-Editor",
                "HDL-generation is not possible,\nbecause an edit dialog of module "
                + self.design.get_module_name()
                + " is still open.",
            )
            return True
        if self.design.get_edit_text_edit_list():
            messagebox.showerror(
                "Error in HDL-SCHEM-Editor",
                "HDL-generation is not possible,\nbecause an edit dialog of module "
                + self.design.get_module_name()
                + " is still open.",
            )
            return True
        return False

    def _get_data_from_graphic(self):
        (
            connector_location_list,  # List of dicts {"type" : "input"|"output"|"inout", "coords" : [x1, y1, ...]}
            wire_location_list,  # List of dictionaries {"declaration" : <string>, "coords" : [x1, y1, ...]}
            block_list,  # Dictionary of {<Canvas-ID>: "HDL", <Canvas-ID>: "HDL", ...]
            symbol_definition_list,  # List: [symbol_definition1, symbol_definition2, ...]
            generate_definition_list,  # List: [generate_definition1, generate_definition2, ...]
        ) = self.design.get_connection_data()
        (
            all_pins_definition_list,
            component_declarations_dict,
            embedded_configurations,
            generic_mapping_dict,
            libraries_from_instance_configuration,
        ) = hdl_generate_functions.HdlGenerateFunctions.extract_data_from_symbols(symbol_definition_list)
        generate_dictionary = self._extract_conditions_from_generates(generate_definition_list)
        pin_and_port_location_list = connector_location_list + all_pins_definition_list
        input_decl, output_decl, inout_decl, signal_decl, instance_connection_definitions = (
            GenerateHDL.create_declarations(
                self.design.get_language(), self.design.get_grid_size(), pin_and_port_location_list, wire_location_list
            )
        )
        return [
            input_decl,
            output_decl,
            inout_decl,
            signal_decl,
            instance_connection_definitions,
            block_list,
            component_declarations_dict,
            embedded_configurations,
            generic_mapping_dict,
            generate_dictionary,
            libraries_from_instance_configuration,
        ]

    def _extract_conditions_from_generates(self, generate_definition_list):
        generate_dictionary = {}
        for generate_definition in generate_definition_list:
            canvas_id, condition = generate_frame.GenerateFrame.get_canvas_id_and_condition_from_generate_definition(
                generate_definition
            )
            generate_dictionary[canvas_id] = condition
        return generate_dictionary

    def _generate_vhdl(
        self,
        input_decl,
        output_decl,
        inout_decl,
        signal_decl,
        instance_connection_definitions,
        block_list,
        component_declarations_dict,
        embedded_configurations,
        libraries_from_instance_configuration,
        generic_mapping_dict,
        sorted_canvas_ids_for_hdl,
        generate_dictionary,
        file_name,
        file_name_architecture,
    ):
        date_string = " at " + datetime.today().ctime() if self.design.get_include_timestamp_in_hdl() else ""
        header = "-- Created by HDL-SCHEM-Editor" + date_string + "\n"
        entity = hdl_generate_entity.GenerateEntity(
            self.design, input_decl, output_decl, inout_decl, file_name
        ).get_entity()
        if self.design.get_number_of_files() == 1:
            start_line_number_of_architecture = (
                1 + header.count("\n") + entity.count("\n") + 1
            )  # first "+1": filename of HDL-file; second "+1": first line for architecture
        else:
            start_line_number_of_architecture = (
                1 + header.count("\n") + 1
            )  # first "+1": filename of architecture; second "+1": first line for architecture
            file_name = file_name_architecture
        architecture = hdl_generate_architecture.GenerateArchitecture(
            self.design,
            self.notebook.diagram_tab.architecture_name,
            signal_decl,
            instance_connection_definitions,
            block_list,
            component_declarations_dict,
            embedded_configurations,
            libraries_from_instance_configuration,
            generic_mapping_dict,
            sorted_canvas_ids_for_hdl,
            generate_dictionary,
            file_name,
            start_line_number_of_architecture,
        ).get_architecture()
        return header, entity, architecture

    def _generate_verilog(
        self,
        input_decl,
        output_decl,
        inout_decl,
        signal_decl,
        instance_connection_definitions,
        block_list,
        component_declarations_dict,
        generic_mapping_dict,
        sorted_canvas_ids_for_hdl,
        generate_dictionary,
        file_name,
    ):
        header = "// Created by HDL-SCHEM-Editor at " + datetime.today().ctime() + "\n"
        module_interface = hdl_generate_module_interface.GenerateModuleInterface(
            self.design, input_decl, output_decl, inout_decl, file_name
        ).get_interface()
        start_line_number_of_content = module_interface.count("\n") + 1
        module_content = hdl_generate_module_content.GenerateModuleContent(
            self.design,
            signal_decl,
            instance_connection_definitions,
            block_list,
            component_declarations_dict,
            generic_mapping_dict,
            sorted_canvas_ids_for_hdl,
            generate_dictionary,
            file_name,
            start_line_number_of_content,
        ).get_content()
        return header, module_interface, module_content

    def _write_hdl_file(self, file_name, file_name_architecture, header, entity, architecture) -> None:
        _, name_of_file = os.path.split(file_name)
        comment_string = "--" if file_name.endswith(".vhd") else "//"
        if file_name_architecture == "":  # VHDL all in 1 file or Verilog
            content = comment_string + " Filename: " + name_of_file + "\n"
            content += header + entity + architecture
            with open(file_name, "w", encoding="utf-8") as fileobject:
                fileobject.write(content)
        else:
            content1 = "-- Filename: " + name_of_file + "\n"
            content1 += header
            content1 += entity
            with open(file_name, "w", encoding="utf-8") as fileobject_entity:
                fileobject_entity.write(content1)
            _, name_of_architecture_file = os.path.split(file_name_architecture)
            content = "-- Filename: " + name_of_architecture_file + "\n"
            content += header
            content += architecture
            with open(file_name_architecture, "w", encoding="utf-8") as fileobject_architecture:
                fileobject_architecture.write(content)
        return

    def _add_line_numbers(self, text):
        text_lines = text.split("\n")
        text_length_as_string = str(len(text_lines))
        number_of_needed_digits_as_string = str(len(text_length_as_string))
        content_with_numbers = ""
        for line_number, line in enumerate(text_lines, start=1):
            content_with_numbers += (
                format(line_number, "0" + number_of_needed_digits_as_string + "d") + ": " + line + "\n"
            )
        return content_with_numbers

    @classmethod
    def create_declarations(cls, language, grid_size, pin_and_port_location_list, wire_location_list):
        """Creates the declarations for the HDL-code from the graphic."""
        input_declarations = []
        output_declarations = []
        inout_declarations = []
        wire_declarations_changed_to_port_declarations = []
        signal_declarations = []
        instance_connection_definitions = []
        fill = ""
        for pin_and_port_location in pin_and_port_location_list:
            if pin_and_port_location["type"] == "inout":  # if at least 1 "inout" is present, then fill will be changed.
                fill = " " * 2
                break
        for wire_location_list_entry in wire_location_list:
            signal_declaration_is_needed = True
            declaration_with_slices = wire_location_list_entry["declaration"]
            signal_name, _, signal_type, comment, initialization, _ = (
                hdl_generate_functions.HdlGenerateFunctions.split_declaration(
                    wire_location_list_entry["declaration"], language
                )
            )
            if comment != "":
                comment = " " + comment
            if initialization != "":
                initialization = " " + initialization
            if language == "VHDL":
                wire_location_list_entry["declaration"] = signal_name + " : " + signal_type + initialization + comment
            else:
                wire_location_list_entry["declaration"] = signal_type + " " + signal_name + comment
            for pin_and_port_location in pin_and_port_location_list:
                pin_is_connected_to_wire = bool(
                    (
                        abs(pin_and_port_location["coords"][0] - wire_location_list_entry["coords"][0])
                        < 0.1 * grid_size
                        and abs(pin_and_port_location["coords"][1] - wire_location_list_entry["coords"][1])
                        < 0.1 * grid_size
                    )
                    or (
                        abs(pin_and_port_location["coords"][0] - wire_location_list_entry["coords"][-2])
                        < 0.1 * grid_size
                        and abs(pin_and_port_location["coords"][1] - wire_location_list_entry["coords"][-1])
                        < 0.1 * grid_size
                    )
                )
                if pin_is_connected_to_wire:
                    if (
                        pin_and_port_location["type"] == "input"
                    ):  # Transform the wire declaration into a input port declaration.
                        if language == "VHDL":
                            input_declaration = re.sub(
                                r":[ ]*(.*)", r": in  \1" + fill, wire_location_list_entry["declaration"]
                            )
                        else:
                            input_declaration = re.sub(
                                "^wire |^reg |^logic ", "input  ", wire_location_list_entry["declaration"]
                            )  # "reg" should not occur.
                        input_declarations.append(input_declaration)
                        wire_declarations_changed_to_port_declarations.append(wire_location_list_entry["declaration"])
                        signal_declaration_is_needed = False
                    elif (
                        pin_and_port_location["type"] == "output"
                    ):  # Transform the wire declaration into a output port declaration.
                        if language == "VHDL":
                            output_declaration = re.sub(
                                r":[ ]*(.*)", r": out \1" + fill, wire_location_list_entry["declaration"]
                            )
                        else:
                            output_declaration = re.sub("^", "output ", wire_location_list_entry["declaration"])
                        output_declarations.append(output_declaration)
                        wire_declarations_changed_to_port_declarations.append(wire_location_list_entry["declaration"])
                        signal_declaration_is_needed = False
                    elif (
                        pin_and_port_location["type"] == "inout"
                    ):  # Transform the wire declaration into a inout port declaration.
                        if language == "VHDL":
                            inout_declaration = re.sub(
                                r":[ ]*(.*)", r": inout \1", wire_location_list_entry["declaration"]
                            )
                        else:
                            inout_declaration = re.sub("^", "inout  ", wire_location_list_entry["declaration"])
                        inout_declarations.append(inout_declaration)
                        wire_declarations_changed_to_port_declarations.append(wire_location_list_entry["declaration"])
                        signal_declaration_is_needed = False
                    else:  # pin_and_port_location["type"]==<entity-call>
                        instance_connection_definition = {}  # Describes the connections to the ports of a instance.
                        instance_connection_definition["declaration"] = (
                            declaration_with_slices  # Declaration of the signal connected to a entity-port
                        )
                        instance_connection_definition["entity_name"] = pin_and_port_location[
                            "type"
                        ]  # Complete entity call
                        instance_connection_definition["architecture_name"] = pin_and_port_location[
                            "architecture_name"
                        ]  # Used by highlighting through hierarchy.
                        instance_connection_definition["instance_name"] = pin_and_port_location[
                            "instance_name"
                        ]  # Instance-Name of the entity
                        instance_connection_definition["port_declaration"] = pin_and_port_location[
                            "port_declaration"
                        ]  # Declaration of the port, the signal is connected to
                        instance_connection_definition["canvas_id"] = pin_and_port_location[
                            "canvas_id"
                        ]  # Canvas-ID of the rectangle of the symbol,
                        instance_connection_definitions.append(
                            instance_connection_definition
                        )  # used as reference in canvas_dictionary.
                        # print("instance_connection_definition =", instance_connection_definition)
            if signal_declaration_is_needed and wire_location_list_entry["declaration"] not in signal_declarations:
                signal_declarations.append(wire_location_list_entry["declaration"])
        port_names = []
        for wire_declaration in wire_declarations_changed_to_port_declarations:
            port_name, _, _, _, _, _ = hdl_generate_functions.HdlGenerateFunctions.split_declaration(
                wire_declaration, language
            )
            port_names.append(port_name)
        signal_declarations_reduced = []
        for signal_declaration in signal_declarations:
            # remove all but signal name from signal_declaration
            signal_name, _, _, _, _, _ = hdl_generate_functions.HdlGenerateFunctions.split_declaration(
                signal_declaration, language
            )
            if signal_name not in port_names:
                signal_declarations_reduced.append(signal_declaration)
        return (
            input_declarations,
            output_declarations,
            inout_declarations,
            signal_declarations_reduced,
            instance_connection_definitions,
        )
