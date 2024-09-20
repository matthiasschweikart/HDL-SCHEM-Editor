"""
Class for inserting an extern module into the schematic
"""
from tkinter import messagebox
import re
import symbol_instance

class SymbolInsertion():   # used by SymbolDefine
    def __init__(self,
                 root,
                 window,      # : schematic_window.SchematicWindow,
                 diagram_tab, # : notebook_diagram_tab.NotebookDiagramTab,
                 ):
        self.root           = root
        self.window         = window
        self.diagram_tab    = diagram_tab
        self.event_x        = 0
        self.event_y        = 0
        self.symbol_ref     = None
        self.funcid_delete  = None
        self.func_id_motion = None
        self.func_id_button = None
        self.func_id_leave  = None
        self.func_id_escape = None
        self.input_polygon_coords    = [0,0,                                # the first point is the connectionpoint at the grid.
                                        0, -0.25*self.window.design.get_grid_size(),
                                        0.5*self.window.design.get_grid_size(),0,
                                        0, +0.25*self.window.design.get_grid_size()]
        self.output_polygon_coords   = [0.5*self.window.design.get_grid_size(),0, # the first point is the connectionpoint at the grid.
                                        0, +0.25*self.window.design.get_grid_size(),
                                        0,0,
                                        0, -0.25*self.window.design.get_grid_size()]
        self.inout_polygon_coords    = [0.5*self.window.design.get_grid_size(),0,
                                        0.25*self.window.design.get_grid_size(), +0.25*self.window.design.get_grid_size(),
                                        0,0,
                                        0.25*self.window.design.get_grid_size(), -0.25*self.window.design.get_grid_size()]
        self.properties = {} # Will be filled by reading the HDL-file and will be handed over to draw_symbol() at the end.
        self.properties["object_tag"] = "instance_" + str(self.window.design.get_instance_id())
        self.window.design.increment_instance_id()

    def draw_symbol(self): # called by symbol_reading
        self.diagram_tab.remove_canvas_bindings() # Only needed for Button-3, to have a "clean" situation.
        self.window.config(cursor="cross")
        self.func_id_motion = self.diagram_tab.canvas.bind("<Motion>"  , self.__move_to)
        self.func_id_button = self.diagram_tab.canvas.bind("<Button-1>", self.__end_inserting)
        self.func_id_leave  = self.diagram_tab.canvas.bind("<Leave>"   , self.__reject)
        self.func_id_escape = self.window.bind            ("<Escape>"  , self.__reject)
        # When the file-dialog disappears, then the mouse-pointer may be outside the Canvas:
        #   Then the symbol is drawn at the place, where the mouse-pointer enters the Canvas.
        # When the file-dialog disappears, then the mouse-pointer may be inside the Canvas:
        #   Then the symbol is drawn at the place, where the mouse-pointer did select the file.
        self.event_x = self.diagram_tab.canvas.canvasx(self.diagram_tab.canvas.winfo_pointerx() - self.diagram_tab.canvas.winfo_rootx())
        self.event_y = self.diagram_tab.canvas.canvasy(self.diagram_tab.canvas.winfo_pointery() - self.diagram_tab.canvas.winfo_rooty())
        symbol_definition = self.__create_symbol_definition()
        self.symbol_ref = symbol_instance.Symbol(self.root, self.window, self.diagram_tab, #push_design_to_stack=False,
                                                 symbol_definition=symbol_definition)
        self.diagram_tab.sort_layers()

    def get_symbol_definition_for_update(self): # called by symbol_instance.Symbol.__update_symbol()
        return self.__create_symbol_definition()

    def get_polygon_coords_for(self, port_type): # called by symbol_instance.Symbol.__update_symbol()
        if port_type=="input":
            return self.input_polygon_coords
        if port_type=="output":
            return self.output_polygon_coords
        return self.inout_polygon_coords

    def set_language(self, language):
        self.properties["language"] = language

    def set_number_of_files(self, number_of_files):
        self.properties["number_of_files"] = number_of_files

    def add_library_names(self, library_names):
        self.properties["library_names"] = library_names

    def add_package_names(self, package_names):
        self.properties["package_names"] = package_names

    def add_file_name(self, filename):
        self.properties["filename"] = filename

    def add_generate_path_value(self, generate_path_value):
        self.properties["generate_path_value"] = generate_path_value

    def add_entity_name_name(self, entity_name):
        self.properties["entity_name"] = entity_name

    def add_architecture_name(self, architecture_name):
        self.properties["architecture_name"] = architecture_name

    def add_architecture_list(self, architecture_list):
        self.properties["architecture_list"] = architecture_list

    def add_port(self, port_declaration):
        if "port_declarations" not in self.properties:
            self.properties["port_declarations"] = []
        self.properties["port_declarations"].append(port_declaration)

    def add_generic_definition(self, generic_definition):
        self.properties["generic_definition"] = generic_definition

    def add_module_library(self, module_library):
        self.properties["module_library"] = module_library

    def add_additional_sources(self, additional_sources):
        additional_sources_list = additional_sources.split(',')
        additional_sources_list = [entry.strip() for entry in additional_sources_list]
        self.properties["additional_sources"] = additional_sources_list

    def __create_symbol_definition(self):
        symbol_definition ={}
        if "port_declarations" in self.properties:
            input_list, output_list, inout_list = self.__split_port_list(self.properties["port_declarations"])
        else:
            input_list = output_list = inout_list = []
        number_of_ports_at_left_side  = len(input_list)
        number_of_ports_at_right_side = len(output_list) + len(inout_list)
        max_pin_number = max(number_of_ports_at_left_side, number_of_ports_at_right_side)
        if max_pin_number==0:
            max_pin_number += 1
        symbol_definition["language"]            = self.properties["language"]
        if "module_library" in self.properties:
            symbol_definition["configuration"]   = {"library": self.properties["module_library"], "config_statement": "None"}
        else:
            symbol_definition["configuration"]   = {"library": "work", "config_statement": "None"}
        symbol_definition["library_names"]       = self.properties["library_names"]
        symbol_definition["package_names"]       = self.properties["package_names"]
        symbol_definition["filename"]            = self.properties["filename"]
        symbol_definition["architecture_filename"] = ""
        symbol_definition["number_of_files"]     = self.properties["number_of_files"]
        symbol_definition["generate_path_value"] = self.properties["generate_path_value"]
        symbol_definition["architecture_name"]   = self.properties["architecture_name"]
        symbol_definition["architecture_list"]   = self.properties["architecture_list"]
        symbol_definition["additional_files"]    = self.properties["additional_sources"]
        symbol_definition["generic_definition"]  = self.properties["generic_definition"]
        symbol_definition["entity_name"]         = {"canvas_id": None,
                                                    "coords"   : [self.event_x + self.window.design.get_grid_size(), self.event_y - 1.5*self.window.design.get_grid_size()],
                                                    "name"     : self.properties["entity_name"]}
        all_instance_names = self.window.design.get_all_instance_names()
        symbol_definition["instance_name"]       = {"canvas_id": None,
                                                   "coords"    : [self.event_x + self.window.design.get_grid_size(), self.event_y - 0.5*self.window.design.get_grid_size()],
                                                   "name"      : self.get_new_instance_name(all_instance_names, self.properties["entity_name"])}
        symbol_definition["object_tag"]          = self.properties["object_tag"]
        height                                   = (max_pin_number+2) * self.window.design.get_grid_size()
        width                                    = 6 * self.window.design.get_grid_size()
        symbol_definition["rectangle"]           = {"coords"   : [self.event_x + 0.5*self.window.design.get_grid_size(),
                                                                 self.event_y - height,
                                                                 self.event_x + 0.5*self.window.design.get_grid_size() + width,
                                                                 self.event_y],
                                                   "canvas_id" : None} # None is a placeholder for the canvas ID that will be created later.
        if self.properties["generic_definition"]!="":
            generic_map = self.__create_a_generic_map_from_the_generic_definition()
        else:
            generic_map = ""
        symbol_definition["generic_block"] ={"coords" : [self.event_x + 0.5*self.window.design.get_grid_size(),
                                                         self.event_y - height - 0.1*self.window.design.get_grid_size()],
                                             "generic_map": generic_map,
                                             "canvas_id"  : None}
        x_offset_inputs  = 0
        x_offset_inouts  = width + 0.5*self.window.design.get_grid_size()
        x_offset_outputs = width + 0.5*self.window.design.get_grid_size()
        y_offset_inputs  = -1.5*self.window.design.get_grid_size()
        y_offset_inouts  = -1.5*self.window.design.get_grid_size()
        y_offset_outputs = -1.5*self.window.design.get_grid_size() - len(inout_list) * self.window.design.get_grid_size()
        port_location_list_inputs  = self.__create_port_list(input_list , self.input_polygon_coords , x_offset_inputs , y_offset_inputs)
        port_location_list_inouts  = self.__create_port_list(inout_list , self.inout_polygon_coords , x_offset_inouts , y_offset_inouts)
        port_location_list_outputs = self.__create_port_list(output_list, self.output_polygon_coords, x_offset_outputs, y_offset_outputs)
        symbol_definition["port_list"] = port_location_list_inputs + port_location_list_inouts + port_location_list_outputs
        symbol_definition["port_range_visibility"] = "Show"
        return symbol_definition

    def __create_a_generic_map_from_the_generic_definition(self):
        generic_map = ""
        generic_definition_lines = self.properties["generic_definition"].split("\n")
        if self.properties["language"]=="VHDL":
            for line in generic_definition_lines:
                if line != "":
                    if "--" in line:
                        comment = re.sub(r".*--", "--", line)
                    else:
                        comment = ""
                    line = re.sub(r"--.*"       , ""     , line)
                    line = re.sub(r";"          , ","    , line)
                    line = re.sub(r"\s*:.*:=\s*", " => " , line) # with init value: replace from "type declaration" to ":=" by "=>"
                    line = re.sub(r"\s*:.*"     , " => ?", line) # without init value: replace from "type declaration" to end of line by "=>"
                    line = re.sub(r"^constant " , ""     , line) # remove the optional "constant" type
                    generic_map += line  + comment + "\n"
        else: # Verilog
            for line in generic_definition_lines:
                if line != "":
                    generic_map += line + "\n"
        return generic_map[:-1] # remove last return

    def get_new_instance_name(self, all_instance_names, entity_name):
        if entity_name + "_inst" not in all_instance_names:
            return entity_name + "_inst"
        id_number = 1
        while entity_name + "_inst" + str(id_number) in all_instance_names:
            id_number += 1
        return entity_name + "_inst" + str(id_number)

    def __create_port_list(self, port_list, triangle_polygon_coords, x_offset, y_offset):
        port_location_list   = []
        for port_declaration in port_list:
            y_offset -= self.window.design.get_grid_size()
            new_coords = []
            for index, coord in enumerate(triangle_polygon_coords):
                if index%2==0:
                    new_coords.append(self.event_x + coord + x_offset) # x-coordinate
                else:
                    new_coords.append(self.event_y + coord + y_offset) # y-coordinate
            port_location_list_entry = {}
            port_location_list_entry["declaration"]    = port_declaration
            port_location_list_entry["coords"]         = new_coords
            port_location_list_entry["canvas_id"]      = None
            port_location_list_entry["canvas_id_text"] = None
            port_location_list.append(port_location_list_entry)
        return port_location_list

    def __split_port_list(self, portlist):
        inputs  = []
        outputs = []
        inouts  = []
        for entry in portlist:
            if self.properties["language"]=="VHDL":
                if   " : in "    in entry:
                    inputs.append (entry)
                elif " : out "   in entry:
                    outputs.append(entry)
                elif " : inout " in entry:
                    inouts.append (entry)
            else:
                if   "input "  in entry:
                    inputs.append (entry)
                elif "output " in entry:
                    outputs.append(entry)
                elif "inout "  in entry:
                    inouts.append (entry)
        return inputs, outputs, inouts

    def __move_to(self, event):
        new_event_x = self.diagram_tab.canvas.canvasx(event.x)
        new_event_y = self.diagram_tab.canvas.canvasy(event.y)
        delta_x = new_event_x-self.event_x
        delta_y = new_event_y-self.event_y
        self.diagram_tab.canvas.move(self.properties["object_tag"], delta_x, delta_y)
        self.event_x = new_event_x
        self.event_y = new_event_y

    def __end_inserting(self, event):
        #print("__end_inserting")
        self.event_x = self.diagram_tab.canvas.canvasx(event.x)
        self.event_y = self.diagram_tab.canvas.canvasx(event.y)
        self.symbol_ref.move_to_grid_ext()
        self.__restore_diagram_tab_canvas_bindings()
        self.window.config(cursor="arrow")
        defined_packages = self.window.design.get_interface_packages()
        checked_definitions = 'in tab "Entity Declarations"'
        if self.window.design.get_number_of_files()==2:
            defined_packages += self.window.design.get_internals_packages()
            checked_definitions = 'in tab "Entity Declarations" or in tab "Architecture Declarations"'
        for package_name in self.symbol_ref.symbol_definition["package_names"]:
            if package_name not in defined_packages and self.window.design.get_language()=="VHDL":
                messagebox.showerror("Warning", "The package " + package_name + " is used by entity " + self.properties["entity_name"] +
                                    " but not defined " + checked_definitions)

    def __restore_diagram_tab_canvas_bindings(self):
        self.__remove_insertion_bindings_from_canvas()
        self.diagram_tab.create_canvas_bindings()

    def __remove_insertion_bindings_from_canvas(self):
        self.diagram_tab.canvas.unbind ("<Motion>"  , self.func_id_motion)
        self.diagram_tab.canvas.unbind ("<Button-1>", self.func_id_button)
        self.diagram_tab.canvas.unbind ("<Leave>"   , self.func_id_leave )
        self.window.unbind             ("<Escape>"  , self.func_id_escape)
        self.func_id_motion = None
        self.func_id_button = None
        self.func_id_leave  = None
        self.func_id_escape = None

    def __reject(self, event):
        self.__restore_diagram_tab_canvas_bindings()
        self.diagram_tab.canvas.focus_set() # needed to catch Ctrl-z
        self.symbol_ref.delete_item(push_design_to_stack=False)
        self.window.config(cursor="arrow")
        del self # Once the last reference to an object is deleted, the object will be removed by garbage collection.
