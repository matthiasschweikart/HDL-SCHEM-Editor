"""
This class modifies the data at file-write or switching VHDL architectures
in a way that the resulting file will only differ from the read file
if the user added/removed/moved any schematic-element or
changed any text/name/control-information.
Any scrolling, zooming will not create a different file content.
"""

class WriteDataCreator:
    def __init__(self, standard_size) -> None:
        self.standard_size = standard_size

    def zoom_graphic_to_standard_size(self, window, actual_size) -> float:
        zoom_factor = self.standard_size / actual_size
        window.notebook_top.diagram_tab.zoom(zoom_factor, zoom_command="zoom_at_file_write", event=None)
        return zoom_factor

    def zoom_graphic_back_to_actual_size(self, window, zoom_factor) -> None:
        window.notebook_top.diagram_tab.zoom(1/zoom_factor, zoom_command="zoom_at_file_write", event=None)

    def round_numbers(self, design_dictionary) -> dict[str, dict|str]:
        if "active__architecture" in design_dictionary:
            design_dictionary_active = design_dictionary[design_dictionary["active__architecture"]]
        else:
            design_dictionary_active = design_dictionary
        canvas_dictionary = design_dictionary_active["canvas_dictionary"]
        all_coords_lists = self._get_coords_lists_of_all_elements(canvas_dictionary)
        self._round_coordinates_in_design_dictionary(all_coords_lists)
        self._round_parameters_in_design_dictionary(design_dictionary_active)
        return design_dictionary

    def _get_coords_lists_of_all_elements(self, canvas_dictionary) -> list:
        all_coords_lists = []
        for canvas_id in canvas_dictionary:
            element_type = canvas_dictionary[canvas_id][1]
            if element_type!="block-rectangle": # The block-rectangle coordinates are stored in element_type "block".
                self._append_coordinate_lists_of_element(all_coords_lists, canvas_id, element_type, canvas_dictionary)
        return all_coords_lists

    def _round_coordinates_in_design_dictionary(self, all_coords_lists) -> None:
        for coords_list in all_coords_lists:
            for index, coord in enumerate(coords_list):
                coords_list[index] = round(coord, 0)

    def _append_coordinate_lists_of_element(self, all_coords_lists, canvas_id, element_type, canvas_dictionary) -> None:
        if element_type=="instance":
            element_parts = ["entity_name", "instance_name", "rectangle", "generic_block", "port_list"]
            for element_part in element_parts:
                if element_part!="port_list":
                    all_coords_lists.append(canvas_dictionary[canvas_id][2][element_part]["coords"])
                else:
                    for port_dict in canvas_dictionary[canvas_id][2][element_part]:
                        all_coords_lists.append(port_dict["coords"])
        elif element_type=="generate_frame":
            element_parts = ["generate_rectangle_coords", "generate_condition_coords"]
            for element_part in element_parts:
                all_coords_lists.append(canvas_dictionary[canvas_id][2][element_part])
        elif element_type=="block":
            all_coords_lists.append(canvas_dictionary[canvas_id][2])
            all_coords_lists.append(canvas_dictionary[canvas_id][3])
        else: # element_type in ("wire", "signal-name", "input", "output", "inout", "dot")
            all_coords_lists.append(canvas_dictionary[canvas_id][2])

    def _round_parameters_in_design_dictionary(self, design_dictionary_active) -> None:
        design_dictionary_active["grid_size"] = round(design_dictionary_active["grid_size"], 0)
        design_dictionary_active["connector_size"] = round(design_dictionary_active["connector_size"],0)
        design_dictionary_active["visible_center_point"] = [0, 0]
