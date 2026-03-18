"""
The class DesignDataSelector pretends to be a DesignData object.
It has all methods, which are implemented in DesignData.
In this way all information which has to be stored in or read from a DesignData object is passed
through DesignDataSelector. The DesignDataSelector object has additional methods which are only used for handling the
alternative architectures of a VHDL schematic. When a new architecture is added, then the DesignDataSelector object
reads all informations which are needed for restoring the old architecture and stores it in self.return_dictionaries.
Then a new and empty DesignData object is created and filled with all information which is identically for all
architectures. The old DesignData object is destroyed when the new DesignData object is created.
When it is switched back to the old architecture, then first the all data from the actual architecture is copied
into self.return_dictionaries. Then the schematic of the old architecture is restored by reading the data from
the self.return_dictionaries and creating a new schematic for the old architecture.
Renaming and deleting an architecture is also supported.
Methods for writing/reading the schematic into/from a file with all architectures or only a single one are provided.
"""

import json
from tkinter import messagebox

from codegen import hdl_generate_through_hierarchy, list_separation_check
from data_io import design_data


class DesignDataSelector:
    """
    This class pretends to be a DesignData object and can switch beteween different DesignData objects for
    different architectures of a VHDL schematic.
    """

    def __init__(self, root, window):
        self.root = root
        self.window = window
        self.active_data = design_data.DesignData(self.root, self.window)
        self.return_dictionaries = {}

    def create_new_and_empty_schematic(self, old_architecture):
        """Creates a new and empty schematic, but first stores all information of the
        old architecture in self.return_dictionaries."""
        self.window.write_data_creator_ref.zoom_graphic_to_standard_size(
            self.window, self.window.design.get_font_size()
        )
        design_dictionary = self.active_data.create_design_dictionary()
        design_dictionary = self.window.write_data_creator_ref.round_numbers(design_dictionary)
        self.return_dictionaries[old_architecture] = design_dictionary
        path_name = (
            self.active_data.get_path_name()
        )  # Remember the path_name, because it will get lost by creating a new DesignData object.
        self.active_data = design_data.DesignData(self.root, self.window)
        self.active_data.set_path_name(path_name)  # Restore the path_name.
        self.window.notebook_top.control_tab.copy_all_information_from_tab_in_empty_design_data()
        self.window.notebook_top.interface_tab.copy_all_information_from_tab_in_empty_design_data()
        self.window.notebook_top.internals_tab.clear()
        self.window.notebook_top.diagram_tab.clear_canvas_for_new_schematic()

    def open_existing_schematic(self, old_architecture, new_architecture):
        """Opens the schematic of the new architecture, but first stores all information of the old architecture."""
        self.create_new_and_empty_schematic(old_architecture)  # old_architecture will be stored in return_dictionaries
        # For the update of the diagram_tab it is not possible to use "update_diagram_tab_from", which is used when a
        # file is read. The reason is, that at file-reads the design-dictionary is extended by the
        # entry "architecture_list". This is necessary, because only 1 design-dictionary is given
        # to "update_diagram_tab_from", but the architecture-select-combobox must be configured.
        # Here again the design-dictionary self.return_dictionaries[new_architecture] does not have the
        # entry "architecture_list". So when "update_diagram_tab_from" would be called, an exception would happen.
        # So "update_diagram_tab" is used, which does not access the entry "architecture_list".
        # An alternative solution would have been adding "architecture_list" to all entries of self.return_dictionaries.
        # But then it would have been difficult to keep all entries consistent.
        self.window.notebook_top.control_tab.update_control_tab_from(self.return_dictionaries[new_architecture])
        self.window.notebook_top.interface_tab.update_interface_tab_from(self.return_dictionaries[new_architecture])
        self.window.notebook_top.internals_tab.update_internals_tab_from(self.return_dictionaries[new_architecture])
        self.window.notebook_top.diagram_tab.update_diagram_tab(
            self.return_dictionaries[new_architecture], push_design_to_stack=True
        )
        self.window.notebook_top.hdl_tab.update_hdl_tab_from(self.return_dictionaries[new_architecture])
        self.window.notebook_top.diagram_tab.view_all()
        self.window.notebook_top.show_tab("Diagram")
        hdl_generate_through_hierarchy.HdlGenerateHierarchy(self.root, self.window, force=False, write_to_file=False)

    def delete_schematic(self, old_architecture, new_architecture):
        """Deletes a schematic."""
        self.open_existing_schematic(old_architecture, new_architecture)
        del self.return_dictionaries[old_architecture]

    def schematic_was_renamed(self, old_architecture):
        "Renames a schematic, which means that the entry in self.return_dictionaries is removed."
        if old_architecture in self.return_dictionaries:
            del self.return_dictionaries[old_architecture]

    def get_design_dictionary_for_all_architectures(self):  # used by file_write
        """Returns a list of dictionaries"""
        save_dict = self.active_data.create_design_dictionary()
        if len(self.return_dictionaries) == 0:
            return save_dict
        if save_dict["architecture_name"] != self.window.notebook_top.diagram_tab.architecture_name:
            messagebox.showerror(
                "Error at file-write in get_design_dictionary_for_all_architectures:",
                "Architecturenames differ: "
                + save_dict["architecture_name"]
                + " "
                + self.window.notebook_top.diagram_tab.architecture_name,
            )
        self.return_dictionaries[self.window.notebook_top.diagram_tab.architecture_name] = save_dict
        self.return_dictionaries["active__architecture"] = self.window.notebook_top.diagram_tab.architecture_name
        if "" in self.return_dictionaries:
            del self.return_dictionaries[
                ""
            ]  # Remove entry with empty key, was created by old version of HDL-SCHEM-Editor
        return self.return_dictionaries

    def extract_design_dictionary_of_active_architecture(self, new_dict, architecture_name):  # used by file_read
        """Returns the design dictionary of the active architecture."""
        # When a design is read in, then the architecture_name is "".
        # When a symbol is updated or when a sub_window is opened (generating HDL, highlighting through hierarchy),
        # then the architecture name is not empty.
        if "active__architecture" in new_dict:
            if architecture_name == "":
                active_architecture = new_dict["active__architecture"]
            elif architecture_name in new_dict:
                active_architecture = architecture_name
            else:
                active_architecture = new_dict["active__architecture"]
                messagebox.showerror(
                    "Error at file read",
                    'Did not find the architecture "'
                    + architecture_name
                    + '" of the module '
                    + new_dict[active_architecture]["module_name"]
                    + ', "'
                    + active_architecture
                    + '" is used instead.',
                )
            del new_dict["active__architecture"]
            architecture_list = [*new_dict]
            self.return_dictionaries = new_dict
            # Here a new, second dictionary object is created instead of using only one
            # by "dict_for_file_read = new_dict[active_architecture]".
            # The new_dict dictionary read from file, is stored in return_dictionaries.
            # The dictionary "dict_for_file_read" for all the update-methods is a different dictionary.
            # This separation is necessary, as at switching from VHDL to Verilog first the compile_cmd is updated
            # in the return_dictionaries by the default compile_cmd (see store_compile_cmd() in this class).
            # And if there would be still only one dictionary, then this update would also have updated the
            # compile_cmd in dict_for_file_read and in this way removed the command stored in file.
            dict_for_file_read = json.loads(
                json.dumps(new_dict[active_architecture])
            )  # This new dictionary is handed over to update-functions for all tabs.
            dict_for_file_read["architecture_list"] = architecture_list
        else:
            if (
                "architecture_name" not in new_dict
            ):  # Old versions of HDL-SCHEM-Editor do not store the architecture name.
                new_dict["architecture_name"] = "struct"
            active_architecture = new_dict["architecture_name"]
            architecture_list = [active_architecture]
            self.return_dictionaries[active_architecture] = new_dict  # not clear if needed
            self.return_dictionaries[""] = new_dict  # Verilog designs do have an empty architecture name.
            dict_for_file_read = new_dict
            dict_for_file_read["architecture_list"] = [active_architecture]
        return dict_for_file_read

    def create_design_dictionary_of_active_architecture(self):
        """Returns the design dictionary of the active architecture."""

        return self.active_data.create_design_dictionary()

    def store_new_module_name(self, var_name, signal_design_change):
        """Stores the new module name in all dictionaries."""
        self.active_data.store_new_module_name(var_name, signal_design_change)
        for architecture in self.return_dictionaries:
            if architecture != "active__architecture":
                self.return_dictionaries[architecture]["module_name"] = var_name.get()

    def store_new_architecture_name(self, architecture_name, signal_design_change):
        """Stores the new architecture name in all dictionaries."""
        self.active_data.store_new_architecture_name(architecture_name, signal_design_change)

    def store_new_language(self, var_name, signal_design_change):
        """Stores the new language in all dictionaries."""
        self.active_data.store_new_language(var_name, signal_design_change)
        for architecture in self.return_dictionaries:
            if architecture != "active__architecture":
                self.return_dictionaries[architecture]["language"] = var_name.get()

    def store_generate_path_value(self, var_name, signal_design_change):
        """Stores the new generate path value in all dictionaries."""
        self.active_data.store_generate_path_value(var_name, signal_design_change)
        for architecture in self.return_dictionaries:
            if architecture != "active__architecture":
                self.return_dictionaries[architecture]["generate_path"] = var_name.get()

    def store_number_of_files(self, var_name, signal_design_change):
        """Stores the new number of files in all dictionaries."""
        self.active_data.store_number_of_files(var_name, signal_design_change)
        for architecture in self.return_dictionaries:
            if architecture != "active__architecture":
                self.return_dictionaries[architecture]["number_of_files"] = var_name.get()

    def store_compile_cmd(self, var_name, signal_design_change):
        """Stores the new compile command in all dictionaries."""
        self.active_data.store_compile_cmd(var_name, signal_design_change)
        for architecture in self.return_dictionaries:
            if architecture != "active__architecture":
                self.return_dictionaries[architecture]["compile_cmd"] = var_name.get()

    def store_compile_hierarchy_cmd(self, var_name, signal_design_change):
        """Stores the new compile hierarchy command in all dictionaries."""
        self.active_data.store_compile_hierarchy_cmd(var_name, signal_design_change)
        for architecture in self.return_dictionaries:
            if architecture != "active__architecture":
                self.return_dictionaries[architecture]["compile_hierarchy_cmd"] = var_name.get()

    def store_new_edit_command(self, var_name, signal_design_change):
        """Stores the new edit command in all dictionaries."""
        self.active_data.store_new_edit_command(var_name, signal_design_change)
        for architecture in self.return_dictionaries:
            if architecture != "active__architecture":
                self.return_dictionaries[architecture]["edit_command"] = var_name.get()

    def store_new_hfe_command(self, var_name, signal_design_change):
        """Stores the new HFE command in all dictionaries."""
        self.active_data.store_new_hfe_command(var_name, signal_design_change)
        for architecture in self.return_dictionaries:
            if architecture != "active__architecture":
                self.return_dictionaries[architecture]["hfe_command"] = var_name.get()

    def store_module_library(self, var_name, signal_design_change):
        """Stores the new module library in all dictionaries."""
        self.active_data.store_module_library(var_name, signal_design_change)
        for architecture in self.return_dictionaries:
            if architecture != "active__architecture":
                self.return_dictionaries[architecture]["module_library"] = var_name.get()

    def store_additional_sources(self, var_name, signal_design_change):
        """Stores the new additional sources in all dictionaries."""
        self.active_data.store_additional_sources(var_name, signal_design_change)
        for architecture in self.return_dictionaries:
            if architecture != "active__architecture":
                self.return_dictionaries[architecture]["additional_sources"] = var_name.get()

    def store_working_directory(self, var_name, signal_design_change):
        """Stores the new working directory in all dictionaries."""
        self.active_data.store_working_directory(var_name, signal_design_change)
        for architecture in self.return_dictionaries:
            if architecture != "active__architecture":
                self.return_dictionaries[architecture]["working_directory"] = var_name.get()

    def store_include_timestamp_in_hdl(self, var_name, signal_design_change):
        """Stores the new include timestamp in HDL setting."""
        self.active_data.store_include_timestamp_in_hdl(var_name, signal_design_change)

    def store_signal_name_font(self, signal_name_font, signal_design_change):
        """Stores the new signal name font."""
        self.active_data.store_signal_name_font(signal_name_font, signal_design_change)

    def store_font_size(self, font_size, signal_design_change):
        """Stores the new font size."""
        self.active_data.store_font_size(font_size, signal_design_change)

    def store_grid_size(self, grid_size, signal_design_change):
        """Stores the new grid size."""
        self.active_data.store_grid_size(grid_size, signal_design_change)

    def store_connector_size(self, connector_size, signal_design_change):
        """Stores the new connector size."""
        self.active_data.store_connector_size(connector_size, signal_design_change)

    def store_visible_center_point(self, visible_center_point, push_design_to_stack, signal_design_change):
        """Stores the new visible center point."""
        self.active_data.store_visible_center_point(visible_center_point, push_design_to_stack, signal_design_change)

    def store_in_text_dictionary(self, text_name, text, signal_design_change):
        """Stores the new text."""
        self.active_data.store_in_text_dictionary(text_name, text, signal_design_change)
        if text_name in ["interface_packages", "interface_generics"]:
            for architecture in self.return_dictionaries:
                if architecture != "active__architecture":
                    self.return_dictionaries[architecture]["text_dictionary"][text_name] = text

    def store_interface_in_canvas_dictionary(
        self, canvas_id, reference, connector_type, location, orientation, push_design_to_stack, signal_design_change
    ):
        """Stores the new interface."""
        self.active_data.store_interface_in_canvas_dictionary(
            canvas_id, reference, connector_type, location, orientation, push_design_to_stack, signal_design_change
        )

    def store_wire_id(self, wire_id):
        """Stores the new wire id."""
        self.active_data.store_wire_id(wire_id)

    def store_block_id(self, block_id):
        """Stores the new block id."""
        self.active_data.store_block_id(block_id)

    def store_generate_frame_id(self, generate_frame_id):
        """Stores the new generate frame id."""
        self.active_data.store_generate_frame_id(generate_frame_id)

    def store_instance_id(self, instance_id):
        """Stores the new instance id."""
        self.active_data.store_instance_id(instance_id)

    def store_wire_in_canvas_dictionary(
        self, canvas_id, reference, coords, tags, arrow, width, push_design_to_stack, signal_design_change
    ):
        """Stores the new wire in canvas dictionary."""
        self.active_data.store_wire_in_canvas_dictionary(
            canvas_id, reference, coords, tags, arrow, width, push_design_to_stack, signal_design_change
        )

    def store_dot_in_canvas_dictionary(self, canvas_id, reference, coords, push_design_to_stack):
        """Stores the new dot in canvas dictionary."""
        self.active_data.store_dot_in_canvas_dictionary(canvas_id, reference, coords, push_design_to_stack)

    def store_signal_name_in_canvas_dictionary(
        self, canvas_id, reference, coords, angle, text, wire_tag, push_design_to_stack, signal_design_change
    ):
        """Stores the new signal name in canvas dictionary."""
        self.active_data.store_signal_name_in_canvas_dictionary(
            canvas_id, reference, coords, angle, text, wire_tag, push_design_to_stack, signal_design_change
        )

    def store_block_in_canvas_dictionary(
        self,
        canvas_id,
        reference,
        rect_coords,
        rect_color,
        text_coords,
        text,
        object_tag,
        push_design_to_stack,
        signal_design_change,
    ):
        """Stores the new block in canvas dictionary."""
        self.active_data.store_block_in_canvas_dictionary(
            canvas_id,
            reference,
            rect_coords,
            rect_color,
            text_coords,
            text,
            object_tag,
            push_design_to_stack,
            signal_design_change,
        )

    def store_block_rectangle_in_canvas_dictionary(self, canvas_id, reference, push_design_to_stack):
        """Stores the new block rectangle in canvas dictionary."""
        self.active_data.store_block_rectangle_in_canvas_dictionary(canvas_id, reference, push_design_to_stack)

    def store_instance_in_canvas_dictionary(
        self, canvas_id, reference, symbol_definition, push_design_to_stack, signal_design_change
    ):
        """Stores the new instance in canvas dictionary."""
        self.active_data.store_instance_in_canvas_dictionary(
            canvas_id, reference, symbol_definition, push_design_to_stack, signal_design_change
        )

    def store_generate_frame_in_canvas_dictionary(
        self, canvas_id, reference, generate_definition, push_design_to_stack, signal_design_change
    ):
        """Stores the new generate frame in canvas dictionary."""
        self.active_data.store_generate_frame_in_canvas_dictionary(
            canvas_id, reference, generate_definition, push_design_to_stack, signal_design_change
        )

    def store_regex_for_log_tab(self, regex_message_find):
        """Stores the new regex for log tab."""
        self.active_data.store_regex_for_log_tab(regex_message_find)

    def store_regex_file_name_quote(self, regex_file_name_quote):
        """Stores the new regex for file name quote."""
        self.active_data.store_regex_file_name_quote(regex_file_name_quote)

    def store_regex_file_line_number_quote(self, regex_file_line_number_quote):
        """Stores the new regex for file line number quote."""
        self.active_data.store_regex_file_line_number_quote(regex_file_line_number_quote)

    def store_sash_position(self, sash_position):
        """Stores the new sash position."""
        self.active_data.store_sash_position(sash_position)

    def remove_canvas_item_from_dictionary(self, canvas_id, push_design_to_stack):
        """Removes a canvas item from the dictionary."""
        self.active_data.remove_canvas_item_from_dictionary(canvas_id, push_design_to_stack)

    def update_window_title(self, written):
        """Updates the window title."""
        self.active_data.update_window_title(written)

    def create_schematic_elements_dictionary(self):
        """Creates a dictionary of schematic elements."""
        return self.active_data.create_schematic_elements_dictionary()

    def get_edit_cmd(self):
        """Returns the edit command."""
        return self.active_data.get_edit_cmd()

    def get_hfe_cmd(self):
        """Returns the HFE command."""
        return self.active_data.hfe_cmd

    def get_working_directory(self):
        """Returns the working directory."""
        return self.active_data.get_working_directory()

    def get_include_timestamp_in_hdl(self):
        """Returns whether to include timestamp in HDL."""
        return self.active_data.get_include_timestamp_in_hdl()

    def get_compile_cmd(self):
        """Returns the compile command."""
        return self.active_data.get_compile_cmd()

    def get_compile_hierarchy_cmd(self):
        """Returns the compile hierarchy command."""
        return self.active_data.get_compile_hierarchy_cmd()

    def get_generate_path_value(self):
        """Returns the generate path value."""
        return self.active_data.get_generate_path_value()

    def set_language(self, language):
        """Sets the new language in all dictionaries."""
        self.active_data.set_language(language)

    def get_language(self):
        """Returns the current language."""
        return self.active_data.get_language()

    def get_block_edit_is_running(self):
        """Returns whether a block edit is running."""
        return self.active_data.get_block_edit_is_running()

    def set_block_edit_is_running(self, value):
        """Sets whether a block edit is running."""
        self.active_data.set_block_edit_is_running(value)

    def get_wire_id(self):
        """Returns the current wire id."""
        return self.active_data.get_wire_id()

    def inc_wire_id(self):
        """Increments the current wire id."""
        self.active_data.inc_wire_id()

    def get_grid_size(self):
        """Returns the current grid size."""
        return self.active_data.get_grid_size()

    def set_grid_size(self, value):
        """Sets the current grid size."""
        self.active_data.set_grid_size(value)

    def get_font_size(self):
        """Returns the current font size."""
        return self.active_data.get_font_size()

    def set_font_size(self, value):
        """Sets the current font size."""
        self.active_data.set_font_size(value)

    def get_connector_size(self):
        """Returns the current connector size."""
        return self.active_data.get_connector_size()

    def get_regex_message_find(self):
        """Returns the regex message find."""
        return self.active_data.regex_message_find

    def set_connector_size(self, value):
        """Sets the current connector size."""
        self.active_data.set_connector_size(value)

    def get_block_id(self):
        """Returns the current block id."""
        return self.active_data.get_block_id()

    def inc_block_id(self):
        """Increments the current block id."""
        self.active_data.inc_block_id()

    def get_generate_frame_id(self):
        """Returns the current generate frame id."""
        return self.active_data.get_generate_frame_id()

    def get_sorted_list_of_instance_dictionaries(self):
        """Returns a sorted list of instance dictionaries."""
        return self.active_data.get_sorted_list_of_instance_dictionaries()

    def increment_generate_frame_id(self):
        """Increments the current generate frame id."""
        self.active_data.increment_generate_frame_id()

    def get_instance_id(self):
        """Returns the current instance id."""
        return self.active_data.get_instance_id()

    def increment_instance_id(self):
        """Increments the current instance id."""
        self.active_data.increment_instance_id()

    def get_schematic_element_type_of(self, canvas_id):
        """Returns the schematic element type of a canvas item."""
        return self.active_data.get_schematic_element_type_of(canvas_id)

    def get_stored_tags_of(self, canvas_id):
        """Returns the stored tags of a canvas item."""
        return self.active_data.get_stored_tags_of(canvas_id)

    def get_edit_text_edit_list(self):
        """Returns the edit text edit list."""
        return self.active_data.get_edit_text_edit_list()

    def edit_text_edit_list_append(self, reference):
        """Appends a reference to the edit text edit list."""
        self.active_data.edit_text_edit_list_append(reference)

    def edit_text_edit_list_remove(self, reference):
        """Removes a reference from the edit text edit list."""
        self.active_data.edit_text_edit_list_remove(reference)

    def get_block_edit_list(self):
        """Returns the block edit list."""
        return self.active_data.get_block_edit_list()

    def block_edit_list_append(self, reference):
        """Appends a reference to the block edit list."""
        self.active_data.block_edit_list_append(reference)

    def block_edit_list_remove(self, reference):
        """Removes a reference from the block edit list."""
        self.active_data.block_edit_list_remove(reference)

    def get_signal_name_edit_list(self):
        """Returns the signal name edit list."""
        return self.active_data.get_signal_name_edit_list()

    def signal_name_edit_list_append(self, reference):
        """Appends a reference to the signal name edit list."""
        self.active_data.signal_name_edit_list_append(reference)

    def signal_name_edit_list_remove(self, reference):
        """Removes a reference from the signal name edit list."""
        self.active_data.signal_name_edit_list_remove(reference)

    def get_edit_line_edit_list(self):
        """Returns the edit line edit list."""
        return self.active_data.get_edit_line_edit_list()

    def edit_line_edit_list_append(self, reference):
        """Appends a reference to the edit line edit list."""
        self.active_data.edit_line_edit_list_append(reference)

    def edit_line_edit_list_remove(self, reference):
        """Removes a reference from the edit line edit list."""
        self.active_data.edit_line_edit_list_remove(reference)

    def get_canvas_ids_of_elements(self):
        """Returns the canvas IDs of elements."""
        return self.active_data.get_canvas_ids_of_elements()

    def get_symbol_definition_of(self, canvas_id):
        """Returns the symbol definition of a canvas item."""
        return self.active_data.get_symbol_definition_of(canvas_id)

    def get_angle_of_signal_name(self, canvas_id):
        """Returns the angle of a signal name."""
        return self.active_data.get_angle_of_signal_name(canvas_id)

    def get_tag_of_signal_name(self, canvas_id):
        """Returns the tag of a signal name."""
        return self.active_data.get_tag_of_signal_name(canvas_id)

    def get_coords_of_interface(self, canvas_id):
        """Returns the coordinates of an interface."""
        return self.active_data.get_coords_of_interface(canvas_id)

    def get_orientation_of_interface(self, canvas_id):
        """Returns the orientation of an interface."""
        return self.active_data.get_orientation_of_interface(canvas_id)

    def get_stored_tags_of_wire(self, canvas_id):
        """Returns the stored tags of a wire."""
        return self.active_data.get_stored_tags_of_wire(canvas_id)

    def get_coords_of_wire(self, canvas_id):
        """Returns the coordinates of a wire."""
        return self.active_data.get_coords_of_wire(canvas_id)

    def get_arrow_of_wire(self, canvas_id):
        """Returns the arrow of a wire."""
        return self.active_data.get_arrow_of_wire(canvas_id)

    def get_width_of_wire(self, canvas_id):
        """Returns the width of a wire."""
        return self.active_data.get_width_of_wire(canvas_id)

    def get_coords_of_signal_name(self, canvas_id):
        """Returns the coordinates of a signal name."""
        return self.active_data.get_coords_of_signal_name(canvas_id)

    def get_declaration_of_signal_name(self, canvas_id):
        """Returns the declaration of a signal name."""
        return self.active_data.get_declaration_of_signal_name(canvas_id)

    def get_rect_coords_of_block(self, canvas_id):
        """Returns the rectangle coordinates of a block."""
        return self.active_data.get_rect_coords_of_block(canvas_id)

    def get_rect_color_of_block(self, canvas_id):
        """Returns the rectangle color of a block."""
        return self.active_data.get_rect_color_of_block(canvas_id)

    def get_text_coords_of_block(self, canvas_id):
        """Returns the text coordinates of a block."""
        return self.active_data.get_text_coords_of_block(canvas_id)

    def get_text_of_block(self, canvas_id):
        """Returns the text of a block."""
        return self.active_data.get_text_of_block(canvas_id)

    def get_generate_definition_of(self, canvas_id):
        """Returns the generate definition of a block."""
        return self.active_data.get_generate_definition_of(canvas_id)

    def get_module_name(self):
        """Returns the module name."""
        return self.active_data.get_module_name()

    def get_additional_sources(self):
        """Returns the additional sources."""
        return self.active_data.get_additional_sources()

    def get_architecture_name(self):
        """Returns the architecture name."""
        return self.active_data.get_architecture_name()

    def get_visible_center_point(self):
        """Returns the visible center point."""
        return self.active_data.get_visible_center_point()

    def get_symbol_definitions(self):
        """Returns the symbol definitions."""
        return self.active_data.get_symbol_definitions()

    def get_connection_data(self):  # Used by design_data itself and by hdl_generate.
        """Returns the connection data."""
        return self.active_data.get_connection_data()

    def get_all_instance_names(self):
        """Returns all instance names."""
        return self.active_data.get_all_instance_names()

    def get_numbers_of_wires(self):
        """Returns the number of wires."""
        return self.active_data.get_numbers_of_wires()

    def get_list_of_canvas_block_references(self):
        """Returns the list of canvas block references."""
        return self.active_data.get_list_of_canvas_block_references()

    def get_list_of_canvas_wire_references(self):
        """Returns the list of canvas wire references."""
        return self.active_data.get_list_of_canvas_wire_references()

    def get_list_of_canvas_signal_name_references(self):
        """Returns the list of canvas signal name references."""
        return self.active_data.get_list_of_canvas_signal_name_references()

    def get_references(self, canvas_ids=None):
        """Returns the references."""
        return self.active_data.get_references(canvas_ids)

    def get_interface_packages(self):
        """Returns the interface packages."""
        return self.active_data.get_interface_packages()

    def get_internals_packages(self):
        """Returns the internals packages."""
        return self.active_data.get_internals_packages()

    def get_number_of_files(self):
        """Returns the number of files."""
        return self.active_data.get_number_of_files()

    def get_signal_declaration(self, canvas_id_of_signal_name):
        """Returns the signal declaration."""
        return self.active_data.get_signal_declaration(canvas_id_of_signal_name)

    def get_stored_language_of_entity(self, entity_name):
        """Returns the stored language of an entity."""
        return self.active_data.get_stored_language_of_entity(entity_name)

    def add_change_to_stack(self, push_design_to_stack):
        """Adds a change to the stack."""
        self.active_data.add_change_to_stack(push_design_to_stack)

    def add_change_to_stack_after_zoom(self):
        """Adds a change to the stack after zoom."""
        self.active_data.add_change_to_stack_after_zoom()

    def clear_stack(self):
        """Clears the stack."""
        self.active_data.clear_stack()

    def get_previous_design_dictionary(self):
        """Returns the previous design dictionary."""
        return self.active_data.get_previous_design_dictionary()

    def get_later_design_dictionary(self):
        """Returns the later design dictionary."""
        return self.active_data.get_later_design_dictionary()

    def get_module_library(self):
        """Returns the module library."""
        return self.active_data.get_module_library()

    # def get_change_stack_pointer(self):
    #     return self.active_data.get_change_stack_pointer()
    def insert_copies_from(self, window, canvas_ids, move_copies_under_the_cursor):
        """Inserts copies from the specified canvas IDs."""
        return self.active_data.insert_copies_from(window, canvas_ids, move_copies_under_the_cursor)

    def set_path_name(self, value):
        """Sets the path name."""
        self.active_data.set_path_name(value)

    def get_file_names(self):
        """Returns the file names."""
        return self.active_data.get_file_names()

    def get_file_names_by_parameters(
        self, number_of_files, language, generate_path_value, module_name, architecture_name
    ):
        """Returns the file names by parameters."""
        return self.active_data.get_file_names_by_parameters(
            number_of_files, language, generate_path_value, module_name, architecture_name
        )

    def get_path_name(self):
        """Returns the path name."""
        return self.active_data.get_path_name()

    def get_text_dictionary(self):
        """Returns the text dictionary."""
        return self.active_data.get_text_dictionary()

    def update_hierarchy(self):
        """Updates the hierarchy."""
        self.active_data.update_hierarchy()

    @classmethod
    def get_interface_packages_from_design_dictionary(cls, design_dictionary):  # called by symbol_define
        """Returns the interface packages from the design dictionary."""
        return design_dictionary["text_dictionary"]["interface_packages"]

    @classmethod
    def get_generics_from_design_dictionary(cls, design_dictionary):  # called by symbol_define
        """Returns the generics from the design dictionary."""
        generics = design_dictionary["text_dictionary"]["interface_generics"]
        if design_dictionary["language"] == "VHDL":
            generics = list_separation_check.ListSeparationCheck(generics, "VHDL").get_fixed_list()
        else:
            generics = list_separation_check.ListSeparationCheck(generics, "Verilog").get_fixed_list()
        return generics

    @classmethod
    def get_symbol_definitions_from_design_dictionary(cls, design_dictionary):
        """Returns the symbol definitions from the design dictionary."""
        symbol_definition_list = []
        for _, element_description_list in design_dictionary["canvas_dictionary"].items():
            if element_description_list[1] == "instance":
                symbol_definition_list.append(element_description_list[2])
        return symbol_definition_list
