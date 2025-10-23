"""
This class creates the shape of the instance's symbol.
The information how the symbol has to look like, is given to the constructor by
the parameter symbol_definition and stored in self.symbol_definition.
When building the symbol, self.symbol_definition is updated in several moments.
Attention: coords are not updated

Data-structure of symbol_definition:
{
    "language"             : "VHDL"|"Verilog"|"SystemVerilog"          # Language of the symbol
    "configuration"        : {"library": <library-name>, "config_statement": "None"|"Embedded"|"At Instance"},
    "library_names"        : [<library-name>, ...],  # used for entity
    "package_names"        : [<package-name>, ...],  # used for entity
    "filename"             : <String with complete filename>,
    "architecture_filename": <String with complete filename>,
    "number_of_files"      : <integer of value 1 or 2>,
    "generate_path_value"  : <String with path to the generated HDL>,
    "additional_files"     : [<filename1>, <filename2>, ... ]  # These files must be compiled before the symbol can be compiled (only needed for HDL-symbols).
    "entity_name"          : {"canvas_id": <canvas_id of entity-text>  , "coords" : [x1, y1], "name": <entity-name>},
    "instance_name"        : {"canvas_id": <canvas_id of instance-text>, "coords" : [x1, y1], "name": <instance-name>},
    "architecture_name"    : <String>,
    "architecture_list"    : [<name1>, <name2>, ...]
    "object_tag"           : "instance_<symbol_insertion.instance_id>",
    "rectangle"            : {"canvas_id": <canvas_id of rectangle>, "coords": [x1, y1, x2, y2], "symbol_color": color},
    "generic_definition"   : <String with all the component generic declarations and comments> # Original code taken from VHDL- or Verilog- or hfe- or hse- file of the instance.
    "generic_defaults"     : [<Generic-declaration>, ...], # Taken from generic_definition
    "generic_block"        : {"canvas_id": <canvas-id of text>, "coords": [x1, y1], "generic_map" : <Text>},
    "port_list"            : [{"canvas_id": <canvas-id of polygon>, "canvas_id_text": <canvas-id of text-field>,
                               "coords": [x1, y1, x2, y2, x3, y3, x4, y4], "declaration": <HDL-declaration of port (without any initialization value and comment)> }, ...],
    "port_range_visibility": "Show"|"Hide"
}
"""
import os
import subprocess
import json
import tkinter as tk
from   tkinter import messagebox
import re

import schematic_window
import symbol_rectangle_move
import symbol_polygon_move
import listbox_animated
import wire_insertion
import signal_name
import edit_line
import edit_text
import symbol_define
import symbol_properties
import symbol_update_ports
import symbol_update_infos
import interface_input
import interface_output
import interface_inout
import block_insertion
import symbol_reading
import interface_insertion
import hdl_generate
import design_data
import file_read
import generate_frame
import color_changer
import constants

class Symbol:
    def __init__(self,
                 root,
                 window, #      : schematic_window.SchematicWindow,
                 diagram_tab, # : notebook_diagram_tab.NotebookDiagramTab,
                 symbol_definition):
        self.root                      = root
        self.window                    = window
        self.diagram_tab               = diagram_tab
        self.symbol_definition         = self.__fix_additional_files_bug(symbol_definition)
        self.event_x                   = None
        self.event_y                   = None
        self.funcid_delete             = None
        self.func_id_motion            = None
        self.func_id_button_release    = None
        self.sym_bind_funcid_button    = None
        self.sym_bind_funcid_dbutton   = None
        self.sym_bind_funcid_enter     = None
        self.sym_bind_funcid_leave     = None
        self.sym_bind_funcid_menu      = None
        self.sym_bind_funcid_edit_in   = None
        self.sym_bind_funcid_edit_gb   = None
        self.sym_bind_funcid_polygons  = {}
        self.original_text             = None
        self.background_rectangle      = None
        self.after_identifier          = None
        self.sym_bind_funcid_port_show = {}
        self.sym_bind_funcid_port_hide = {}
        self.sym_bind_funcid_show1     = None
        self.sym_bind_funcid_hide1     = None
        self.sym_bind_funcid_show2     = None
        self.sym_bind_funcid_hide2     = None
        rectangle_coords = self.symbol_definition["rectangle"]["coords"]
        if "symbol_color" in self.symbol_definition["rectangle"]:
            symbol_color = self.symbol_definition["rectangle"]["symbol_color"]
        else:
            symbol_color = constants.SYMBOL_DEFAULT_COLOR
        self.symbol_definition["rectangle"]["canvas_id"]     = self.diagram_tab.canvas.create_rectangle(*rectangle_coords,
                                                                                                    fill=symbol_color,
                                                                                                    activefill="red",
                                                                                                    tags=(self.symbol_definition["object_tag"], "layer4", "schematic-element"))
        if self.symbol_definition["architecture_name"]!="":
            entity_name = self.symbol_definition["entity_name"]["name"] + '.' + self.symbol_definition["architecture_name"]
        else:
            entity_name = self.symbol_definition["entity_name"]["name"]
        self.symbol_definition["entity_name"  ]["canvas_id"] = self.diagram_tab.canvas.create_text(*self.symbol_definition["entity_name"]["coords"],
                                                                                                   font=("Courier", self.window.design.get_font_size()),
                                                                                                   text=entity_name,
                                                                                                   anchor="w", fill="black",
                                                                                                   tags=(self.symbol_definition["object_tag"], "instance-text",
                                                                                                         "layer3", "schematic-element"))
        self.symbol_definition["instance_name"]["canvas_id"] = self.diagram_tab.canvas.create_text(*self.symbol_definition["instance_name"]["coords"],
                                                                                                   font=("Courier", self.window.design.get_font_size()),
                                                                                                   text=self.symbol_definition["instance_name"]["name"],
                                                                                                   anchor="w", fill="black",
                                                                                                   tags=(self.symbol_definition["object_tag"], "instance-text",
                                                                                                         "instance-name", "layer3", "schematic-element"))
        if "generic_block" in self.symbol_definition:
            if self.symbol_definition["language"]=="SystemVerilog":
                symbol_language_for_check = "Verilog"
            else:
                symbol_language_for_check = self.symbol_definition["language"]
            if self.window.design.get_language()=="SystemVerilog":
                design_language_for_check = "Verilog"
            else:
                design_language_for_check = self.window.design.get_language()
            if symbol_language_for_check!=design_language_for_check:
                generic_map = self.__get_translated_generic_map(self.symbol_definition["generic_block"]["generic_map"])
            else:
                generic_map = self.symbol_definition["generic_block"]["generic_map"]
            self.symbol_definition["generic_block"]["canvas_id"] = self.diagram_tab.canvas.create_text(*self.symbol_definition["generic_block"]["coords"],
                                                                   font=("Courier", self.window.design.get_font_size()),
                                                                   text=generic_map, anchor="sw",
                                                                   tags=(self.symbol_definition["object_tag"], "instance-text", "generic-map", "layer3", "schematic-element"))
        for port_entry in self.symbol_definition["port_list"]:
            port_declaration = port_entry["declaration"]
            polygon_coords   = port_entry["coords"]
            polygon_rectangle_point_x  = polygon_coords[4]
            polygon_rectangle_point_y  = polygon_coords[5]
            # When a symbol is copied, the polygon_coords have values which are based at there own grid_size.
            # Before the symbol is adapted to self.window.design.get_grid_size(), it is created here.
            # So here the grid_size of the symbol must be used, in order to place the portnames at the correct place:
            grid_size_of_symbol = abs(2*(polygon_coords[4]-polygon_coords[0]))
            port_name, _, port_range = self.get_port_name_and_direction_and_range(port_declaration)
            if   abs(polygon_rectangle_point_x-rectangle_coords[0])<grid_size_of_symbol/10: # "left"
                text_delta_x = 0.1 * grid_size_of_symbol
                text_delta_y = 0
                text_anchor  = "w"
                text_angle   = "0"
            elif abs(polygon_rectangle_point_x-rectangle_coords[2])<grid_size_of_symbol/10: # "right"
                text_delta_x = - 0.1 * grid_size_of_symbol
                text_delta_y = 0
                text_anchor  = "e"
                text_angle   = "0"
            elif abs(polygon_rectangle_point_y-rectangle_coords[1])<grid_size_of_symbol/10: # "top"
                text_delta_x = 0
                text_delta_y = + 0.1 * grid_size_of_symbol
                text_anchor  = "e"
                text_angle   = "90"
            #elif abs(polygon_rectangle_point_y-rectangle_coords[3])<grid_size_of_symbol/10: # "bottom"
            else:
                text_delta_x = 0
                text_delta_y = - 0.1 * grid_size_of_symbol
                text_anchor  = "w"
                text_angle   = "90"
            if self.symbol_definition["port_range_visibility"]=="Hide":
                combined_port_name = port_name
            else:
                combined_port_name = port_name + port_range
            #print("polygon_coords =", polygon_coords , " of " + port_name)
            port_entry["canvas_id"]      = self.diagram_tab.canvas.create_polygon(*polygon_coords , outline="black", fill=symbol_color, activefill="red",
                                                                                        tags=(self.symbol_definition["object_tag"], "layer4", "schematic-element"))
            port_entry["canvas_id_text"] = self.diagram_tab.canvas.create_text(polygon_coords[4] + text_delta_x, polygon_coords[5] + text_delta_y,
                                                                                     font=("Courier", self.window.design.get_font_size()),
                                                                                     text=combined_port_name, anchor=text_anchor, angle=text_angle,
                                                                                     tags=(self.symbol_definition["object_tag"], "instance-text", "layer3", "schematic-element"))
        self.menu_entry_list = tk.StringVar()
        if self.symbol_definition["port_range_visibility"]=="Hide":
            self.menu_entry_list.set(Symbol.menu_string2)
        else:
            self.menu_entry_list.set(Symbol.menu_string1)
        self.__add_bindings_to_symbol()
        # When the symbol is created by copy/paste, then it is also stored by notebook_diagram_tab.__move_selection_end().
        # When the symbol is created by symbol_insertion, then it is also stored by symbol_insertion.__end_inserting().
        # But when the symbol is created by notebook_diagram_tab.update_from(), then this store command is needed:
        self.store_item(push_design_to_stack=False, signal_design_change=False)  # Changed to False, because when switching architectures no design change takes place.

    def __fix_additional_files_bug(self, symbol_definition):
         # Due to a bug in 4.6, the symbol-definition may contain the additional-files as array of characters.
        fixed_entry = []
        file_name = ""
        for list_element in symbol_definition["additional_files"]:
            if len(symbol_definition["additional_files"])!=1 and len(list_element) in (0,1):
                if list_element==',':
                    fixed_entry.append(file_name)
                    file_name = ""
                elif list_element=="":
                    file_name += " "
                else:
                    file_name += list_element
        if file_name!="": # Append last file-name.
            fixed_entry.append(file_name)
        if fixed_entry:
            #print("__fix_additional_files_bug: fix for symbol", symbol_definition["entity_name"]["name"])
            symbol_definition["additional_files"] = fixed_entry
        return symbol_definition

    def __get_translated_generic_map(self, generic_map):
        if self.symbol_definition["language"]=="VHDL":
            # translate into Verilog
            generic_map = re.sub(">" , ""  , generic_map)
            generic_map = re.sub("--", "//", generic_map)
        else:
            # translate into VHDL
            generic_map = re.sub("=" , "=>", generic_map)
            generic_map = re.sub("//", "--", generic_map)
        return generic_map

    def get_port_name_and_direction_and_range(self, port_declaration):
        #print("port_declaration =", port_declaration)
        if self.symbol_definition["language"]=="VHDL":
            port_name, port_direction_and_type = port_declaration.rsplit(':')
            if " in " in port_direction_and_type:
                port_direction = "in"
            elif " out " in port_direction_and_type:
                port_direction = "out"
            else:
                port_direction = "inout"
            port_name  = port_name.strip()
            port_range = self.__get_vhdl_port_range(port_direction_and_type)
        else:
            range_start = port_declaration.find('[')
            range_end   = port_declaration.find(']')
            if range_start!=-1:
                port_range = port_declaration[range_start:range_end + 1]
            else:
                port_range = ""
            port_declaration = re.sub(r"\/\/HDL-SCHEM-Editor.*", "", port_declaration)
            word_list = port_declaration.split()
            port_name = word_list[-1]
            if "input" in word_list:
                port_direction = "in"
            elif "output" in word_list:
                port_direction = "out"
            else:
                port_direction = "inout"
        return port_name, port_direction, port_range

    def __get_vhdl_port_range(self,port_direction_and_type):
        #print("port_direction_and_type =", port_direction_and_type)
        if "(" not in port_direction_and_type or " range " in port_direction_and_type:
            return ""
        port_range = re.sub(r"^.*?\(" , r"(" , port_direction_and_type) # remove all before the starting '('
        port_range = re.sub(r"(.*\))" , r"\1", port_range             ) # remove all after the ending ')'
        port_range = re.sub(r"\("     , "["  , port_range             )
        port_range = re.sub(r"\)"     , "]"  , port_range             )
        port_range = re.sub(" downto ", ":", port_range, flags=re.I)
        port_range = re.sub(" to "    , ":", port_range, flags=re.I)
        # Do not show unnecessary blanks around ':', '+', '-', '*', '/':
        port_range = re.sub(r"\s*:\s*" , ":" , port_range)
        port_range = re.sub(r"\s*\+\s*", "+" , port_range)
        port_range = re.sub(r"\s*-\s*" , "-" , port_range)
        port_range = re.sub(r"\s*\*\s*", "*" , port_range)
        port_range = re.sub(r"\s*\/\s*", "/" , port_range)
        return port_range

    def store_item(self, push_design_to_stack, signal_design_change):
        self.symbol_definition = json.loads(json.dumps(self.symbol_definition)) # Make a real copy, so that the symbol_definition stored in stack is not modified.
        self.__update_coords_info_in_symbol_definition()
        self.__update_instance_name_in_symbol_definition()
        self.__update_generic_block_in_symbol_definition()
        self.window.design.store_instance_in_canvas_dictionary(self.symbol_definition["rectangle"]["canvas_id"], self,
                                                               self.symbol_definition, push_design_to_stack, signal_design_change)

    def __update_instance_name_in_symbol_definition(self):
        self.symbol_definition["instance_name"]["name"] = self.diagram_tab.canvas.itemcget(self.symbol_definition["instance_name"]["canvas_id"], "text")

    def __update_generic_block_in_symbol_definition(self):
        if "generic_block" in self.symbol_definition:
            self.symbol_definition["generic_block"]["generic_map"] = self.diagram_tab.canvas.itemcget(self.symbol_definition["generic_block"]["canvas_id"], "text")

    def __update_coords_info_in_symbol_definition(self):
        coords = self.diagram_tab.canvas.coords(self.symbol_definition["rectangle"]    ["canvas_id"])
        self.symbol_definition["rectangle"]    ["coords"] = coords
        coords = self.diagram_tab.canvas.coords(self.symbol_definition["entity_name"]  ["canvas_id"])
        self.symbol_definition["entity_name"]  ["coords"] = coords
        coords = self.diagram_tab.canvas.coords(self.symbol_definition["instance_name"]["canvas_id"])
        self.symbol_definition["instance_name"]["coords"] = coords
        if "port_list" in self.symbol_definition:
            for index, port_entry  in enumerate(self.symbol_definition["port_list"]):
                self.symbol_definition["port_list" ][index]["coords"] = self.diagram_tab.canvas.coords(port_entry["canvas_id"])
        if "generic_block" in self.symbol_definition:
            self.symbol_definition["generic_block" ]["coords"] = self.diagram_tab.canvas.coords(self.symbol_definition["generic_block" ]["canvas_id"])

    def delete_item(self, push_design_to_stack):
        self.__bind_diagramtab_delete_to_canvas()
        self.window.design.remove_canvas_item_from_dictionary(self.symbol_definition["rectangle"]["canvas_id"], push_design_to_stack)
        self.diagram_tab.canvas.delete(self.symbol_definition["object_tag"])
        self.diagram_tab.create_canvas_bindings() # Needed because when "self" is deleted after entering the symbol, no __at_leave will take place.
        del self # Once the last reference to an object is deleted, the object will be removed by garbage collection.

    def __bind_diagramtab_delete_to_canvas(self):
        if self.funcid_delete is not None: # Check is needed, because sometimes a select-rectangle and the delete-binding both perform a delete.
            self.diagram_tab.canvas.unbind("<Delete>", self.funcid_delete)
            self.funcid_delete = None
            self.diagram_tab.canvas.bind("<Delete>", lambda event: self.diagram_tab.delete_selection())

    def __add_bindings_to_symbol(self):
        self.sym_bind_funcid_button = self.diagram_tab.canvas.tag_bind(self.symbol_definition["rectangle"]["canvas_id"],"<Button-1>",
                                      lambda event: symbol_rectangle_move.RectangleMove(event, self.window, self.diagram_tab, self, self.symbol_definition))
        self.sym_bind_funcid_dbutton= self.diagram_tab.canvas.tag_bind(self.symbol_definition["rectangle"]["canvas_id"],"<Double-Button-1>",
                                                                       lambda event: self.__open_source_code_after_idle())
        self.sym_bind_funcid_enter  = self.diagram_tab.canvas.tag_bind(self.symbol_definition["rectangle"]["canvas_id"],"<Enter>"          ,lambda event: self.__at_enter())
        self.sym_bind_funcid_leave  = self.diagram_tab.canvas.tag_bind(self.symbol_definition["rectangle"]["canvas_id"],"<Leave>"          ,lambda event: self.__at_leave())
        self.sym_bind_funcid_menu   = self.diagram_tab.canvas.tag_bind(self.symbol_definition["rectangle"]["canvas_id"],"<Button-3>"       ,self.__show_menu)
        for port_definition in self.symbol_definition["port_list"]:
            self.sym_bind_funcid_polygons [port_definition["canvas_id"]] = self.diagram_tab.canvas.tag_bind(port_definition["canvas_id"], "<Button-1>",
                lambda event, canvas_id=port_definition["canvas_id"], port_name_canvas_id=port_definition["canvas_id_text"]:
                    symbol_polygon_move.PolygonMove(event, self.window, self.diagram_tab, self, canvas_id, port_name_canvas_id, True))
            self.sym_bind_funcid_port_show[port_definition["canvas_id_text"]] = self.diagram_tab.canvas.tag_bind(port_definition["canvas_id_text"], "<Enter>",
                lambda event, canvas_id_text=port_definition["canvas_id_text"]: self.show_port_type(canvas_id_text))
            self.sym_bind_funcid_port_hide[port_definition["canvas_id_text"]] = self.diagram_tab.canvas.tag_bind(port_definition["canvas_id_text"], "<Leave>",
                lambda event, canvas_id_text=port_definition["canvas_id_text"]: self.hide_port_type(canvas_id_text))
        self.sym_bind_funcid_show1   = self.diagram_tab.canvas.tag_bind(self.symbol_definition["entity_name"]["canvas_id"],"<Enter>",
                                                            lambda event, canvas_id=self.symbol_definition["entity_name"]["canvas_id"]: self.__show_symbol_info_start(canvas_id))
        self.sym_bind_funcid_hide1   = self.diagram_tab.canvas.tag_bind(self.symbol_definition["entity_name"]["canvas_id"],"<Leave>",
                                                            lambda event, canvas_id=self.symbol_definition["entity_name"]["canvas_id"]: self.__hide_symbol_info(canvas_id))
        self.sym_bind_funcid_show2   = self.diagram_tab.canvas.tag_bind(self.symbol_definition["instance_name"]["canvas_id"],"<Enter>",
                                                            lambda event, canvas_id=self.symbol_definition["instance_name"]["canvas_id"]: self.__show_symbol_info_start(canvas_id))
        self.sym_bind_funcid_hide2   = self.diagram_tab.canvas.tag_bind(self.symbol_definition["instance_name"]["canvas_id"],"<Leave>",
                                                            lambda event, canvas_id=self.symbol_definition["instance_name"]["canvas_id"]: self.__hide_symbol_info(canvas_id))
        self.sym_bind_funcid_edit_in = self.diagram_tab.canvas.tag_bind(self.symbol_definition["instance_name"]["canvas_id"],"<Double-Button-1>",
                                                                        lambda event: edit_line.EditLine(self.window.design,
                                                                                                         self.diagram_tab,
                                                                                                         self.symbol_definition["instance_name"]["canvas_id"],
                                                                                                         self))
        if "generic_block" in self.symbol_definition:
            self.sym_bind_funcid_edit_gb = self.diagram_tab.canvas.tag_bind(self.symbol_definition["generic_block"]["canvas_id"],"<Double-Button-1>",
                                                                        lambda event: edit_text.EditText("generic_block",
                                                                                                         self.window,
                                                                                                         self.diagram_tab,
                                                                                                         self.symbol_definition["generic_block"]["canvas_id"],
                                                                                                         self))

    def show_port_type(self, canvas_id_text):
        self.after_identifier = self.diagram_tab.canvas.after(1000, lambda : self.show_port_type_after_delay(canvas_id_text))

    def show_port_type_after_delay(self, canvas_id_text):
        for entry in self.symbol_definition["port_list"]:
            if entry["canvas_id_text"]==canvas_id_text:
                port_declaration = entry["declaration"]
                self.original_text = self.diagram_tab.canvas.itemcget(canvas_id_text, "text")
                self.diagram_tab.canvas.itemconfigure(canvas_id_text, text=port_declaration, font=("Courier", 10))
                self.background_rectangle = self.diagram_tab.canvas.create_rectangle(self.diagram_tab.canvas.bbox(canvas_id_text), fill="white")
                self.diagram_tab.canvas.tag_raise(canvas_id_text, self.background_rectangle)

    def hide_port_type(self, canvas_id_text):
        if self.after_identifier is not None:
            self.diagram_tab.canvas.after_cancel(self.after_identifier)
        if self.background_rectangle is not None:
            self.diagram_tab.canvas.delete(self.background_rectangle)
            self.diagram_tab.canvas.itemconfigure(canvas_id_text, text=self.original_text, font=("Courier", self.window.design.get_font_size()))
            self.background_rectangle = None

    def __show_symbol_info_start(self, canvas_id):
        self.after_identifier = self.diagram_tab.canvas.after(1000, self.__show_symbol_info, canvas_id)

    def __show_symbol_info(self, canvas_id):
        self.original_text = self.diagram_tab.canvas.itemcget(canvas_id, "text")
        tags = self.diagram_tab.canvas.gettags(canvas_id)
        if "instance-name" in tags: # Get also the entity name.
            text =  self.diagram_tab.canvas.itemcget(self.symbol_definition["entity_name"  ]["canvas_id"], "text") + "\n"
            text += self.original_text + "\n"
        else:                       # Get also the instance name.
            text =  self.original_text + "\n"
            text += self.diagram_tab.canvas.itemcget(self.symbol_definition["instance_name"  ]["canvas_id"], "text") + "\n"
        text += self.diagram_tab.design.get_language()
        self.diagram_tab.canvas.itemconfigure(canvas_id, text=text, font=("Courier", 10))
        self.background_rectangle = self.diagram_tab.canvas.create_rectangle(self.diagram_tab.canvas.bbox(canvas_id),fill="white")
        self.diagram_tab.canvas.tag_raise(canvas_id, self.background_rectangle)

    def __hide_symbol_info(self, canvas_id):
        self.diagram_tab.canvas.after_cancel(self.after_identifier)
        if self.background_rectangle is not None:
            self.diagram_tab.canvas.delete(self.background_rectangle)
            self.background_rectangle = None
            self.diagram_tab.canvas.itemconfigure(canvas_id, text=self.original_text, font=("Courier", self.window.design.get_font_size()))

    def __remove_bindings_from_symbol(self):
        self.diagram_tab.canvas.tag_unbind(self.symbol_definition["rectangle"    ]["canvas_id"],"<Button-1>"       , self.sym_bind_funcid_button)
        self.diagram_tab.canvas.tag_unbind(self.symbol_definition["rectangle"    ]["canvas_id"],"<Double-Button-1>", self.sym_bind_funcid_dbutton)
        self.diagram_tab.canvas.tag_unbind(self.symbol_definition["rectangle"    ]["canvas_id"],"<Enter>"          , self.sym_bind_funcid_enter)
        self.diagram_tab.canvas.tag_unbind(self.symbol_definition["rectangle"    ]["canvas_id"],"<Leave>"          , self.sym_bind_funcid_leave)
        self.diagram_tab.canvas.tag_unbind(self.symbol_definition["entity_name"  ]["canvas_id"],"<Enter>"          , self.sym_bind_funcid_show1)
        self.diagram_tab.canvas.tag_unbind(self.symbol_definition["entity_name"  ]["canvas_id"],"<Leave>"          , self.sym_bind_funcid_hide1)
        self.diagram_tab.canvas.tag_unbind(self.symbol_definition["rectangle"    ]["canvas_id"],"<Button-3>"       , self.sym_bind_funcid_menu)
        self.diagram_tab.canvas.tag_unbind(self.symbol_definition["instance_name"]["canvas_id"],"<Double-Button-1>", self.sym_bind_funcid_edit_in)
        self.diagram_tab.canvas.tag_unbind(self.symbol_definition["instance_name"]["canvas_id"],"<Enter>"          , self.sym_bind_funcid_show2)
        self.diagram_tab.canvas.tag_unbind(self.symbol_definition["instance_name"]["canvas_id"],"<Leave>"          , self.sym_bind_funcid_hide2)
        for port_definition in self.symbol_definition["port_list"]:
            self.diagram_tab.canvas.tag_unbind(port_definition["canvas_id"]     , "<Button-1>", self.sym_bind_funcid_polygons [port_definition["canvas_id"]])
            self.diagram_tab.canvas.tag_unbind(port_definition["canvas_id_text"], "<Enter>"   , self.sym_bind_funcid_port_show[port_definition["canvas_id_text"]])
            self.diagram_tab.canvas.tag_unbind(port_definition["canvas_id_text"], "<Leave>"   , self.sym_bind_funcid_port_hide[port_definition["canvas_id_text"]])
        if "generic_block" in self.symbol_definition:
            self.diagram_tab.canvas.tag_unbind(self.symbol_definition["generic_block"]["canvas_id"], "<Double-Button-1>", self.sym_bind_funcid_edit_gb)
        self.sym_bind_funcid_button   = None
        self.sym_bind_funcid_dbutton  = None
        self.sym_bind_funcid_enter    = None
        self.sym_bind_funcid_leave    = None
        self.sym_bind_funcid_menu     = None
        self.sym_bind_funcid_edit_in  = None
        self.sym_bind_funcid_edit_gb  = None
        self.sym_bind_funcid_polygons = {}
        self.sym_bind_funcid_show1    = None
        self.sym_bind_funcid_hide1    = None
        self.sym_bind_funcid_show2    = None
        self.sym_bind_funcid_hide2    = None

    def __at_enter(self):
        if not self.diagram_tab.canvas.find_withtag("selected"):
            self.diagram_tab.canvas.focus_set()
            self.funcid_delete = self.diagram_tab.canvas.bind("<Delete>", lambda event: self.delete_item(push_design_to_stack=True))

    def __at_leave(self):
        self.__bind_diagramtab_delete_to_canvas()

    def __show_menu(self, event):
        menu = listbox_animated.ListboxAnimated(self.diagram_tab.canvas, listvariable=self.menu_entry_list, height=10,
                                                bg='grey', width=50, activestyle='dotbox', relief="raised")
        event_x = self.diagram_tab.canvas.canvasx(event.x)
        event_y = self.diagram_tab.canvas.canvasy(event.y)
        menue_window = self.diagram_tab.canvas.create_window(event_x+40,event_y,window=menu)
        menu.bind("<Button-1>", lambda event: self.__evaluate_menu_after_idle(menue_window, menu))
        menu.bind("<Leave>"   , lambda event: self.__close_menu(menue_window, menu))

    def __evaluate_menu_after_idle(self, menue_window, menu):
        self.diagram_tab.canvas.after_idle(self.__evaluate_menu, menue_window, menu)

    def __evaluate_menu(self, menue_window, menu):
        selected_entry = menu.get(menu.curselection()[0])
        if "Open" in selected_entry:
            self.__open_source_code_after_idle()
        elif 'Edit properties' in selected_entry:
            symbol_properties.SymbolProperties(self)
        elif 'Add input and output connectors' in selected_entry:
            self.__add_connectors()
            self.store_item(push_design_to_stack=True, signal_design_change=True)
        elif 'Add signal stubs and keep' in selected_entry:
            self.__add_signal_stubs("keep")
            self.store_item(push_design_to_stack=True, signal_design_change=True)
        elif 'Add signal stubs and remove' in selected_entry:
            self.__add_signal_stubs("remove")
            self.store_item(push_design_to_stack=True, signal_design_change=True)
        elif 'Add signal stubs and ask' in selected_entry:
            self.__add_signal_stubs("ask")
            self.store_item(push_design_to_stack=True, signal_design_change=True)
        elif 'Update symbol from source (with generics)' in selected_entry:
            self.symbol_definition["port_range_visibility"] = "Show"
            self.menu_entry_list.set(Symbol.menu_string1)
            symbol_define_ref = symbol_define.SymbolDefine(self.root, self.window, self.diagram_tab, self.get_filename())
            symbol_update_ports.SymbolUpdatePorts         (self.root, self.window, self.diagram_tab, self, symbol_define_ref)
            symbol_update_infos.SymbolUpdateInfos         (self.root, self.window, self.diagram_tab, self, symbol_define_ref,
                                                           update_generics=True, update_by_reading_from_other_file=False)
            # store_item is not needed, as SybolUpdateInfos calls Symbol.update(), where a store_item is called.
        elif 'Update symbol from source (without generics)' in selected_entry:
            self.symbol_definition["port_range_visibility"] = "Show"
            self.menu_entry_list.set(Symbol.menu_string1)
            symbol_define_ref = symbol_define.SymbolDefine(self.root, self.window, self.diagram_tab, self.get_filename())
            symbol_update_ports.SymbolUpdatePorts         (self.root, self.window, self.diagram_tab, self, symbol_define_ref)
            symbol_update_infos.SymbolUpdateInfos         (self.root, self.window, self.diagram_tab, self, symbol_define_ref,
                                                           update_generics=False, update_by_reading_from_other_file=False)
            # store_item is not needed, as SybolUpdateInfos calls Symbol.update(), where a store_item is called.
        elif 'Hide' in selected_entry:
            self.menu_entry_list.set(Symbol.menu_string2)
            self.__hide_port_ranges()
            self.store_item(push_design_to_stack=True, signal_design_change=False)
        elif 'Show' in selected_entry:
            self.menu_entry_list.set(Symbol.menu_string1)
            self.__show_port_ranges()
            self.store_item(push_design_to_stack=True, signal_design_change=False)
        elif 'Change color' in selected_entry:
            new_color = color_changer.ColorChanger(constants.SYMBOL_DEFAULT_COLOR, self.window).get_new_color()
            if new_color is not None:
                self.__update_color_in_symbol_definition_and_graphic(new_color)
                self.store_item(push_design_to_stack=True, signal_design_change=True)
        self.__close_menu(menue_window, menu)

    def __update_color_in_symbol_definition_and_graphic(self, new_color):
        self.symbol_definition["rectangle"]["symbol_color"] = new_color
        self.diagram_tab.canvas.itemconfigure(self.symbol_definition["rectangle"]["canvas_id"], fill=new_color)
        for port_entry in self.symbol_definition["port_list"]:
            self.diagram_tab.canvas.itemconfigure(port_entry["canvas_id"], fill=new_color)

    def __hide_port_ranges(self):
        for port_entry in self.symbol_definition["port_list"]:
            port_declaration = port_entry["declaration"]
            port_name, _, _ = self.get_port_name_and_direction_and_range(port_declaration)
            self.diagram_tab.canvas.itemconfigure(port_entry["canvas_id_text"], text=port_name)
        self.symbol_definition["port_range_visibility"] = "Hide"

    def __show_port_ranges(self):
        for port_entry in self.symbol_definition["port_list"]:
            port_declaration = port_entry["declaration"]
            port_name, _, port_range = self.get_port_name_and_direction_and_range(port_declaration)
            self.diagram_tab.canvas.itemconfigure(port_entry["canvas_id_text"], text=port_name + port_range)
        self.symbol_definition["port_range_visibility"] = "Show"

    def __close_menu(self, menue_window, menu):
        menu.destroy()
        self.diagram_tab.canvas.delete(menue_window)

    def __add_connectors(self):
        list_of_port_dictionaries = self.__add_signal_stubs("keep")
        for port_dictionary in list_of_port_dictionaries:
            wire_coords = self.diagram_tab.canvas.coords(port_dictionary["wire_tag"])
            if   port_dictionary["position"] == "left":
                connector_coords = wire_coords[0:2]
                if port_dictionary["direction"]=="input":
                    orientation = 0
                else:
                    orientation = 2
            elif port_dictionary["position"] == "bottom":
                connector_coords = wire_coords[0:2]
                if port_dictionary["direction"]=="input":
                    orientation = 3
                else:
                    orientation = 1
            elif port_dictionary["position"] == "right":
                connector_coords = wire_coords[2:]
                if port_dictionary["direction"]=="input":
                    orientation = 2
                else:
                    orientation = 0
            else: # top
                connector_coords = wire_coords[2:]
                if port_dictionary["direction"]=="input":
                    orientation = 1
                else:
                    orientation = 3
            if port_dictionary["direction"]=="input":
                interface_input .Input (self.window, self.diagram_tab, None, follow_mouse=False, location=connector_coords, orientation=orientation)
            elif port_dictionary["direction"]=="output":
                interface_output.Output(self.window, self.diagram_tab, None, follow_mouse=False, location=connector_coords, orientation=orientation)
            else:
                interface_inout .Inout (self.window, self.diagram_tab, None, follow_mouse=False, location=connector_coords, orientation=orientation)

    def __add_signal_stubs(self, mode):
        if mode=="remove":
            remove_all_port_name_suffixes = True
            ask_for_each_suffix = False
        elif mode=="keep":
            remove_all_port_name_suffixes = False
            ask_for_each_suffix = False
        else: # "ask"
            remove_all_port_name_suffixes = False
            ask_for_each_suffix = True
        list_of_port_dictionaries = [] # Filled with dictionaries, which have these keys: "position", "wire_tag", "direction"
        wire_ref = None
        for port_entry in self.symbol_definition["port_list"]:
            polygon_coords  = self.diagram_tab.canvas.coords(port_entry["canvas_id"])
            if self.__port_is_open(polygon_coords):
                port_dictionary = {} # keys to be used: "direction", "position", "wire_tag"
                port_declaration = port_entry["declaration"]
                port_dictionary["direction"] = self.__get_port_direction_from_port_declaration(port_declaration)
                if self.window.design.get_language()=="VHDL":
                    signal_declaration = self.__create_vhdl_signal_declaration(port_declaration)
                else: # Verilog or SystemVerilog design
                    signal_declaration = self.__create_verilog_signal_declaration(port_declaration)
                if   polygon_coords[0]<self.symbol_definition["rectangle"]["coords"][0]: # left
                    position = "left"
                    wire_coords = [polygon_coords[0] - 8*self.window.design.get_grid_size(), polygon_coords[1], polygon_coords[0], polygon_coords[1]]
                elif polygon_coords[0]>self.symbol_definition["rectangle"]["coords"][2]: # right
                    position = "right"
                    wire_coords = [polygon_coords[0], polygon_coords[1], polygon_coords[0] + 8*self.window.design.get_grid_size(), polygon_coords[1]]
                elif polygon_coords[1]<self.symbol_definition["rectangle"]["coords"][1]: # top
                    position = "top"
                    wire_coords = [polygon_coords[0], polygon_coords[1], polygon_coords[0], polygon_coords[1] - 8*self.window.design.get_grid_size()]
                elif polygon_coords[1]>self.symbol_definition["rectangle"]["coords"][3]: # bottom
                    position = "bottom"
                    wire_coords = [polygon_coords[0], polygon_coords[1] + 8*self.window.design.get_grid_size(), polygon_coords[0], polygon_coords[1]]
                port_dictionary["position"] = position

                if self.symbol_definition["language"]=="VHDL":
                    port_name = re.sub(" *:.*", "", signal_declaration)
                else:
                    port_name = port_declaration.split()[-1]
                if port_name.endswith("_i") or port_name.endswith("_o") or port_name.endswith("_io") :
                    if not ask_for_each_suffix:
                        remove_this_port_name_suffix = "no"
                    else:
                        remove_this_port_name_suffix = messagebox.askquestion('Found suffix "_i", "_o", "_io":', "Remove suffix in " + port_name +"?", default="no")
                    if remove_all_port_name_suffixes or remove_this_port_name_suffix=="yes":
                        if self.symbol_definition["language"]=="VHDL":
                            signal_declaration = re.sub("_i :|_o :|_io :", " :", signal_declaration)
                        else:
                            signal_declaration = re.sub("_i$|_o$|_io$", "", signal_declaration)
                width = self.__determine_line_width(port_declaration)
                wire_ref = wire_insertion.Wire(self.root, self.window, self.diagram_tab, #push_design_to_stack=False,
                                               coords=wire_coords,
                                               tags="adding_signal_stubs", arrow="none", width=width)
                wire_tag = wire_ref.get_object_tag()
                port_dictionary["wire_tag"] = wire_tag
                if   position=="left":
                    #signal_name_delta_x = 0.5 * self.window.design.get_grid_size()
                    signal_name_delta_x = self.window.design.get_grid_size()
                    signal_name_delta_y = 0
                    signal_name_angle   = 0
                elif position=="right":
                    #signal_name_delta_x = 0.5 * self.window.design.get_grid_size()
                    signal_name_delta_x = self.window.design.get_grid_size()
                    signal_name_delta_y = 0
                    signal_name_angle   = 0
                elif position=="top":
                    signal_name_delta_x = 0
                    #signal_name_delta_y = - 0.5 * self.window.design.get_grid_size()
                    signal_name_delta_y = - self.window.design.get_grid_size()
                    signal_name_angle   = 90
                elif position=="bottom":
                    signal_name_delta_x = 0
                    #signal_name_delta_y = - 0.5 * self.window.design.get_grid_size()
                    signal_name_delta_y = - self.window.design.get_grid_size()
                    signal_name_angle   = 90
                signal_name.SignalName(self.window.design, self.diagram_tab, # push_design_to_stack=True,
                                    coords=[wire_coords[0] + signal_name_delta_x, wire_coords[1] + signal_name_delta_y], angle=signal_name_angle,
                                    wire_tag=wire_tag, declaration=signal_declaration)
                list_of_port_dictionaries.append(port_dictionary)
        if wire_ref is not None:
            wire_ref.add_dots_new_for_all_wires()
        #self.store_item(push_design_to_stack=True, signal_design_change=True)
        return list_of_port_dictionaries

    def __create_vhdl_signal_declaration(self, port_declaration):
        if self.symbol_definition["language"]=="VHDL":
            signal_declaration = re.sub(" in | out | inout ", " ", port_declaration)
        else: # self.symbol_definition["language"]=="Verilog/SystemVerilog"
            if "[" in port_declaration:
                port_range = re.sub(r".*\[(.*)\].*", r"\1", port_declaration)
                bounds = port_range.split(":")
                if bounds[0].isnumeric() and bounds[1].isnumeric():
                    if int(bounds[0])>=int(bounds[1]):
                        port_range_direction = " downto "
                    else:
                        port_range_direction = " to "
                else:
                    port_range_direction = re.sub(r".*//HDL-SCHEM-Editor:", "", port_declaration)
                    port_range_direction = ' ' + port_range_direction + ' '
                    port_declaration = re.sub(r"//HDL-SCHEM-Editor:.*", "", port_declaration)
                port_declaration_list = port_declaration.split(" ")
                signal_declaration = port_declaration_list[-1] + " : " + "std_logic_vector(" + bounds[0] + port_range_direction + bounds[1] + ")"
            else:
                port_declaration_list = port_declaration.split(" ")
                signal_declaration = port_declaration_list[-1] + " : " + "std_logic"
        return signal_declaration

    def __create_verilog_signal_declaration(self, port_declaration):
        if self.symbol_definition["language"]=="VHDL":
            port_declaration = self.__translate_port_declaration_from_vhdl_into_verilog(port_declaration)
        port_declaration   = re.sub(" reg "    , " "    , port_declaration)
        port_declaration   = re.sub(" wire "   , " "    , port_declaration)
        port_declaration   = re.sub(" logic "  , " "    , port_declaration)
        port_declaration   = re.sub("^input *" , "wire ", port_declaration)
        port_declaration   = re.sub("^output *", "wire ", port_declaration)
        signal_declaration = re.sub("^inout *" , "wire ", port_declaration)
        return signal_declaration

    def __get_port_direction_from_port_declaration(self, port_declaration):
        if self.symbol_definition["language"]=="VHDL":
            port_declaration_without_comment = re.sub(r"--.*", "", port_declaration)
            if " in " in port_declaration_without_comment:
                port_direction = "input"
            elif " out " in port_declaration:
                port_direction = "output"
            else:
                port_direction = "inout"
        else: # self.symbol_definition["language"]=="Verilog/SystemVerilog"
            port_declaration_without_comment = re.sub(r"//.*", "", port_declaration) # remove comments at the end of the string.
            if "input " in port_declaration_without_comment:
                port_direction = "input"
            elif "output " in port_declaration:
                port_direction = "output"
            else:
                port_direction = "inout"
        return port_direction

    def __translate_port_declaration_from_vhdl_into_verilog(self, port_declaration):
        port_declaration = re.sub(r"--.*", "", port_declaration)
        port_declaration = "wire " + port_declaration
        if " downto " in port_declaration:
            port_declaration = re.sub(r"(wire )(.*?)\s*:.*\((.*) downto (.*)\).*", r"\1[\3:\4] \2", port_declaration)
        elif " to " in port_declaration:
            port_declaration = re.sub(r"(wire )(.*?)\s*:.*\((.*) to (.*)\).*"    , r"\1[\3:\4] \2", port_declaration)
        else:
            port_declaration = re.sub(r"\s*:.*", "", port_declaration)
        return port_declaration

    def __port_is_open(self, polygon_coords):
        overlapping_ids = self.diagram_tab.canvas.find_overlapping(polygon_coords[0]-1, polygon_coords[1]-1, polygon_coords[0]+1, polygon_coords[1]+1)
        for canvas_id in overlapping_ids:
            if self.diagram_tab.canvas.type(canvas_id)=="line" and "grid_line" not in self.diagram_tab.canvas.gettags(canvas_id):
                return False
        return True

    def __determine_line_width(self, port_declaration):
        if ((self.window.design.get_language()=="VHDL" and "(" in port_declaration) or
            (self.window.design.get_language()!="VHDL" and "[" in port_declaration)):
            return 3
        return 1

    def __open_source_code_after_idle(self):
        # Wait until all events are handled, because otherwise handling of this
        # events would make self.window the active window again.
        self.window.after_idle(Symbol.open_source_code, self.root, self.window, self.symbol_definition["filename"], self.symbol_definition["architecture_name"])

    def move_to_grid_ext(self):
        touching_point = "middle"
        delta_x, delta_y = self.__get_delta_to_grid(touching_point)
        self.diagram_tab.canvas.move(self.symbol_definition["object_tag"], delta_x, delta_y)
        #print("symbol_instance: move_to_grid_ext, before store_item: canvas_id =", self.symbol_definition["rectangle"]["canvas_id"])
        self.store_item(push_design_to_stack=True, signal_design_change=True)
        #rint("symbol_instance: move_to_grid_ext, after store_item:references =", self.window.design.get_references(canvas_ids=[self.symbol_definition["rectangle"]["canvas_id"]]))

    def __get_delta_to_grid(self, touching_point):
        coords = self.diagram_tab.canvas.coords(self.symbol_definition["rectangle"]["canvas_id"])
        if   touching_point=="top_left":
            remainder_x = (coords[0] - 0.5*self.window.design.get_grid_size()) % self.window.design.get_grid_size()
            remainder_y = (coords[1] - 0.5*self.window.design.get_grid_size()) % self.window.design.get_grid_size()
        elif touching_point=="top_right":
            remainder_x = (coords[2] - 0.5*self.window.design.get_grid_size()) % self.window.design.get_grid_size()
            remainder_y = (coords[1] - 0.5*self.window.design.get_grid_size()) % self.window.design.get_grid_size()
        elif touching_point=="bottom_right":
            remainder_x = (coords[2] - 0.5*self.window.design.get_grid_size()) % self.window.design.get_grid_size()
            remainder_y = (coords[3] - 0.5*self.window.design.get_grid_size()) % self.window.design.get_grid_size()
        elif touching_point=="bottom_left":
            remainder_x = (coords[0] - 0.5*self.window.design.get_grid_size()) % self.window.design.get_grid_size()
            remainder_y = (coords[3] - 0.5*self.window.design.get_grid_size()) % self.window.design.get_grid_size()
        else: # touching_point=="middle"
            remainder_x = (coords[0] - 0.5*self.window.design.get_grid_size()) % self.window.design.get_grid_size()
            remainder_y = (coords[1] - 0.5*self.window.design.get_grid_size()) % self.window.design.get_grid_size()
        delta_x = - remainder_x
        delta_y = - remainder_y
        if remainder_x>self.window.design.get_grid_size()/2:
            delta_x += self.window.design.get_grid_size()
        if remainder_y>self.window.design.get_grid_size()/2:
            delta_y += self.window.design.get_grid_size()
        return delta_x, delta_y

    def select_item(self):
        #self.diagram_tab.canvas.itemconfigure(self.symbol_definition["rectangle"]["canvas_id"], fill="red")
        self.diagram_tab.canvas.itemconfigure(self.symbol_definition["rectangle"]["canvas_id"], outline="red", width=5)
        self.diagram_tab.canvas.itemconfigure(self.symbol_definition["rectangle"]["canvas_id"], dash=(5, ))
        port_list = self.symbol_definition["port_list"]
        for port_dict in port_list:
            self.diagram_tab.canvas.itemconfigure(port_dict["canvas_id"], fill="red")
        self.__remove_bindings_from_symbol()

    def unselect_item(self):
        self.diagram_tab.canvas.itemconfigure(self.symbol_definition["rectangle"]["canvas_id"], outline="black", width=1)
        self.diagram_tab.canvas.itemconfigure(self.symbol_definition["rectangle"]["canvas_id"], dash=())
        if "symbol_color" in self.symbol_definition["rectangle"]:
            symbol_color = self.symbol_definition["rectangle"]["symbol_color"]
        else:
            symbol_color = constants.SYMBOL_DEFAULT_COLOR
        port_list = self.symbol_definition["port_list"]
        for port_dict in port_list:
            self.diagram_tab.canvas.itemconfigure(port_dict["canvas_id"], fill=symbol_color)
        self.__add_bindings_to_symbol()

    def get_object_tag(self):
        return self.symbol_definition["object_tag"]

    def get_filename(self):
        return self.symbol_definition["filename"]

    def get_symbol_defintion(self):
        return self.symbol_definition

    def update(self, update_list, store_in_design_and_stack):
        # update() is called by __evaluate_menu when "update from source with/without generics" was selected:
        #   First SymbolUpdatePorts is created and changes self.symbol_definition directly.
        #   But then SymbolUpdateInfos is created and these items get updated by update():
        #   "entity_name", "generate_path_value", "generic_definition", "generic_block", "library"
        #   or only
        #   "entity_name", "generate_path_value", "library".
        # update() is called by __evaluate_menu/SymbolProperties when "edit properties" was selected and the created property window is closed by "save".
        #   Then these items may get updated:
        #   "library", "architecture_name", "config_statement", "filename", "additional_files", "port_range_visibility"
        #   If "filename" was updated, then (as if "update from source" was called) SymbolUpdatePorts and SymbolUpdateInfos are created and change:
        #   "entity_name", "generate_path_value", "generic_definition", "generic_block", "library"
        #   As "library" is part of both groups, it is important to handle it before "filename", because the new file shall win, if it also
        #   changes "library".
        for key in update_list:
            if   key=="library"              : # key will be used by symbol_properties.py and by symbol_update_infos.py.
                # This defines the VHDL-library, from which the symbol has to be taken at compile time (used in embedded configuration).
                self.symbol_definition["configuration"]["library"]          = update_list[key]
            elif key=="config_statement"     : # key will be used by symbol_properties.py
                self.symbol_definition["configuration"]["config_statement"] = update_list[key]
            elif key=="architecture_name"    : # key will be used by symbol_properties.py
                self.__switch_architecture_for_submodule(update_list[key])
            elif key=="architecture_list"    : # key will be used by symbol_properties.py
                self.symbol_definition["architecture_list"]                 = update_list[key]
            elif key=="additional_files"     : # key will be used by symbol_properties.py and by symbol_update_infos.py
                self.symbol_definition["additional_files"]                  = update_list[key]
            elif key=="filename"             : # key will be used by symbol_properties.py
                self.symbol_definition["filename"]                          = update_list[key]
                # The object symbol_define_ref has the attribute symbol_properties which is used for update:
                symbol_define_ref = symbol_define.SymbolDefine(self.root, self.window, self.diagram_tab, self.get_filename())
                symbol_update_ports.SymbolUpdatePorts(self.root, self.window, self.diagram_tab, self, symbol_define_ref)
                symbol_update_infos.SymbolUpdateInfos(self.root, self.window, self.diagram_tab, self, symbol_define_ref,update_generics=True,update_by_reading_from_other_file=True)
            elif key=="architecture_filename": # key will be used by symbol_properties.py
                self.symbol_definition["architecture_filename"]             = update_list[key]
            elif key=="number_of_files":  # key will be used by symbol_properties.py
                self.symbol_definition["number_of_files"]                   = update_list[key]
            elif key=="port_range_visibility": # key will be used by symbol_properties.py
                self.symbol_definition["port_range_visibility"]             = update_list[key]
                if update_list[key]=="Hide":
                    self.__hide_port_ranges()
                else:
                    self.__show_port_ranges()
            elif key=="generate_path_value"  : # key is defined by symbol_update_infos.py
                self.symbol_definition["generate_path_value"]               = update_list[key]
            elif key=="entity_name"          : # key is defined by symbol_update_infos.py
                self.symbol_definition["entity_name"]["name"]               = update_list[key]
                if self.symbol_definition["architecture_name"]!="":
                    entity_name = self.symbol_definition["entity_name"]["name"] + '.' + self.symbol_definition["architecture_name"]
                else:
                    entity_name = self.symbol_definition["entity_name"]["name"]
                self.diagram_tab.canvas.itemconfigure(self.symbol_definition["entity_name"]["canvas_id"], text=entity_name)
            elif key=="generic_definition"   : # key is defined by symbol_update_infos.py
                self.symbol_definition["generic_definition"]                = update_list[key]
            elif key=="generic_block"        : # key is defined by symbol_update_infos.py
                if self.symbol_definition["language"]!=self.window.design.get_language():
                    generic_map = self.__get_translated_generic_map(update_list[key])
                else:
                    generic_map = update_list[key]
                self.diagram_tab.canvas.itemconfigure(self.symbol_definition["generic_block"]["canvas_id"], text=generic_map)
                self.symbol_definition["generic_block"]["generic_map"]      = update_list[key]
        if update_list and store_in_design_and_stack:
            self.store_item(push_design_to_stack=True, signal_design_change=True)

    def __switch_architecture_for_submodule(self, new_architecture_name):
        submodule_window = None
        for opened_subwindow in schematic_window.SchematicWindow.open_window_dict:
            if opened_subwindow.design.get_path_name()==self.symbol_definition["filename"]:
                submodule_window = opened_subwindow
        if submodule_window is not None: # is None for HFE- or HDL- instances
            if new_architecture_name in submodule_window.notebook_top.diagram_tab.architecture_list:
                old_architecture_name = self.symbol_definition["architecture_name"]
                if submodule_window.design.get_architecture_name()!=new_architecture_name:
                    submodule_window.design.open_existing_schematic(old_architecture_name, new_architecture_name)
                    submodule_window.notebook_top.diagram_tab.architecture_combobox.set(new_architecture_name)
                self.symbol_definition["architecture_name"] = new_architecture_name
                self.__change_architecture_string_at_symbol()
            else:
                messagebox.showerror("Error by switching architectures:", "Architecture " + new_architecture_name + " does not exist.")
        else:
            # No opened_window was found for the design with this filename: self.symbol_definition["filename"]
            # This happens, when during link-dictionary generation no valid HDL was found for an instance.
            # Then linking is not possible as HDL and source file have different versions of the module.
            # Because no link-generation for this module was possible, no read of the module design file to the open_window_dict was started.
            self.symbol_definition["architecture_name"] = new_architecture_name
            self.__change_architecture_string_at_symbol()

    def __change_architecture_string_at_symbol(self):
        if self.symbol_definition["architecture_name"]!="":
            architecture_string = '.' + self.symbol_definition["architecture_name"]
        else:
            architecture_string = ""
        self.diagram_tab.canvas.itemconfigure(self.symbol_definition["entity_name"]["canvas_id"],
                                                text=self.symbol_definition["entity_name"]["name"] + architecture_string)

    def add_pasted_tag_to_all_canvas_items(self):
        list_of_canvas_ids = [self.symbol_definition["rectangle"    ]["canvas_id"],
                              self.symbol_definition["entity_name"  ]["canvas_id"],
                              self.symbol_definition["instance_name"]["canvas_id"],
                              self.symbol_definition["generic_block"]["canvas_id"]]
        for port_entry in self.symbol_definition["port_list"]:
            list_of_canvas_ids.append(port_entry["canvas_id"])
            list_of_canvas_ids.append(port_entry["canvas_id_text"])
        for canvas_id in list_of_canvas_ids:
            self.diagram_tab.canvas.addtag_withtag("pasted_tag", canvas_id)

    def adapt_coordinates_by_factor(self, factor):
        list_of_canvas_ids = [self.symbol_definition["rectangle"    ]["canvas_id"],
                              self.symbol_definition["entity_name"  ]["canvas_id"],
                              self.symbol_definition["instance_name"]["canvas_id"],
                              self.symbol_definition["generic_block"]["canvas_id"]]
        for port_entry in self.symbol_definition["port_list"]:
            list_of_canvas_ids.append(port_entry["canvas_id"])
            list_of_canvas_ids.append(port_entry["canvas_id_text"])
        for canvas_id in list_of_canvas_ids:
            coords = self.diagram_tab.canvas.coords(canvas_id)
            coords = [value*factor for value in coords]
            self.diagram_tab.canvas.coords(canvas_id, coords)


    @classmethod
    def get_pin_list(cls, symbol_definition):
        pin_list = []
        for port_list_entry in symbol_definition["port_list"]:
            if symbol_definition["configuration"]["config_statement"]=="At Instance":
                entity_call = "entity "
                entity_call += symbol_definition["configuration"]["library"] + "."
                entity_call += symbol_definition["entity_name"]["name"]
                if symbol_definition["architecture_name"]!="":
                    entity_call += "(" + symbol_definition["architecture_name"] + ")"
            else:
                entity_call = symbol_definition["entity_name"]["name"]
            port_declaration = port_list_entry["declaration"]
            list_entry = {"type"             : entity_call,                                 # The key "type" is used, because pin_list is combined with a second dictionary
                          "instance_name"    : symbol_definition["instance_name"]["name"] , # which already has this key, see hdl_generate.HdlGenerate.create _declarations().
                          "architecture_name": symbol_definition["architecture_name"]     , # This name is used when highlighting through hierarchy is used.
                          "canvas_id"        : symbol_definition["rectangle"]["canvas_id"],
                          "coords"           : port_list_entry["coords"][0:2],
                          "port_declaration" : port_declaration}
            pin_list.append(list_entry)
        return pin_list

    @classmethod
    def get_generic_map(cls, symbol_definition):
        if "generic_block" in symbol_definition:
            return symbol_definition["generic_block"]["generic_map"]
        return []

    @classmethod
    def get_embedded_configuration(cls, symbol_definition):
        if symbol_definition["configuration"]["config_statement"]=="Embedded":
            config_statement = "    for "
            instance_name = re.sub(r"\s*--.*", "", symbol_definition["instance_name"]["name"])
            config_statement += instance_name + " : " + symbol_definition["entity_name"]["name"]
            config_statement += " use entity "+ symbol_definition["configuration"]["library"] + "." + symbol_definition["entity_name"]["name"]
            if symbol_definition["architecture_name"]!="":
                config_statement += "(" + symbol_definition["architecture_name"] + ")"
            config_statement += ";\n"
            return config_statement
        return ""

    @classmethod
    def get_library_from_instance_configuration(cls, symbol_definition):
        if symbol_definition["configuration"]["config_statement"]=="At Instance":
            return [symbol_definition["instance_name"]["name"], symbol_definition["configuration"]["library"]]
        return None

    @classmethod
    def get_generic_definition(cls, symbol_definition):
        return symbol_definition["generic_definition"]

    @classmethod
    def get_language(cls, symbol_definition):
        return symbol_definition["language"]

    @classmethod
    def get_canvas_id(cls, symbol_definition):
        return symbol_definition["rectangle"]["canvas_id"]

    @classmethod
    def get_entity_name(cls, symbol_definition):
        return symbol_definition["entity_name"]["name"]

    @classmethod
    def get_instance_name(cls, symbol_definition):
        return symbol_definition["instance_name"]["name"]

    @classmethod
    def get_symbol_definition_shifted(cls, symbol_definition, offset):
        symbol_definition["entity_name"  ]["coords"] = [coord + offset for coord in symbol_definition["entity_name"  ]["coords"]]
        symbol_definition["instance_name"]["coords"] = [coord + offset for coord in symbol_definition["instance_name"]["coords"]]
        symbol_definition["rectangle"    ]["coords"] = [coord + offset for coord in symbol_definition["rectangle"    ]["coords"]]
        symbol_definition["generic_block"]["coords"] = [coord + offset for coord in symbol_definition["generic_block"]["coords"]]
        for entry in symbol_definition["port_list"]:
            entry["coords"] = [coord + offset for coord in entry["coords"]]
        return symbol_definition

    @classmethod
    def get_priority_from_symbol_definition(cls, symbol_definition):
        comment = ""
        if "--" in symbol_definition["instance_name"]["name"]:
            comment = re.sub(r".*--", "", symbol_definition["instance_name"]["name"])
        elif "//" in symbol_definition["instance_name"]["name"]:
            comment = re.sub(r".*//", "", symbol_definition["instance_name"]["name"])
        if comment!="" and not comment.isspace():
            word_list = comment.split()
            if word_list[0].isnumeric():
                return int(word_list[0])
        return -1

    @classmethod
    def open_source_code(cls, root, window, path_name, arch_name):
        for open_window in schematic_window.SchematicWindow.open_window_dict:
            if open_window.design.get_path_name()==path_name:
                if open_window.design.get_architecture_name()!=arch_name and arch_name!="": # Some old Verilog-designs may have the arch-name "".
                    open_window.design.open_existing_schematic(open_window.design.get_architecture_name(), arch_name)
                    open_window.notebook_top.diagram_tab.architecture_combobox.set(arch_name)
                open_window.open_this_window()
                return
        if not os.path.isfile(path_name):
            path_name = cls.try_to_replace_not_found_name_by_correct_one(window, path_name)
        if path_name=="":
            return
        if path_name.endswith(".hse"):
            new_window = schematic_window.SchematicWindow(root, wire_insertion.Wire, signal_name.SignalName,
                            interface_input.Input, interface_output.Output, interface_inout.Inout, block_insertion.Block, symbol_reading.SymbolReading,
                            interface_insertion.InterfaceInsertion, Symbol, hdl_generate.GenerateHDL, design_data.DesignData, generate_frame.GenerateFrame,
                            visible=True, working_directory="")
            new_window.lift()
            architecture_name = arch_name
            file_read.FileRead(new_window, path_name, architecture_name, fill_link_dictionary=True)
            #new_window.attributes("-topmost", 1) # Pushes the window in the foreground
            #new_window.attributes("-topmost", 0) # Allows to put other windows in the foreground by clicking at an icon in the taskbar.
        else:
            if path_name.endswith(".hfe"):
                command = window.design.get_hfe_cmd()
            else:
                command = window.design.get_edit_cmd()
                if command=="" or command.isspace():
                    messagebox.showerror("Error in HDL-SCHEM-Editor", 'Cannot open source code of symbol because no "edit command" is defined in the control tab.')
                    return
            # Check if HFE was already started with design stored in path_name:
            success = Symbol.bring_process_in_foreground(path_name)
            if success:
                return
            # Under linux the command must be an array:
            cmd = []
            cmd.extend(command.split())
            cmd.append(path_name)
            window.config(cursor="watch")
            try:
                # Wenn der Sub-Prozess beim Start viele Ausgaben macht, dann scheint er sich sofort zu beenden.
                subprocess.Popen(cmd,
                    # text=True,              # needed when "for line in process.stdout"  is used.
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT)
                # Not used, because it blocks HSE:
                # for line in process.stdout: # Terminates when process.stdout is closed.
                #     window.notebook_top.log_tab.insert_line_in_log(line, state_after_insert="disabled")
            except FileNotFoundError:
                messagebox.showerror("Error in HDL-SCHEM-Editor", "Error when running " + command + ' "' + path_name + '"')
            window.config(cursor="arrow")

    @classmethod
    def bring_process_in_foreground(cls, path_name):
        name_of_dir, name_of_file = os.path.split(path_name)
        window_title = name_of_file + ' (' + name_of_dir + ")"
        if Symbol.window_is_aready_open(window_title):
            return True
        window_title = re.sub(r"/", r"\\", window_title)
        if Symbol.window_is_aready_open(window_title):
            return True
        window_title = name_of_file + ' (' + name_of_dir + ") *"
        if Symbol.window_is_aready_open(window_title):
            return True
        window_title = re.sub(r"/", r"\\", window_title)
        if Symbol.window_is_aready_open(window_title):
            return True
        return False

    @classmethod
    def window_is_aready_open(cls, window_title):
        # windows_already_open = getwindow.getWindowsWithTitle(window_title)
        # if windows_already_open:
        #     if windows_already_open[0].isMinimized:
        #         windows_already_open[0].restore()
        #     windows_already_open[0].activate()
        #     return True
        return False

    @classmethod
    def try_to_replace_not_found_name_by_correct_one(cls, window, path_name):
        _, file_name = os.path.split(path_name)
        path_name_parent = window.design.get_path_name()
        directory_parent, _ = os.path.split(path_name_parent)
        new_path_name = directory_parent +'/'+ file_name
        if os.path.isfile(new_path_name):
            use_new_filename = messagebox.askquestion("Source file not found",
                                                      "Shall the file\n" +
                                                       new_path_name +
                                                      "\nbe used instead of the not found\n" +
                                                       path_name)
            if use_new_filename=="yes":
                symbol_definitions = window.design.get_symbol_definitions()
                for symbol_definition in symbol_definitions:
                    if symbol_definition["filename"]==path_name:
                        ref = window.design.get_references([symbol_definition["rectangle"]["canvas_id"]])[0]
                        ref.symbol_definition["filename"] = new_path_name
                        ref.symbol_definition["architecture_filename"] = new_path_name
                        ref.store_item(push_design_to_stack=True, signal_design_change=True)
                return new_path_name
            return ""
        messagebox.showerror("Error in HDL-SCHEM-Editor", 'File\n' + path_name + "\nwas not found.")
        return ""

    menu_string1 = (
        r"""Open\ source\ (Double\ Mouseclick)
            Update\ symbol\ from\ source\ (with\ generics)
            Update\ symbol\ from\ source\ (without\ generics)
            Add\ input\ and\ output\ connectors
            Add\ signal\ stubs\ and\ keep\ suffixes\ ("_i",\ "_o",\ "_io")
            Add\ signal\ stubs\ and\ remove\ suffixes\ ("_i",\ "_o",\ "_io")
            Add\ signal\ stubs\ and\ ask\ at\ each\ suffix\ ("_i",\ "_o",\ "_io")
            Edit\ properties
            Hide\ ranges
            Change\ color
        """)
    menu_string2 = (
        r"""Open\ source\ (Double\ Mouseclick)
            Update\ symbol\ from\ source\ (with\ generics)
            Update\ symbol\ from\ source\ (without\ generics)
            Add\ input\ and\ output\ connectors
            Add\ signal\ stubs\ and\ keep\ suffixes\ ("_i",\ "_o",\ "_io")
            Add\ signal\ stubs\ and\ remove\ suffixes\ ("_i",\ "_o",\ "_io")
            Add\ signal\ stubs\ and\ ask\ at\ each\ suffix\ ("_i",\ "_o",\ "_io")
            Edit\ properties
            Show\ ranges
            Change\ color
        """)
