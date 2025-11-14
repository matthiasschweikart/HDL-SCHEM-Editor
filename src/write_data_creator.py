"""
This class modifies the data at file-write in a way
that the resulting file will only differ from the read file
if the user added/removed/moved any schematic-element or
changed any text/name/contol-information. Any scrolling, zooming
will not create a different file content.
The "include timestamp in generated HDL" must be switched off if
the file shall not change.
"""
#import canvas_editing

class WriteDataCreator:
    def __init__(self, standard_size):
        self.standard_size = standard_size
        self.actual_size = 0.0
        self.list_of_elements_in_graphic = []

    # def zoom_graphic_to_standard_size(self, actual_size):
    #     self.actual_size = actual_size
    #     canvas_editing._canvas_zoom([0,0], self.standard_size/self.actual_size)
    #     return

    # def zoom_graphic_back_to_actual_size(self):
    #     canvas_editing._canvas_zoom([0,0], self.actual_size/self.standard_size)
    #     return

    # def round_and_sort_data(self, design_dictionary, graphical_elements):
    #     design_dictionary = self._round_coordinates(design_dictionary, graphical_elements)
    #     design_dictionary = self._round_parameters(design_dictionary)
    #     design_dictionary = self._sort(design_dictionary)
    #     return design_dictionary

    # def _round_coordinates(self, design_dictionary, graphical_elements):
    #     for graphical_element in graphical_elements:
    #         if graphical_element in design_dictionary:
    #             self.list_of_elements_in_graphic.append(graphical_element)
    #     for graphical_element in self.list_of_elements_in_graphic:
    #         for graphical_element_property_list in design_dictionary[graphical_element]:
    #             coordinates = graphical_element_property_list[0]
    #             for index, coordinate in enumerate(coordinates):
    #                 graphical_element_property_list[0][index] = round(coordinate, 0)
    #     return design_dictionary

    # def _round_parameters(self, design_dictionary):
    #     design_dictionary["label_fontsize"] = round(design_dictionary["label_fontsize"], 0)
    #     design_dictionary["priority_distance"] = round(design_dictionary["priority_distance"], 0)
    #     return design_dictionary

    # def _sort(self, design_dictionary):
    #     # At all sorts the key is the first tag which the graphical element has (identifier tag).
    #     # The sorting will always give the same result if the order of tags is not changed by tkinter.
    #     for graphical_element in self.list_of_elements_in_graphic:
    #         if graphical_element in ("window_condition_action_block", "window_global_actions"):
    #             index_of_key = 3
    #         elif graphical_element.startswith("window_"):
    #             index_of_key = 2
    #         else:
    #             index_of_key = 1
    #         design_dictionary[graphical_element] = sorted(design_dictionary[graphical_element], key=lambda x: x[index_of_key][0] )
    #     return design_dictionary
