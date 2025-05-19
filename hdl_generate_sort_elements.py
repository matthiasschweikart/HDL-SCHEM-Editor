"""
This class looks into the schematic and identifies the priorities given in the comment at each schematic element.
Afterwards the schematic elements are sorted based on the priorities found.
Sorting takes hierarchical generate-elements into account.
"""
from tkinter import messagebox

class SortElements():
    def __init__(self, notebook, design, write_to_file):
        self.design = design
        self.sorted_canvas_ids_for_hdl = []
        elements_dictionary = design.create_schematic_elements_dictionary()
        # elements_dictionary = (keys are the Canvas-IDs which are used in design_dictionary)
        # {<Canvas-ID1>: {"prio": <number>, "type": <"Generate"|"Block"|"Instance">, "coords": [n1, n2, n3, n4], "hdl": <code>},
        #  <Canvas-ID2>: {"prio": <number>, "type": <"Generate"|"Block"|"Instance">, "coords": [n1, n2, n3, n4], "hdl": <code>},
        #  ...
        # }
        enclosed_dictionary = self.__create_enclosed_dictionary(elements_dictionary, notebook)
        # The enclosed_dictionary describes which Canvas-IDs are enclosed by generate rectangles.
        # Some Canvas-IDs may be element of several lists, when hierarchical generates are used.
        # Structure of enclosed_dictionary:
        # enclosed_dictionary = [<Canvas-IDx>: [<IDa>, <IDb>, ...],   # The list contains all enclosed IDs, even if they are generates.
        #                        <Canvas-IDy>: [<IDc>, <IDd>, ...],
        #                        ...
        #                       ]
        canvas_ids_of_top_elements = self.__create_list_of_not_enclosed_canvas_ids(elements_dictionary, enclosed_dictionary, write_to_file)
        self.__remove_ambiguity_from_enclosed_dictionary(canvas_ids_of_top_elements, elements_dictionary, enclosed_dictionary)
        self.__sort_enclosed_dictionary(enclosed_dictionary, elements_dictionary, write_to_file)
        self.__expand_generates(canvas_ids_of_top_elements, enclosed_dictionary)

    def get_sorted_list_of_schematic_elements(self):
        return self.sorted_canvas_ids_for_hdl

    def __create_enclosed_dictionary(self, elements_dictionary, notebook):
        enclosed_dictionary = {}
        for schematic_element_canvas_id in elements_dictionary:
            if elements_dictionary[schematic_element_canvas_id]["type"]=="generate_frame":
                enclosed_elements = notebook.diagram_tab.get_enclosed_elements(elements_dictionary[schematic_element_canvas_id]["coords"])
                enclosed_dictionary[schematic_element_canvas_id] = enclosed_elements
        return enclosed_dictionary

    def __create_list_of_not_enclosed_canvas_ids(self, elements_dictionary, enclosed_dictionary, write_to_file):
        canvas_ids_of_top_elements = list(elements_dictionary)
        #print("canvas_ids_of_top_elements1 =", canvas_ids_of_top_elements)
        # Remove all IDs whose symbol is enclosed in a generate-frame:
        for _, enclosed_elements in enclosed_dictionary.items():
            for enclosed_element in enclosed_elements:
                if enclosed_element in canvas_ids_of_top_elements:
                    canvas_ids_of_top_elements.remove(enclosed_element)
        canvas_ids_of_top_elements = self.__sort_canvas_ids(canvas_ids_of_top_elements, elements_dictionary, write_to_file)
        return canvas_ids_of_top_elements

    def __remove_ambiguity_from_enclosed_dictionary(self, canvas_ids, elements_dictionary, enclosed_dictionary):
        for canvas_id_of_this_generate in canvas_ids:
            if elements_dictionary[canvas_id_of_this_generate]["type"]=="generate_frame":
                self.__fix_enclosed_dictionary(canvas_id_of_this_generate, enclosed_dictionary)
                canvas_ids_of_next_generate_level = enclosed_dictionary[canvas_id_of_this_generate]
                self.__remove_ambiguity_from_enclosed_dictionary(canvas_ids_of_next_generate_level, elements_dictionary, enclosed_dictionary)

    def __sort_enclosed_dictionary(self, enclosed_dictionary, elements_dictionary, write_to_file):
        for canvas_id_of_generate, enclosed_canvas_ids in enclosed_dictionary.items():
            enclosed_dictionary[canvas_id_of_generate] = self.__sort_canvas_ids(enclosed_canvas_ids, elements_dictionary, write_to_file)

    def __expand_generates(self, canvas_ids_of_top_elements, enclosed_dictionary):
        for canvas_id_top in canvas_ids_of_top_elements:
            self.sorted_canvas_ids_for_hdl.append(canvas_id_top)
            if canvas_id_top in enclosed_dictionary:
                string_with_enclosed_canvas_ids = ""
                for enclosed_element in enclosed_dictionary[canvas_id_top]:
                    string_with_enclosed_canvas_ids += str(enclosed_element) + ' '
                self.sorted_canvas_ids_for_hdl.append("begin-generate " + string_with_enclosed_canvas_ids)
                self.__expand_generates(enclosed_dictionary[canvas_id_top], enclosed_dictionary)
                self.sorted_canvas_ids_for_hdl.append("end generate " + str(canvas_id_top))

    def __fix_enclosed_dictionary(self, current_generate_canvas_id, enclosed_dictionary):
        enclosed_of_this_generate = enclosed_dictionary[current_generate_canvas_id] # Contains all elements through all included generates.
        for generate_canvas_id, enclosed_elements_of_other_generate in enclosed_dictionary.items():
            if generate_canvas_id!=current_generate_canvas_id: # Look only into all other generates.
                for enclosed_element in enclosed_elements_of_other_generate:
                    if enclosed_element in enclosed_of_this_generate:
                        enclosed_of_this_generate.remove(enclosed_element)  # Remove all the enclosed elements which are enclosed by other generates.
        enclosed_dictionary[current_generate_canvas_id] = enclosed_of_this_generate

    def __sort_canvas_ids(self, list_of_canvas_ids, elements_dictionary, write_to_file):
        canvas_id_dict_with_prio    = {}
        canvas_id_list_without_prio = []
        prio_check_list = []
        prio_check_failed = False
        for canvas_id in list_of_canvas_ids:
            if elements_dictionary[canvas_id]["prio"]!=-1:
                if elements_dictionary[canvas_id]["prio"] not in prio_check_list:
                    prio_check_list.append(elements_dictionary[canvas_id]["prio"])
                else:
                    prio_check_failed = True
                    if write_to_file:
                        messagebox.showerror("Error in HDL-SCHEM-Editor", "There are 2 elements in the schematic " +
                                             self.design.get_module_name() +
                                             " which have the same priority comment with value " +
                                             str(elements_dictionary[canvas_id]["prio"]) +  ", therefore the elements will not be sorted in the HDL.")
        for canvas_id in list_of_canvas_ids:
            if not prio_check_failed and elements_dictionary[canvas_id]["prio"]!=-1:
                canvas_id_dict_with_prio[elements_dictionary[canvas_id]["prio"]] = canvas_id
            else:
                canvas_id_list_without_prio.append(canvas_id)
        canvas_id_dict_with_prio_sorted = dict(sorted(canvas_id_dict_with_prio.items()))
        sorted_list = [canvas_id_dict_with_prio_sorted[prio] for prio in canvas_id_dict_with_prio_sorted]
        sorted_list.extend(canvas_id_list_without_prio)
        return sorted_list
