"""
This class implements a highlight object.
This object carries all information of all highlighted canvas lines in the complete schematic.
"""

import re
from tkinter import messagebox

from codegen import hdl_generate, hdl_generate_functions
from gui import schematic_window


class WireHighlight:
    """The WireHighlight object carries all information of all highlighted canvas lines in the complete schematic."""

    highlight_object = None

    def __init__(self, root):
        WireHighlight.highlight_object = self
        self.root = root
        self.highlight_id = (
            0  # Needed to identify a hierarchical net with different signal-names at the different hierarchy levels.
        )
        self.color_list = ["blue", "magenta", "green", "orange", "yellow", "pink", "skyblue"]
        self.color_number = 0
        self.highlight_dict = {}
        # Structure of self.highlight_dict:
        # {<file-name1>: {<signal_name1> : {"canvas_ids": [canvas_id1, canvas_id2, ...], "color": <color>,
        #                                   "width": <width>, "highlight_id": <number>}},
        #                 <signal_name2> : {"canvas_ids": [canvas_id4, canvas_id5, ...], "color": <color>,
        #                                   "width": <width>, "highlight_id": <number>}},
        #                 ...},
        #  <file-name2>: {<signal_name3> : {"canvas_ids": [canvas_id7, canvas_id8, ...], "color": <color>,
        #                                   "width": <width>, "highlight_id": <number>}},
        #                 <signal_name4> : {"canvas_ids": [canvas_id9, canvas_id10,...], "color": <color>,
        #                                   "width": <width>, "highlight_id": <number>}},
        #                 ...}
        # }

    def add_to_highlight(self, window, canvas_id, depth):
        """Highlight the net which belongs to the canvas_id in the complete schematic."""
        hse_filename = window.design.get_path_name()
        if hse_filename == "":
            messagebox.showerror("Warning in HDL-SCHEM-Editor", "Design must be safed before highlighting is possible.")
            return
        if hse_filename not in self.highlight_dict:
            self.highlight_dict[hse_filename] = {}
        for signal_name in self.highlight_dict[hse_filename]:
            if canvas_id in self.highlight_dict[hse_filename][signal_name]["canvas_ids"]:
                return  # because already highlighted
        self._start_filling_highlight_dict(window, canvas_id, depth)
        self._highlight_in_all_open_windows()
        self.highlight_id += 1

    def _start_filling_highlight_dict(self, window, canvas_id, depth):
        signal_name = self._get_signal_name(window, canvas_id)
        self.color_number = (self.color_number + 1) % len(self.color_list)
        old_wire_width = window.notebook_top.diagram_tab.canvas.itemcget(canvas_id, "width")
        self._fill_highlight_dict_for_this_window(
            window, signal_name, old_wire_width, self.color_list[self.color_number], depth
        )

    def _highlight_in_all_open_windows(self):
        for open_window, filename in schematic_window.SchematicWindow.open_window_dict.items():
            if filename in self.highlight_dict:
                self._highlight_canvas_lines(open_window, self.highlight_dict[filename])

    def _fill_highlight_dict_for_this_window(self, window, signal_name, old_wire_width, color, depth):
        list_of_canvas_ids_to_highlight = self._get_list_of_canvas_ids_to_highlight(window, signal_name)
        self._create_entry_in_highlight_dict(
            window, signal_name, list_of_canvas_ids_to_highlight, color, old_wire_width
        )
        if depth == "hierarchical":
            instance_connection_definitions = self._get_connection_info_for_all_instances(window)
            for instance_connection_definition in instance_connection_definitions:
                if self._signal_is_connected_to_instance(window, instance_connection_definition, signal_name):
                    filename = self._get_filename_of_instance(window, instance_connection_definition)
                    if filename.endswith(".hse"):
                        sub_window = self._load_design(filename)
                        if sub_window.design.get_module_name() != "":  # File Read was a success.
                            if window.design.get_language() == "VHDL":
                                port_name = re.sub(r"\s*:.*", "", instance_connection_definition["port_declaration"])
                            else:
                                port_name = instance_connection_definition["port_declaration"].split()[-1]
                            self._fill_highlight_dict_for_this_window(
                                sub_window, port_name, old_wire_width, color, depth
                            )

    def _get_signal_name(self, window, canvas_id):
        wire_reference = window.design.get_references([canvas_id])[0]
        canvas_id_of_signal_name = window.notebook_top.diagram_tab.canvas.find_withtag(
            wire_reference.wire_tag + "_signal_name"
        )[0]
        signal_declaration = window.design.get_signal_declaration(canvas_id_of_signal_name)
        signal_name, _, _, _, _, _ = hdl_generate_functions.HdlGenerateFunctions.split_declaration(
            signal_declaration, window.design.get_language()
        )
        return signal_name

    def _get_list_of_canvas_ids_to_highlight(self, window, signal_name):
        signal_name_references = window.design.get_list_of_canvas_signal_name_references()
        list_of_canvas_ids_to_highlight = []
        for signal_name_reference in signal_name_references:
            other_signal_name, _, _, _, _, _ = hdl_generate_functions.HdlGenerateFunctions.split_declaration(
                signal_name_reference.declaration, window.design.get_language()
            )
            if other_signal_name == signal_name:
                canvas_ids_of_wire_and_name = window.notebook_top.diagram_tab.canvas.find_withtag(
                    signal_name_reference.wire_tag
                )
                for canvas_id in canvas_ids_of_wire_and_name:
                    if window.notebook_top.diagram_tab.canvas.type(
                        canvas_id
                    ) == "line" and "grid_line" not in window.notebook_top.diagram_tab.canvas.gettags(canvas_id):
                        list_of_canvas_ids_to_highlight.append(canvas_id)
        return list_of_canvas_ids_to_highlight

    def _create_entry_in_highlight_dict(
        self, window, signal_name, list_of_canvas_ids_to_highlight, color, old_wire_width
    ):
        hse_filename = window.design.get_path_name()
        if hse_filename not in self.highlight_dict:
            self.highlight_dict[hse_filename] = {}
        self.highlight_dict[hse_filename][signal_name] = {}
        self.highlight_dict[hse_filename][signal_name]["canvas_ids"] = list_of_canvas_ids_to_highlight
        self.highlight_dict[hse_filename][signal_name]["color"] = color
        self.highlight_dict[hse_filename][signal_name]["width"] = old_wire_width
        self.highlight_dict[hse_filename][signal_name]["highlight_id"] = self.highlight_id

    def _get_connection_info_for_all_instances(self, window):
        (
            _,  # List of dictionaries {"type" : "input"|"output"|"inout", "coords" : [x1, y1, ...]}
            wire_location_list,  # List of dictionaries {"declaration" : <string>, "coords" : [x1, y1, ...]}
            _,  # Dictionary of {<Canvas-ID>: "HDL", <Canvas-ID>: "HDL", ...]
            symbol_definition_list,  # List: [symbol_definition1, symbol_definition2, ...]
            _,  # List: [generate_definition1, generate_definition2, ...]
        ) = window.design.get_connection_data()
        all_pins_definition_list, _, _, _, _ = hdl_generate_functions.HdlGenerateFunctions.extract_data_from_symbols(
            symbol_definition_list
        )
        _, _, _, _, instance_connection_definitions = hdl_generate.GenerateHDL.create_declarations(
            window.design.get_language(), window.design.get_grid_size(), all_pins_definition_list, wire_location_list
        )
        return instance_connection_definitions

    def _signal_is_connected_to_instance(self, window, instance_connection_definition, signal_name):
        connected_signal, _, _, _, _, _ = hdl_generate_functions.HdlGenerateFunctions.split_declaration(
            instance_connection_definition["declaration"], window.design.get_language()
        )
        return signal_name == connected_signal

    def _get_filename_of_instance(self, window, instance_connection_definition):
        reference_to_instance = window.design.get_references([instance_connection_definition["canvas_id"]])[0]
        return reference_to_instance.get_filename()

    def _load_design(self, filename):
        sub_window = None
        for open_window in schematic_window.SchematicWindow.open_window_dict:
            if open_window.design.get_path_name() == filename:
                sub_window = open_window
        return sub_window

    def unhighlight_all_and_delete_object(self):
        """Unhighlight all highlighted nets in the complete schematic and delete the highlight object."""
        WireHighlight.highlight_object = None
        for open_window, filename in schematic_window.SchematicWindow.open_window_dict.items():
            if filename in self.highlight_dict:
                for signal_name in self.highlight_dict[filename]:
                    self._unhighlight_wire_in_open_schematic(open_window, filename, signal_name)
        del self

    def _unhighlight_wire_in_open_schematic(self, open_window, filename, signal_name):
        """Unhighlight a specific wire in an open schematic."""
        for canvas_id in self.highlight_dict[filename][signal_name]["canvas_ids"]:
            if canvas_id in open_window.notebook_top.diagram_tab.canvas.find_all():
                open_window.notebook_top.diagram_tab.canvas.itemconfigure(
                    canvas_id, fill="black", width=self.highlight_dict[filename][signal_name]["width"]
                )

    def unhighlight_net(self, window, canvas_id):
        """Unhighlight the net which belongs to the canvas_id in the complete schematic."""
        hse_filename = window.design.get_path_name()
        signal_name = self._get_signal_name(window, canvas_id)
        highlight_id_to_remove = self._get_highlight_id_to_remove(hse_filename, signal_name)
        if highlight_id_to_remove is not None:
            self._unhighlight_id(highlight_id_to_remove)

    def _get_highlight_id_to_remove(self, hse_filename, signal_name):
        for filename, signal_dict in self.highlight_dict.items():
            if filename == hse_filename:
                for signal_name_entry in signal_dict:
                    if signal_name_entry == signal_name:
                        return signal_dict[signal_name]["highlight_id"]
        return None

    def _unhighlight_id(self, highlight_id_to_remove):
        filename_entries_to_delete = []
        for filename, signal_dict in self.highlight_dict.items():
            local_signal_name_to_remove = self._check_for_highlight_id_in_file(highlight_id_to_remove, signal_dict)
            if local_signal_name_to_remove is not None:
                self._unhighlight_wire_in_schematic(filename, local_signal_name_to_remove)
                del self.highlight_dict[filename][local_signal_name_to_remove]
                if not self.highlight_dict[filename]:
                    filename_entries_to_delete.append(filename)
        for filename_entry_to_delete in filename_entries_to_delete:
            del self.highlight_dict[filename_entry_to_delete]
        if not self.highlight_dict:
            WireHighlight.highlight_object = None
            del self

    def _check_for_highlight_id_in_file(self, highlight_id_to_remove, signal_dict):
        for local_signal_name in signal_dict:
            if signal_dict[local_signal_name]["highlight_id"] == highlight_id_to_remove:
                return local_signal_name
        return None

    def _unhighlight_wire_in_schematic(self, filename, local_signal_name_to_remove):
        for open_window, open_filename in schematic_window.SchematicWindow.open_window_dict.items():
            if open_filename == filename:
                self._unhighlight_wire_in_open_schematic(open_window, filename, local_signal_name_to_remove)

    def highlight_at_window_opening(self, window):
        """Highlight the nets in the window which are highlighted in the complete schematic."""
        for filename, signal_dict in self.highlight_dict.items():
            if filename == window.design.get_path_name():
                self._highlight_canvas_lines(window, signal_dict)

    def _highlight_canvas_lines(self, window, signal_dict):
        for signal_name in signal_dict:
            for canvas_id in signal_dict[signal_name]["canvas_ids"]:
                window.notebook_top.diagram_tab.canvas.itemconfigure(
                    canvas_id, fill=signal_dict[signal_name]["color"], width=3
                )
