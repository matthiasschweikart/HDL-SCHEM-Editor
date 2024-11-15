""" Stores all data of one schematic window """
import copy
import json
import os
import hdl_generate
import interface_inout
import interface_input
import interface_output
import wire_insertion
import signal_name
import block_insertion
import symbol_instance
import generate_frame
import notebook_diagram_tab
import constants

class DesignData():
    def __init__(self, root, schematic_window):
        self.root                     = root
        self.window                   = schematic_window
        self.path_name                = ""
        self.module_name              = ""
        self.architecture_name        = "struct"
        self.language                 = "VHDL"
        self.generate_path_value      = ""
        self.number_of_files          = 2
        self.compile_cmd              = ""
        self.compile_hierarchy_cmd    = ""
        self.edit_cmd                 = ""
        self.hfe_cmd                  = ""
        self.module_library           = ""
        self.additional_sources       = ""
        self.working_directory        = ""
        self.signal_name_font         ="Courier"
        self.regex_message_find       = ""
        self.regex_file_name_quote    = ""
        self.regex_file_line_number_quote = ""
        self.font_size                = 10
        self.grid_size                = 2 * self.font_size
        self.connector_size           = 3 * self.font_size
        self.visible_center_point     = (0, 0)
        self.wire_id                  = 0
        self.block_id                 = 0
        self.generate_frame_id        = 0
        self.instance_id              = 0
        self.text_dictionary          = {"interface_packages"             : "",
                                         "interface_generics"             : "",
                                         "internals_packages"             : "",
                                         "architecture_first_declarations": "",
                                         "architecture_last_declarations" : ""}
        self.canvas_dictionary        = {}
        self.change_stack             = []
        self.change_stack.append(self.create_design_dictionary()) # Put an empty design at the stack.
        self.change_stack_pointer     = -1
        self.last_stack_entry_was_caused_by_zoom = False
        self.block_edit_is_running    = False
        # These lists are used to close running edits, when a new file is read:
        self.block_edit_list          = []
        self.signal_name_edit_list    = []
        self.edit_line_edit_list      = []
        self.edit_text_edit_list      = []
        self.debug_stack              = False
        self.sorted_list_of_instance_dictionaries = []
    def store_new_module_name(self, var_name, signal_design_change):
        self.module_name = var_name.get()
        if signal_design_change:
            self.update_window_title(written=False)
    def store_new_architecture_name(self, architecture_name, signal_design_change):
        self.architecture_name = architecture_name
        if signal_design_change:
            self.update_window_title(written=False)
    def store_generate_path_value(self, var_name, signal_design_change):
        self.generate_path_value = var_name.get()
        if signal_design_change:
            self.update_window_title(written=False)
    def store_new_language(self, var_name, signal_design_change):
        self.language = var_name.get()
        if signal_design_change:
            self.update_window_title(written=False)
    def store_number_of_files(self, var_name, signal_design_change):
        self.number_of_files = var_name.get()
        if signal_design_change:
            self.update_window_title(written=False)
    def store_new_edit_command(self, var_name, signal_design_change):
        self.edit_cmd = var_name.get()
        if signal_design_change:
            self.update_window_title(written=False)
    def store_new_hfe_command(self, var_name, signal_design_change):
        self.hfe_cmd = var_name.get()
        if signal_design_change:
            self.update_window_title(written=False)
    def store_module_library(self, var_name, signal_design_change):
        self.module_library = var_name.get()
        self.update_hierarchy()
        if signal_design_change:
            self.update_window_title(written=False)
    def store_additional_sources(self, var_name, signal_design_change):
        self.additional_sources = var_name.get()
        if signal_design_change:
            self.update_window_title(written=False)
    def store_working_directory(self, var_name, signal_design_change):
        self.working_directory = var_name.get()
        if signal_design_change:
            self.update_window_title(written=False)
    def store_compile_cmd(self, var_name, signal_design_change):
        self.compile_cmd = var_name.get()
        if signal_design_change:
            self.update_window_title(written=False)
    def store_compile_hierarchy_cmd(self, var_name, signal_design_change):
        self.compile_hierarchy_cmd = var_name.get()
        if signal_design_change:
            self.update_window_title(written=False)
    def store_signal_name_font(self, signal_name_font, signal_design_change):
        self.signal_name_font = signal_name_font
        if signal_design_change:
            self.update_window_title(written=False)
    def store_font_size(self, font_size, signal_design_change):
        self.font_size = font_size
        if signal_design_change:
            self.update_window_title(written=False)
    def store_grid_size(self, grid_size, signal_design_change):
        self.grid_size = grid_size
        if signal_design_change:
            self.update_window_title(written=False)
    def store_connector_size(self, connector_size, signal_design_change):
        self.connector_size = connector_size
        if signal_design_change:
            self.update_window_title(written=False)
    def store_visible_center_point(self, visible_center_point, push_design_to_stack, signal_design_change):
        self.visible_center_point = visible_center_point
        self.add_change_to_stack(push_design_to_stack)
        if self.debug_stack:
            print("debug_stack: store_visible_center_point")
    def store_in_text_dictionary(self, text_name, text, signal_design_change):
        # text_name can be: "interface_packages", "interface_generics", "internals_packages", "architecture_first_declarations", "architecture_last_declarations"
        self.text_dictionary[text_name] = text
        if signal_design_change:
            self.update_window_title(written=False)
    def store_interface_in_canvas_dictionary(self, canvas_id, reference, connector_type, location, orientation, push_design_to_stack, signal_design_change):
        self.canvas_dictionary[canvas_id] = [reference, connector_type, location, orientation]
        self.add_change_to_stack(push_design_to_stack)
        if signal_design_change:
            self.update_window_title(written=False)
        if self.debug_stack:
            print("debug_stack: store_interface_in_canvas_dictionary")
    def store_wire_id(self, wire_id):
        self.wire_id = wire_id
    def store_block_id(self, block_id):
        self.block_id = block_id
    def store_generate_frame_id(self, generate_frame_id):
        self.generate_frame_id = generate_frame_id
    def store_instance_id(self, instance_id):
        self.instance_id = instance_id
    def store_wire_in_canvas_dictionary(self, canvas_id, reference, coords, tags, arrow, width, push_design_to_stack, signal_design_change):
        if "selected" in tags:
            # This can happen if a symbol is moved to which a selected wire is connected.
            tags = list(tags)
            tags.remove("selected") # Selection is not stored in canvas_dictionary.
        self.canvas_dictionary[canvas_id] = [reference, "wire", coords, tags, arrow, width]
        self.add_change_to_stack(push_design_to_stack)
        if signal_design_change:
            self.update_window_title(written=False)
        if self.debug_stack:
            print("debug_stack: store_wire_in_canvas_dictionary")
    def store_dot_in_canvas_dictionary(self, canvas_id, reference, coords, push_design_to_stack):
        self.canvas_dictionary[canvas_id] = [reference, "dot", coords]
        self.add_change_to_stack(push_design_to_stack)
        if self.debug_stack:
            print("debug_stack: store_dot_in_canvas_dictionary")
    def store_signal_name_in_canvas_dictionary(self, canvas_id, reference, coords, angle, text, wire_tag, push_design_to_stack, signal_design_change):
        self.canvas_dictionary[canvas_id] = [reference, "signal-name", coords, angle, text, wire_tag]
        self.add_change_to_stack(push_design_to_stack)
        if signal_design_change:
            self.update_window_title(written=False)
        if self.debug_stack:
            print("debug_stack: store_signal_name_in_canvas_dictionary")
    def store_block_in_canvas_dictionary(self, canvas_id, reference, rect_coords, rect_color, text_coords, text, object_tag, push_design_to_stack, signal_design_change):
        self.canvas_dictionary[canvas_id] = [reference, "block", rect_coords, text_coords, text, object_tag, rect_color]
        self.add_change_to_stack(push_design_to_stack)
        if signal_design_change:
            self.update_window_title(written=False)
        if self.debug_stack:
            print("debug_stack: store_block_in_canvas_dictionary")
    def store_block_rectangle_in_canvas_dictionary(self, canvas_id, reference, push_design_to_stack):
        self.canvas_dictionary[canvas_id] = [reference, "block-rectangle"]
        self.add_change_to_stack(push_design_to_stack)
        if self.debug_stack:
            print("debug_stack: store_block_rectangle_in_canvas_dictionary")
    def store_instance_in_canvas_dictionary(self, canvas_id, reference, symbol_definition, push_design_to_stack, signal_design_change):
        symbol_definition_copy = json.loads(json.dumps(symbol_definition))
        self.canvas_dictionary[canvas_id] = [reference, "instance", symbol_definition_copy]
        self.add_change_to_stack(push_design_to_stack)
        if signal_design_change:
            self.update_window_title(written=False)
        if self.debug_stack:
            print("debug_stack: store_instance_in_canvas_dictionary")
    def store_generate_frame_in_canvas_dictionary(self, canvas_id, reference, generate_definition, push_design_to_stack, signal_design_change):
        generate_definition_copy = json.loads(json.dumps(generate_definition))
        self.canvas_dictionary[canvas_id] = [reference, "generate_frame", generate_definition_copy]
        self.add_change_to_stack(push_design_to_stack)
        if signal_design_change:
            self.update_window_title(written=False)
        if self.debug_stack:
            print("debug_stack: store_generate_frame_in_canvas_dictionary")
    def store_regex_for_log_tab(self, regex_message_find):
        self.regex_message_find = regex_message_find
        self.update_window_title(written=False)
    def store_regex_file_name_quote(self, regex_file_name_quote):
        self.regex_file_name_quote = regex_file_name_quote
        self.update_window_title(written=False)
    def store_regex_file_line_number_quote(self, regex_file_line_number_quote):
        self.regex_file_line_number_quote = regex_file_line_number_quote
        self.update_window_title(written=False)
    def remove_canvas_item_from_dictionary(self, canvas_id, push_design_to_stack):
        del self.canvas_dictionary[canvas_id]
        self.add_change_to_stack(push_design_to_stack)
        self.update_window_title(written=False)
        if self.debug_stack:
            print("debug_stack: remove_canvas_item_from_dictionary")
    def update_window_title(self, written):
        name_of_dir, name_of_file = os.path.split(self.path_name)
        if not written:
            self.window.title(name_of_file + ' (' + name_of_dir + ") *")
        else:
            self.window.title(name_of_file + ' (' + name_of_dir + ")")
    def create_design_dictionary(self):
        (connector_location_list,  # List of dictionaries {"type" : "input"|"output"|"inout", "coords" : [x1, y1, ...]}
        wire_location_list,        # List of dictionaries {"declaration" : <string>, "coords" : [x1, y1, ...]}
        _,                         # Dictionary {"Canvas-ID": <Text of block>, "Canvas-ID": <Text of block>, ...}
        _,                         # List: [symbol_definition1, symbol_definition2, ...]
        _                          # List: [generate_definition1, generate_definition2, ...]
        ) = self.get_connection_data()
        input_decl, output_decl, inout_decl, _, _ =  hdl_generate.GenerateHDL.create_declarations(self.language, self.grid_size, connector_location_list, wire_location_list)
        design_dictionary = {}
        design_dictionary["module_name"          ] = self.module_name
        design_dictionary["architecture_name"    ] = self.architecture_name
        design_dictionary["port_declarations"    ] = input_decl + output_decl + inout_decl
        design_dictionary["generate_path_value"  ] = self.generate_path_value
        design_dictionary["language"             ] = self.language
        design_dictionary["number_of_files"      ] = self.number_of_files
        design_dictionary["edit_cmd"             ] = self.edit_cmd
        design_dictionary["hfe_cmd"              ] = self.hfe_cmd
        design_dictionary["module_library"       ] = self.module_library
        design_dictionary["additional_sources"   ] = self.additional_sources
        design_dictionary["working_directory"    ] = self.working_directory
        design_dictionary["compile_cmd"          ] = self.compile_cmd
        design_dictionary["compile_hierarchy_cmd"] = self.compile_hierarchy_cmd
        design_dictionary["signal_name_font"     ] = self.signal_name_font
        design_dictionary["font_size"            ] = self.font_size
        design_dictionary["grid_size"            ] = self.grid_size
        design_dictionary["visible_center_point" ] = self.visible_center_point
        design_dictionary["connector_size"       ] = self.connector_size
        design_dictionary["regex_message_find"   ] = self.regex_message_find
        design_dictionary["regex_file_name_quote"] = self.regex_file_name_quote
        design_dictionary["regex_file_line_number_quote"] = self.regex_file_line_number_quote
        design_dictionary["wire_id"              ] = self.wire_id
        design_dictionary["block_id"             ] = self.block_id
        design_dictionary["generate_frame_id"    ] = self.generate_frame_id
        design_dictionary["instance_id"          ] = self.instance_id
        design_dictionary["text_dictionary"      ] = self.text_dictionary.copy()
        # Create a new object in design_dictionary["canvas_dictionary"], because the reference to the object
        # must be replaced by "empty". Otherwise at Undo/Redo the unused objects would be still "used" and
        # would not be deleted by garbage collection:
        design_dictionary["canvas_dictionary"    ] = {}
        for canvas_id, element_description_list in self.canvas_dictionary.items():
            design_dictionary["canvas_dictionary"][canvas_id] = []
            for index, attribute in enumerate(element_description_list):
                if index==0:
                    design_dictionary["canvas_dictionary"][canvas_id].append("empty") # remove the reference.
                else:
                    design_dictionary["canvas_dictionary"][canvas_id].append(attribute)
        design_dictionary = json.loads(json.dumps(design_dictionary)) # Got necessary, because generate_frame is stored as reference.
        return design_dictionary
    def create_schematic_elements_dictionary(self): # Used by hdl_generate_sort_elements.SortElements
        # [<ID1>: ["prio": <number>, "type": <"generate_frame"|"block"|"instance">, "coords": [n1, n2, n3, n4]],
        #  <ID2>: ["prio": <number>, "type": <"generate_frame"|"Block"|"Instance">, "coords": [n1, n2, n3, n4]],
        hdl_element_dict = {}
        for canvas_id, element_description_list in self.canvas_dictionary.items():
            if element_description_list[1]=="instance":
                new_hdl_element_entry = {}
                new_hdl_element_entry["type"  ] = "instance"
                new_hdl_element_entry["prio"  ] = symbol_instance.Symbol.get_priority_from_symbol_definition(element_description_list[2])
                new_hdl_element_entry["coords"] = []
                hdl_element_dict[canvas_id] = new_hdl_element_entry
            elif element_description_list[1]=="block":
                new_hdl_element_entry = {}
                new_hdl_element_entry["type"  ] = "block"
                new_hdl_element_entry["prio"  ] = block_insertion.Block.get_priority_from_text(element_description_list[4])
                new_hdl_element_entry["coords"] = []
                hdl_element_dict[canvas_id] = new_hdl_element_entry
            elif element_description_list[1]=="generate_frame":
                new_hdl_element_entry = {}
                new_hdl_element_entry["type"  ] = "generate_frame"
                new_hdl_element_entry["prio"  ] = generate_frame.GenerateFrame.get_priority_from_generate_definition        (element_description_list[2])
                new_hdl_element_entry["coords"] = generate_frame.GenerateFrame.get_rectangle_coords_from_generate_definition(element_description_list[2])
                hdl_element_dict[canvas_id] = new_hdl_element_entry
        return hdl_element_dict
    def get_edit_cmd(self):
        return self.edit_cmd
    def get_hfe_cmd(self):
        return self.hfe_cmd
    def get_working_directory(self):
        return self.working_directory
    def get_compile_cmd(self):
        return self.compile_cmd
    def get_compile_hierarchy_cmd(self):
        return self.compile_hierarchy_cmd
    def get_generate_path_value(self):
        return self.generate_path_value
    def set_language(self, language):
        self.language = language
    def get_language(self):
        return self.language
    def get_block_edit_is_running(self):
        return self.block_edit_is_running
    def set_block_edit_is_running(self, value):
        self.block_edit_is_running = value
    def get_wire_id(self):
        return self.wire_id
    def inc_wire_id(self):
        self.wire_id += 1
    def get_grid_size(self):
        return self.grid_size
    def set_grid_size(self, value):
        self.grid_size = value
    def get_font_size(self):
        return self.font_size
    def set_font_size(self, value):
        self.font_size = value
    def get_connector_size(self):
        return self.connector_size
    def get_regex_message_find(self):
        return self.regex_message_find
    def set_connector_size(self, value):
        self.connector_size = value
    def get_block_id(self):
        return self.block_id
    def inc_block_id(self):
        self.block_id += 1
    def get_generate_frame_id(self):
        return self.generate_frame_id
    def get_sorted_list_of_instance_dictionaries(self):
        return self.sorted_list_of_instance_dictionaries
    def increment_generate_frame_id(self):
        self.generate_frame_id += 1
    def get_instance_id(self):
        return self.instance_id
    def increment_instance_id(self):
        self.instance_id += 1
    def get_schematic_element_type_of(self,canvas_id):
        return self.canvas_dictionary[canvas_id][1]
    def get_stored_tags_of(self, canvas_id):
        return self.canvas_dictionary[canvas_id][3]
    def get_edit_text_edit_list(self):
        return self.edit_text_edit_list
    def edit_text_edit_list_append(self, reference):
        self.edit_text_edit_list.append(reference)
    def edit_text_edit_list_remove(self, reference):
        self.edit_text_edit_list.remove(reference)
    def get_block_edit_list(self):
        return self.block_edit_list
    def block_edit_list_append(self, reference):
        self.block_edit_list.append(reference)
    def block_edit_list_remove(self, reference):
        self.block_edit_list.remove(reference)
    def get_signal_name_edit_list(self):
        return self.signal_name_edit_list
    def signal_name_edit_list_append(self, reference):
        self.signal_name_edit_list.append(reference)
    def signal_name_edit_list_remove(self, reference):
        if reference in self.signal_name_edit_list:
            self.signal_name_edit_list.remove(reference)
    def get_edit_line_edit_list(self):
        return self.edit_line_edit_list
    def get_module_library(self):
        return self.module_library
    def get_additional_sources(self):
        return self.additional_sources
    def edit_line_edit_list_append(self, reference):
        self.edit_line_edit_list.append(reference)
    def edit_line_edit_list_remove(self, reference):
        self.edit_line_edit_list.remove(reference)
    def get_canvas_ids_of_elements(self):
        return self.canvas_dictionary.keys()
    def get_symbol_definition_of(self, canvas_id):
        return self.canvas_dictionary[canvas_id][2]
    def get_angle_of_signal_name(self, canvas_id):
        return self.canvas_dictionary[canvas_id][3]
    def get_tag_of_signal_name(self, canvas_id):
        return self.canvas_dictionary[canvas_id][5]
    def get_coords_of_interface(self, canvas_id):
        return self.canvas_dictionary[canvas_id][2]
    def get_orientation_of_interface(self, canvas_id):
        return self.canvas_dictionary[canvas_id][3]
    def get_stored_tags_of_wire(self, canvas_id):
        return self.canvas_dictionary[canvas_id][3]
    def get_coords_of_wire(self, canvas_id):
        return self.canvas_dictionary[canvas_id][2]
    def get_arrow_of_wire(self, canvas_id):
        return self.canvas_dictionary[canvas_id][4]
    def get_width_of_wire(self, canvas_id):
        return self.canvas_dictionary[canvas_id][5]
    def get_coords_of_signal_name(self, canvas_id):
        return self.canvas_dictionary[canvas_id][2]
    def get_declaration_of_signal_name(self, canvas_id):
        if canvas_id in self.canvas_dictionary:
            return self.canvas_dictionary[canvas_id][4]
        return None
    def get_rect_coords_of_block(self, canvas_id):
        return self.canvas_dictionary[canvas_id][2]
    def get_rect_color_of_block(self, canvas_id):
        if len(self.canvas_dictionary[canvas_id])==7:
            return self.canvas_dictionary[canvas_id][6]
        return constants.BLOCK_DEFAULT_COLOR
    def get_text_coords_of_block(self, canvas_id):
        return self.canvas_dictionary[canvas_id][3]
    def get_text_of_block(self, canvas_id):
        return self.canvas_dictionary[canvas_id][4]
    def get_generate_definition_of(self, canvas_id):
        return self.canvas_dictionary[canvas_id][2]
    def get_module_name(self):
        return self.module_name
    def get_architecture_name(self):
        return self.architecture_name
    def get_visible_center_point(self):
        return int(self.visible_center_point[0]), int(self.visible_center_point[1])
    def get_path_name(self):
        return self.path_name
    def get_text_dictionary(self):
        return self.text_dictionary
    def set_path_name(self, value):
        self.path_name = value
    def get_file_names(self):
        return self.get_file_names_by_parameters(self.number_of_files, self.language, self.generate_path_value, self.module_name, self.architecture_name)
    def get_file_names_by_parameters(self, number_of_files, language, generate_path_value, module_name, architecture_name):
        if number_of_files==1:
            if language=="VHDL":
                file_type = ".vhd"
            elif language=="Verilog":
                file_type = ".v"
            else:
                file_type = ".sv"
            file_name = generate_path_value + "/" + module_name + file_type
            file_name_architecture = ""
        else:
            file_name = generate_path_value + "/" + module_name + "_e.vhd"
            file_name_architecture = generate_path_value + "/" + module_name + "_" + architecture_name + ".vhd"
        return file_name, file_name_architecture
    def get_symbol_definitions(self):
        symbol_definition_list = []
        for _, element_description_list in self.canvas_dictionary.items():
            if element_description_list[1]=="instance":
                symbol_definition_list.append(element_description_list[2])
        return symbol_definition_list
    def get_connection_data(self): # Used by design_data itself and by hdl_generate.
        port_list                     = []
        wire_list                     = []
        block_list                    = {}
        symbol_definition_list        = []
        generate_definition_list      = []
        tag_to_declaration_dictionary = {}
        for canvas_id, element_description_list in self.canvas_dictionary.items():
            if element_description_list[1] in ["input", "output", "inout"]:
                port_list.append({"type" : element_description_list[1], "coords" : element_description_list[2]})
            elif element_description_list[1]=="wire":
                tag_list = element_description_list[3]
                for tag in tag_list:
                    if tag.startswith("wire_"):
                        wire_tag = tag
                wire_list.append({"declaration" : wire_tag, "coords" : element_description_list[2]})
            elif element_description_list[1]=="signal-name":
                tag_to_declaration_dictionary[element_description_list[5]] = element_description_list[4]
            elif element_description_list[1]=="block":
                block_list[canvas_id] = element_description_list[4]
            elif element_description_list[1]=="instance":
                symbol_definition_list.append(element_description_list[2])   # add symbol_definition
            elif element_description_list[1]=="generate_frame":
                generate_definition_list.append(element_description_list[2]) # add generate_definition (a dictionary)
        for index, entry in enumerate(wire_list):
            wire_tag = entry["declaration"]
            wire_list[index]["declaration"] = tag_to_declaration_dictionary[wire_tag]
        return port_list, wire_list, block_list, symbol_definition_list, generate_definition_list
    def get_all_instance_names(self):
        all_instance_names = []
        for _, element_description_list in self.canvas_dictionary.items():
            if element_description_list[1]=="instance":
                all_instance_names.append(element_description_list[2]["instance_name"]["name"])
        return all_instance_names
    def get_numbers_of_wires(self):
        number_of_wires = 0
        for _, element_description_list in self.canvas_dictionary.items():
            if element_description_list[1]=="wire":
                number_of_wires += 1
        return number_of_wires
    def get_list_of_canvas_block_references(self):
        list_of_canvas_block_references = []
        for _, element_description_list in self.canvas_dictionary.items():
            if element_description_list[1]=="block":
                list_of_canvas_block_references.append(element_description_list[0])
        return list_of_canvas_block_references
    def get_list_of_canvas_wire_references(self):
        list_of_canvas_wires_references = []
        for _, element_description_list in self.canvas_dictionary.items():
            if element_description_list[1]=="wire":
                list_of_canvas_wires_references.append(element_description_list[0])
        return list_of_canvas_wires_references
    def get_list_of_canvas_signal_name_references(self):
        list_of_canvas_signal_name_references = []
        for _, element_description_list in self.canvas_dictionary.items():
            if element_description_list[1]=="signal-name":
                list_of_canvas_signal_name_references.append(element_description_list[0])
        return list_of_canvas_signal_name_references
    # def get_list_of_canvas_wire_ids(self):
    #     list_of_canvas_wires_ids = []
    #     for canvas_id, element_description_list in self.canvas_dictionary.items():
    #         if element_description_list[1]=="wire":
    #             list_of_canvas_wires_ids.append(canvas_id)
    #     return list_of_canvas_wires_ids
    # def get_list_of_canvas_dot_ids(self):
    #     list_of_canvas_dot_ids = []
    #     for canvas_id, element_description_list in self.canvas_dictionary.items():
    #         if element_description_list[1]=="dot":
    #             list_of_canvas_dot_ids.append(canvas_id)
    #     return list_of_canvas_dot_ids
    def get_references(self, canvas_ids=None):
        ref_list = []
        if canvas_ids is None:
            for value in self.canvas_dictionary.values():
                ref_list.append(value[0]) # Return the reference of each canvas ID.
        else:
            for canvas_id in canvas_ids:
                if canvas_id in self.canvas_dictionary: # Instances (and also other objects) do not store all their canvas-IDs in the dictionary.
                    ref_list.append(self.canvas_dictionary[canvas_id][0]) # Return the references to the objects, which are selected by canvas_ids.
        return ref_list
    def get_interface_packages(self):
        return self.text_dictionary["interface_packages"]
    def get_internals_packages(self):
        return self.text_dictionary["internals_packages"]
    def get_number_of_files(self):
        return self.number_of_files
    def get_signal_declaration(self, canvas_id_of_signal_name):
        return self.canvas_dictionary[canvas_id_of_signal_name][4]
    def get_stored_language_of_entity(self, entity_name):
        for _, element_description_list in self.canvas_dictionary.items():
            if element_description_list[1]=="instance":
                symbol_definition = element_description_list[2]
                if symbol_definition["entity_name"]["name"]==entity_name:
                    return symbol_definition["language"]
        return None
    def add_change_to_stack(self, push_design_to_stack):
        #print("add_change_to_stack:", push_design_to_stack, self.window)
        if push_design_to_stack is True:
            self.update_hierarchy()
            # Check for double wire_tags, caused by programming error:
            # for canvas_id in self.canvas_dictionary:
            #     if self.window.notebook_top.diagram_tab.canvas.type(canvas_id)=="line":
            #         ref = self.get_references([canvas_id])[0]
            #         my_wire_tag = ref.wire_tag
            #         for other_canvas_id in self.canvas_dictionary:
            #             if self.window.notebook_top.diagram_tab.canvas.type(other_canvas_id)=="line":
            #                 if other_canvas_id!=canvas_id:
            #                     other_ref = self.get_references([other_canvas_id])[0]
            #                     other_wire_tag = other_ref.wire_tag
            #                     if other_wire_tag==my_wire_tag:
            #                         print("Fatal: A wire_tag exists more than one time = ", my_wire_tag, ' ')
            #                         signal_name_ref = self.get_references(self.window.notebook_top.diagram_tab.canvas.find_withtag(other_wire_tag + "_signal_name"))[0]
            #                         print("Signal-Declaration =", signal_name_ref.declaration)
            self.last_stack_entry_was_caused_by_zoom = False
            self.visible_center_point = [
                (self.window.notebook_top.diagram_tab.canvas.canvasx(0) +
                    self.window.notebook_top.diagram_tab.canvas.canvasx(self.window.notebook_top.diagram_tab.canvas.winfo_width ()))/2,
                (self.window.notebook_top.diagram_tab.canvas.canvasy(0) +
                    self.window.notebook_top.diagram_tab.canvas.canvasy(self.window.notebook_top.diagram_tab.canvas.winfo_height()))/2]
            if self.change_stack_pointer!=len(self.change_stack)-1:
                del self.change_stack[self.change_stack_pointer+1:]
                #print("Stack upper entries cleared: self.change_stack_pointer, len(self.change_stack) =", self.change_stack_pointer, len(self.change_stack))
                self.window.notebook_top.diagram_tab.redo_button.config(state="disabled")
            design = self.create_design_dictionary()
            self.change_stack.append(design)
            self.change_stack_pointer += 1 # Points to the entry which was yet appended.
            #print("stack_pointer (add)=", self.change_stack_pointer, "vcp =", self.visible_center_point)
            if self.change_stack_pointer>0:
                self.window.notebook_top.diagram_tab.undo_button.config(state="enabled")
        else:
            #print("add_change_to_stack called with False")
            pass
    def add_change_to_stack_after_zoom(self):
        if self.last_stack_entry_was_caused_by_zoom:
            #print("add_change_to_stack_after_zoom: Overwrite the last zoom stack entry")
            # Overwrite the last zoom stack entry:
            del self.change_stack[self.change_stack_pointer]
            self.change_stack_pointer -= 1
        if self.change_stack_pointer!=len(self.change_stack)-1:
            del self.change_stack[self.change_stack_pointer+1:]
            #print("add_change_to_stack_after_zoom: Stack upper entries cleared by zoom")
            self.window.notebook_top.diagram_tab.redo_button.config(state="disabled")
        design = self.create_design_dictionary()
        self.change_stack.append(design)
        self.change_stack_pointer += 1 # Points to the entry which was yet appended.
        #print("stack-pointer after zoom =", self.change_stack_pointer)
        if self.change_stack_pointer>0:
            self.window.notebook_top.diagram_tab.undo_button.config(state="enabled")
        self.last_stack_entry_was_caused_by_zoom = True
    def clear_stack(self): # used by file_read
        #print("clear_stack called")
        self.change_stack             = []
        self.change_stack_pointer     = -1
        self.window.notebook_top.diagram_tab.undo_button.config(state="disabled")
        self.window.notebook_top.diagram_tab.redo_button.config(state="disabled")
    def get_previous_design_dictionary(self):
        if self.change_stack_pointer!=0:
            self.change_stack_pointer -= 1
            if self.change_stack_pointer==0:
                self.window.notebook_top.diagram_tab.undo_button.config(state="disabled")
            self.window.notebook_top.diagram_tab.redo_button.config(state="enabled")
            #print("stack_pointer (get previous)=", self.change_stack_pointer)
            return copy.deepcopy(self.change_stack[self.change_stack_pointer])
        return None
    def get_later_design_dictionary(self):
        if self.change_stack_pointer!=len(self.change_stack)-1:
            self.change_stack_pointer += 1
            #print("stack_pointer (get later   )=", self.change_stack_pointer)
            if self.change_stack_pointer==len(self.change_stack)-1:
                self.window.notebook_top.diagram_tab.redo_button.config(state="disabled")
            self.window.notebook_top.diagram_tab.undo_button.config(state="enabled")
            return copy.deepcopy(self.change_stack[self.change_stack_pointer])
        return None
    # def get_change_stack_pointer(self):
    #     return self.change_stack_pointer

    def insert_copies_from(self, window, canvas_ids, move_copies_under_the_cursor):
        dummy = None
        references_of_copies = []
        object_tag_dict = self.__create_dict_for_replacing_old_wire_tags_by_new_wire_tags(canvas_ids, window)
        for canvas_id in canvas_ids:
            if canvas_id in window.design.get_canvas_ids_of_elements():
                if   window.design.get_schematic_element_type_of(canvas_id)=="input":
                    ref = interface_input.Input  (self.window, self.window.notebook_top.diagram_tab, dummy, follow_mouse=False, #push_design_to_stack=False,
                                    location      = window.design.get_coords_of_interface(canvas_id),
                                    orientation   = window.design.get_orientation_of_interface(canvas_id))
                    references_of_copies.append(ref)
                elif window.design.get_schematic_element_type_of(canvas_id)=="output":
                    ref = interface_output.Output(self.window, self.window.notebook_top.diagram_tab, dummy, follow_mouse=False, #push_design_to_stack=False,
                                    location      = window.design.get_coords_of_interface(canvas_id),
                                    orientation   = window.design.get_orientation_of_interface(canvas_id))
                    references_of_copies.append(ref)
                elif window.design.get_schematic_element_type_of(canvas_id)=="inout":
                    ref = interface_inout.Inout  (self.window, self.window.notebook_top.diagram_tab, dummy, follow_mouse=False, #push_design_to_stack=False,
                                    location      = window.design.get_coords_of_interface(canvas_id),
                                    orientation   = window.design.get_orientation_of_interface(canvas_id))
                    references_of_copies.append(ref)
                elif window.design.get_schematic_element_type_of(canvas_id)=="wire":
                    tags = list(window.design.get_stored_tags_of_wire(canvas_id)) # example: ('wire_0', 'current')
                    for index, tag in enumerate(tags):
                        if tag in object_tag_dict:
                            tags[index] = object_tag_dict[tag]
                    ref = wire_insertion.Wire(self.root, self.window, self.window.notebook_top.diagram_tab, #push_design_to_stack=False,
                                    coords        = window.design.get_coords_of_wire(canvas_id),
                                    tags          = tags,
                                    arrow         = window.design.get_arrow_of_wire(canvas_id),
                                    width         = window.design.get_width_of_wire(canvas_id))
                    references_of_copies.append(ref)
                elif window.design.get_schematic_element_type_of(canvas_id)=="signal-name":
                    wire_tag = window.design.get_tag_of_signal_name(canvas_id)
                    if wire_tag in object_tag_dict: # Then not only a signal name was copied, but also the corresponding wire.
                        tag = object_tag_dict[window.design.get_tag_of_signal_name(canvas_id)]
                        ref = signal_name.SignalName(self, self.window.notebook_top.diagram_tab, #push_design_to_stack=False,
                                        coords        = window.design.get_coords_of_signal_name(canvas_id),
                                        angle         = window.design.get_angle_of_signal_name(canvas_id), # canvas_dictionary[canvas_id][3]
                                        declaration   = window.design.get_declaration_of_signal_name(canvas_id),
                                        wire_tag      = tag)
                        references_of_copies.append(ref)
                elif window.design.get_schematic_element_type_of(canvas_id)=="block-rectangle":
                    pass
                    # The block-rectangle is stored in canvas_dictionary for delete_item(), store_item() and select_item(),
                    # but is not an object, for which a copy must be generated.
                elif window.design.get_schematic_element_type_of(canvas_id)=="block":
                    tag = "block_" + str(self.block_id)
                    self.block_id += 1
                    ref = block_insertion.Block(self.window, self.window.notebook_top.diagram_tab, # push_design_to_stack=False,
                                                rect_coords = window.design.get_rect_coords_of_block(canvas_id),
                                                rect_color  = window.design.get_rect_color_of_block (canvas_id),
                                                text_coords = window.design.get_text_coords_of_block(canvas_id),
                                                text        = window.design.get_text_of_block       (canvas_id),
                                                block_tag   = tag)
                    references_of_copies.append(ref)                     # block text
                    references_of_copies.append(ref.rectangle_reference) # block rectangle
                elif window.design.get_schematic_element_type_of(canvas_id)=="instance":
                    symbol_definition_copy = json.loads(json.dumps(window.design.get_symbol_definition_of(canvas_id)))
                    symbol_definition_copy["object_tag"] = "instance_" + str(self.instance_id)
                    symbol_definition_copy["instance_name"]["name"] += str(self.instance_id)
                    self.instance_id += 1 # Must be incremented after being used in an object tag.
                    ref = symbol_instance.Symbol(self.root, self.window, self.window.notebook_top.diagram_tab, #push_design_to_stack=False,
                                                 symbol_definition=symbol_definition_copy)
                    references_of_copies.append(ref)
                elif window.design.get_schematic_element_type_of(canvas_id)=="generate_frame":
                    generate_definition_copy = json.loads(json.dumps(window.design.get_generate_definition_of(canvas_id)))
                    generate_definition_copy["object_tag"] = "generate_frame_" + str(self.generate_frame_id)
                    self.generate_frame_id += 1 # Must be incremented after being used in an object tag.
                    ref = generate_frame.GenerateFrame(self.root, self.window, self.window.notebook_top.diagram_tab, generate_definition_copy)
                    references_of_copies.append(ref)
                elif window.design.get_schematic_element_type_of(canvas_id)=="dot":
                    pass # Dots are inserted by a method of wire_insertion
                else:
                    pass
            else:
                #print("canvas_id not found in design dictionary:", canvas_id, self.canvas.type(canvas_id))
                pass
        factor = self.grid_size/notebook_diagram_tab.NotebookDiagramTab.grid_size_copied_from
        for ref in references_of_copies:
            ref.adapt_coordinates_by_factor(factor)
            ref.add_pasted_tag_to_all_canvas_items()
        if references_of_copies:
            self.__move_copies(move_copies_under_the_cursor)
        self.window.notebook_top.diagram_tab.canvas.dtag("pasted_tag", "pasted_tag")
        return references_of_copies

    def __create_dict_for_replacing_old_wire_tags_by_new_wire_tags(self, canvas_ids, window):
        # When wires are copied, then the old wire_tag must be replaced by a new wire_tag.
        object_tag_dict = {}
        for canvas_id in canvas_ids:
            if canvas_id in window.design.get_canvas_ids_of_elements():
                if window.design.get_schematic_element_type_of(canvas_id)=="wire":
                    old_tags = window.design.get_stored_tags_of(canvas_id) # example: ('wire_0', 'current')
                    for tag in old_tags:
                        if tag.startswith("wire_"):
                            old_tag = tag
                    new_tag = "wire_" + str(self.wire_id)
                    self.wire_id += 1
                    object_tag_dict[old_tag] = new_tag
        return object_tag_dict

    def __move_copies(self, move_copies_under_the_cursor):
        bbox_coords = self.window.notebook_top.diagram_tab.canvas.bbox("pasted_tag")
        bbox_middle_x = (bbox_coords[0] + bbox_coords[2])/2
        bbox_middle_y = (bbox_coords[1] + bbox_coords[3])/2
        if move_copies_under_the_cursor:
            canvas_position_x = self.window.notebook_top.diagram_tab.canvas.canvasx(self.window.notebook_top.diagram_tab.canvas.winfo_pointerx() -
                                                                                            self.window.notebook_top.diagram_tab.canvas.winfo_rootx())
            canvas_position_y = self.window.notebook_top.diagram_tab.canvas.canvasy(self.window.notebook_top.diagram_tab.canvas.winfo_pointery() -
                                                                                            self.window.notebook_top.diagram_tab.canvas.winfo_rooty())
        else: # move copies in the center of the window
            canvas_position_x = (self.window.notebook_top.diagram_tab.canvas.canvasx(0) +
                                 self.window.notebook_top.diagram_tab.canvas.canvasx(self.window.notebook_top.diagram_tab.canvas.winfo_width ()))/2
            canvas_position_y = (self.window.notebook_top.diagram_tab.canvas.canvasy(0) +
                                 self.window.notebook_top.diagram_tab.canvas.canvasy(self.window.notebook_top.diagram_tab.canvas.winfo_height()))/2
        delta_x = canvas_position_x - bbox_middle_x
        delta_y = canvas_position_y - bbox_middle_y
        delta_x = delta_x - delta_x%self.grid_size
        delta_y = delta_y - delta_y%self.grid_size
        self.window.notebook_top.diagram_tab.canvas.move("pasted_tag", delta_x, delta_y)

    def update_hierarchy(self):
        list_of_instance_dictionaries = []
        for _, element_description_list in self.canvas_dictionary.items():
            if element_description_list[1]=="instance":
                symbol_definition = element_description_list[2]
                instance_dict = {
                    "configuration_library": symbol_definition["configuration"]["library"],
                    "instance_name"        : symbol_definition["instance_name"]["name"],
                    "module_name"          : symbol_definition["entity_name"]["name"],
                    "architecture_name"    : symbol_definition["architecture_name"],
                    "number_of_files"      : symbol_definition["number_of_files"],
                    "generate_path_value"  : symbol_definition["generate_path_value"],
                    "language"             : symbol_definition["language"],
                    "additional_files"     : symbol_definition["additional_files"],
                    "env_language"         : self.window.notebook_top.control_tab.language.get(),
                    "filename"             : symbol_definition["filename"],
                    "architecture_filename": symbol_definition["architecture_filename"]
                }
                list_of_instance_dictionaries.append(instance_dict)
        sorted_list_of_instance_dictionaries = sorted(list_of_instance_dictionaries, key=lambda d: d["instance_name"])
        self.sorted_list_of_instance_dictionaries = sorted_list_of_instance_dictionaries
        # Even if self.sorted_list_of_instance_dictionaries was not changed by the line before,
        # the treeviews must be updated, because there might have been changes in the additional HDL-files.
        # So each change in the database (even it only a symbol is moved) updates the hierarchy view:
        self.window.hierarchytree.refresh_treeviews()
        # Old solution which did not check all possible design changes:
        # if (sorted_list_of_instance_dictionaries!=self.sorted_list_of_instance_dictionaries or # A design change happened.
        #     not sorted_list_of_instance_dictionaries):                                  # This is the bottom of the design.
        #     self.sorted_list_of_instance_dictionaries = sorted_list_of_instance_dictionaries
        #     self.window.hierarchytree.refresh_treeviews()
