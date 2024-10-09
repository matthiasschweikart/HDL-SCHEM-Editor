"""
When a symbol is updated, this class removes obsolete ports, adds new ports and modifies changed ports.
"""
import symbol_polygon_move
import constants

class SymbolUpdatePorts():
    def __init__(self, root, window, diagram_tab, symbol, symbol_define_ref):
        self.root        = root
        self.window      = window
        self.diagram_tab = diagram_tab
        self.symbol      = symbol
        instance_updated = symbol_define_ref.get_symbol_insertion_ref()
        if instance_updated is None: # Is None, if a VHDL with a non integer generic was tried to instantiate into a Verilog design.
            return
        symbol_definition_upd = instance_updated.get_symbol_definition_for_update() # From a symbol which is calculated by symbol_insertion.Instance at x=0, y=0
        ports_to_remove, ports_type_change = self.__search_list1_entries_in_list2(symbol.symbol_definition["port_list"], symbol_definition_upd   ["port_list"])
        ports_to_add   , _                 = self.__search_list1_entries_in_list2(symbol_definition_upd   ["port_list"], symbol.symbol_definition["port_list"])
        symbol_definition_port_list_entries_to_remove = []
        for port_entry_index in ports_to_add:
            self.__shift_symbol_bottom_down_for_new_port()
            new_port_entry = symbol_definition_upd["port_list"][port_entry_index]
            port_name, port_direction, port_range = symbol.get_port_name_and_direction_and_range(new_port_entry["declaration"])
            rectangle_coords = self.diagram_tab.canvas.coords(symbol.symbol_definition["rectangle"]["canvas_id"])
            new_polygon_coords, text_delta_x, text_anchor = self.__calculate_positions(port_direction, instance_updated, rectangle_coords)
            if "symbol_color" in symbol.symbol_definition["rectangle"]:
                symbol_color = symbol.symbol_definition["rectangle"]["symbol_color"]
            else:
                symbol_color = constants.SYMBOL_DEFAULT_COLOR
            new_port_entry["canvas_id"]      = self.diagram_tab.canvas.create_polygon(*new_polygon_coords , outline="black", fill=symbol_color, activefill="red",
                                                                                        tags=(symbol.symbol_definition["object_tag"], "schematic-element"))
            new_port_entry["canvas_id_text"] = self.diagram_tab.canvas.create_text(new_polygon_coords[4] + text_delta_x, new_polygon_coords[5],
                                                                                    font=("Courier", self.window.design.get_font_size()),
                                                                                    text=port_name + port_range, anchor=text_anchor,
                                                                                    tag=(symbol.symbol_definition["object_tag"], "instance-text", "schematic-element"))
            symbol.symbol_definition["port_list"].append(new_port_entry)

            symbol.sym_bind_funcid_port_show[new_port_entry["canvas_id_text"]] = self.diagram_tab.canvas.tag_bind(new_port_entry["canvas_id_text"], "<Enter>",
                lambda event, canvas_id_text=new_port_entry["canvas_id_text"]: self.symbol.show_port_type(canvas_id_text))
            symbol.sym_bind_funcid_port_hide[new_port_entry["canvas_id_text"]] = self.diagram_tab.canvas.tag_bind(new_port_entry["canvas_id_text"], "<Leave>",
                lambda event, canvas_id_text=new_port_entry["canvas_id_text"]: self.symbol.hide_port_type(canvas_id_text))

            symbol.sym_bind_funcid_polygons[new_port_entry["canvas_id"]] = self.diagram_tab.canvas.tag_bind(new_port_entry["canvas_id"], "<Button-1>",
                lambda event, canvas_id=new_port_entry["canvas_id"], port_name_canvas_id=new_port_entry["canvas_id_text"]:
                    symbol_polygon_move.PolygonMove(event, self.window, self.diagram_tab, symbol, canvas_id, port_name_canvas_id, True))
        for change_entry in ports_type_change:
            # change_entry = {"index_in_port_list": index_in_port_list, "index_in_port_list_upd": index_in_port_list_upd,
            #                 "direction_change": direction_has_changed, "declaration": port_declaration}
            declaration     = symbol.symbol_definition["port_list"][change_entry["index_in_port_list"]    ]["declaration"]
            declaration_upd = symbol_definition_upd   ["port_list"][change_entry["index_in_port_list_upd"]]["declaration"]
            _        , port_direction    , _              = symbol.get_port_name_and_direction_and_range(declaration)
            port_name, port_direction_upd, port_range_upd = symbol.get_port_name_and_direction_and_range(declaration_upd)
            self.__update_declaration_in_symbol_definition(change_entry, declaration_upd)
            self.__update_port_range_in_graphics(change_entry, port_name + port_range_upd)
            if port_direction_upd!=port_direction:
                polygon_coords_new = self.__calculate_polygon_coords_for_direction_change(change_entry, port_direction, port_direction_upd)
                self.__update_polygon_in_symbol_definition(change_entry, polygon_coords_new)
                self.__update_polygon_in_graphics         (change_entry, polygon_coords_new)
        for port_to_remove in ports_to_remove:
            self.diagram_tab.canvas.delete(symbol.symbol_definition["port_list"][port_to_remove]["canvas_id"])
            self.diagram_tab.canvas.delete(symbol.symbol_definition["port_list"][port_to_remove]["canvas_id_text"])
            symbol_definition_port_list_entries_to_remove.append(port_to_remove) # Remove at the end to keep indices valid in the meantime.
        if ports_to_remove: # must be done last, as it modifies the order of entries in self.symbol_definition["port_list"]
            new_port_list = []
            port_list = symbol.symbol_definition["port_list"]
            for index, port_list_entry in enumerate(port_list):
                if index in ports_to_remove:
                    self.diagram_tab.canvas.delete(symbol.symbol_definition["port_list"][index]["canvas_id"])
                    self.diagram_tab.canvas.delete(symbol.symbol_definition["port_list"][index]["canvas_id_text"])
                else:
                    new_port_list.append(port_list_entry)
            symbol.symbol_definition["port_list"] = new_port_list
        # Unnötig, weil das schon in update() erledigt wird.
        #    if ports_to_add or ports_to_remove or ports_type_change:
        #     symbol.store_item(push_design_to_stack=True, signal_design_change=True)

    def __shift_symbol_bottom_down_for_new_port(self):
        rectangle_coords = self.diagram_tab.canvas.coords(self.symbol.symbol_definition["rectangle"]["canvas_id"])
        rectangle_coords[3] += self.window.design.get_grid_size()
        self.diagram_tab.canvas.coords(self.symbol.symbol_definition["rectangle"]["canvas_id"],
                                        rectangle_coords[0], rectangle_coords[1],
                                        rectangle_coords[2], rectangle_coords[3])
        entity_name_coords = self.diagram_tab.canvas.coords(self.symbol.symbol_definition["entity_name"]["canvas_id"])
        entity_name_coords[1] += self.window.design.get_grid_size()
        self.diagram_tab.canvas.coords(self.symbol.symbol_definition["entity_name"]["canvas_id"],
                                        entity_name_coords[0], entity_name_coords[1])
        instance_name_coords = self.diagram_tab.canvas.coords(self.symbol.symbol_definition["instance_name"]["canvas_id"])
        instance_name_coords[1] += self.window.design.get_grid_size()
        self.diagram_tab.canvas.coords(self.symbol.symbol_definition["instance_name"]["canvas_id"],
                                        instance_name_coords[0], instance_name_coords[1])

    def __calculate_positions(self, port_direction, instance_updated, rectangle_coords):
        new_polygon_coords = [0, 0, 0, 0, 0, 0, 0, 0]
        if port_direction=="in":
            polygon_coords = instance_updated.get_polygon_coords_for("input")
            new_polygon_coords[0] = polygon_coords[0] + rectangle_coords[0] - 0.5 * self.window.design.get_grid_size()
            new_polygon_coords[2] = polygon_coords[2] + rectangle_coords[0] - 0.5 * self.window.design.get_grid_size()
            new_polygon_coords[4] = polygon_coords[4] + rectangle_coords[0] - 0.5 * self.window.design.get_grid_size()
            new_polygon_coords[6] = polygon_coords[6] + rectangle_coords[0] - 0.5 * self.window.design.get_grid_size()
            new_polygon_coords[1] = polygon_coords[1] + rectangle_coords[3] - 0.5 * self.window.design.get_grid_size()
            new_polygon_coords[3] = polygon_coords[3] + rectangle_coords[3] - 0.5 * self.window.design.get_grid_size()
            new_polygon_coords[5] = polygon_coords[5] + rectangle_coords[3] - 0.5 * self.window.design.get_grid_size()
            new_polygon_coords[7] = polygon_coords[7] + rectangle_coords[3] - 0.5 * self.window.design.get_grid_size()
            text_delta_x = 0.1 * self.window.design.get_grid_size()
            text_anchor  = "w"
        else:
            if port_direction=="out":
                polygon_coords = instance_updated.get_polygon_coords_for("output")
            else:
                polygon_coords = instance_updated.get_polygon_coords_for("inout")
            new_polygon_coords[0] = polygon_coords[0] + rectangle_coords[2]
            new_polygon_coords[2] = polygon_coords[2] + rectangle_coords[2]
            new_polygon_coords[4] = polygon_coords[4] + rectangle_coords[2]
            new_polygon_coords[6] = polygon_coords[6] + rectangle_coords[2]
            new_polygon_coords[1] = polygon_coords[1] + rectangle_coords[3] - 0.5 * self.window.design.get_grid_size()
            new_polygon_coords[3] = polygon_coords[3] + rectangle_coords[3] - 0.5 * self.window.design.get_grid_size()
            new_polygon_coords[5] = polygon_coords[5] + rectangle_coords[3] - 0.5 * self.window.design.get_grid_size()
            new_polygon_coords[7] = polygon_coords[7] + rectangle_coords[3] - 0.5 * self.window.design.get_grid_size()
            text_delta_x = - 0.1 * self.window.design.get_grid_size()
            text_anchor  = "e"
        return new_polygon_coords, text_delta_x, text_anchor

    def __update_declaration_in_symbol_definition(self, change_entry, declaration_upd):
        self.symbol.symbol_definition["port_list"][change_entry["index_in_port_list"]]["declaration"] = declaration_upd

    def __update_port_range_in_graphics(self, change_entry, new_text):
        self.diagram_tab.canvas.itemconfigure(self.symbol.symbol_definition["port_list"][change_entry["index_in_port_list"]]["canvas_id_text"], text=new_text)

    def __update_polygon_in_graphics(self, change_entry, polygon_coords_new):
        self.diagram_tab.canvas.coords(self.symbol.symbol_definition["port_list"][change_entry["index_in_port_list"]]["canvas_id"], polygon_coords_new)

    def __update_polygon_in_symbol_definition(self, change_entry, polygon_coords_new):
        self.symbol.symbol_definition["port_list"][change_entry["index_in_port_list"]]["coords"] = polygon_coords_new

    def __calculate_polygon_coords_for_direction_change(self, change_entry, port_direction, port_direction_upd):
        polygon_coords   = self.diagram_tab.canvas.coords(self.symbol.symbol_definition["port_list"][change_entry["index_in_port_list"]]["canvas_id"])
        rectangle_coords = self.diagram_tab.canvas.coords(self.symbol.symbol_definition["rectangle"]["canvas_id"])
        polygon_coords_new = list(polygon_coords)
        polygon_rotation_point_x     = polygon_coords[4]
        polygon_rotation_point_y     = polygon_coords[5]
        if   abs(polygon_rotation_point_x - rectangle_coords[0])<self.window.design.get_grid_size()/10:
            polygon_position = "left"
        elif abs(polygon_rotation_point_x - rectangle_coords[2])<self.window.design.get_grid_size()/10:
            polygon_position = "right"
        elif abs(polygon_rotation_point_y - rectangle_coords[1])<self.window.design.get_grid_size()/10:
            polygon_position = "top"
        else:
            polygon_position = "bottom"
        if polygon_position in ["left", "right"]:
            if port_direction=="in" and port_direction_upd=="out":
                polygon_coords_new[2] = polygon_coords[4]
                polygon_coords_new[6] = polygon_coords[4]
            elif port_direction=="in" and port_direction_upd=="inout":
                polygon_coords_new[2] = (polygon_coords[0] + polygon_coords[4])/2
                polygon_coords_new[6] = (polygon_coords[0] + polygon_coords[4])/2
            elif port_direction=="out" and port_direction_upd=="in":
                polygon_coords_new[2] = polygon_coords[0]
                polygon_coords_new[6] = polygon_coords[0]
            elif port_direction=="out" and port_direction_upd=="inout":
                polygon_coords_new[2] = (polygon_coords[0] + polygon_coords[4])/2
                polygon_coords_new[6] = (polygon_coords[0] + polygon_coords[4])/2
            elif port_direction=="inout" and port_direction_upd=="in":
                polygon_coords_new[2] = polygon_coords[0]
                polygon_coords_new[6] = polygon_coords[0]
            elif port_direction=="inout" and port_direction_upd=="out":
                polygon_coords_new[2] = polygon_coords[4]
                polygon_coords_new[6] = polygon_coords[4]
        else: # polygon_position in ["top", "bottom"]
            if port_direction=="in" and port_direction_upd=="out":
                polygon_coords_new[3] = polygon_coords[5]
                polygon_coords_new[7] = polygon_coords[5]
            elif port_direction=="in" and port_direction_upd=="inout":
                polygon_coords_new[3] = (polygon_coords[1] + polygon_coords[5])/2
                polygon_coords_new[7] = (polygon_coords[1] + polygon_coords[5])/2
            elif port_direction=="out" and port_direction_upd=="in":
                polygon_coords_new[3] = polygon_coords[1]
                polygon_coords_new[7] = polygon_coords[1]
            elif port_direction=="out" and port_direction_upd=="inout":
                polygon_coords_new[3] = (polygon_coords[1] + polygon_coords[5])/2
                polygon_coords_new[7] = (polygon_coords[1] + polygon_coords[5])/2
            elif port_direction=="inout" and port_direction_upd=="in":
                polygon_coords_new[3] = polygon_coords[1]
                polygon_coords_new[7] = polygon_coords[1]
            elif port_direction=="inout" and port_direction_upd=="out":
                polygon_coords_new[3] = polygon_coords[5]
                polygon_coords_new[7] = polygon_coords[5]
        return polygon_coords_new

    def __search_list1_entries_in_list2(self, port_list1, port_list2):
        ports_to_remove       = []
        direction_has_changed = []
        type_has_changed      = []
        for index_in_port_list, port_entry in enumerate(port_list1):
            port_declaration = port_entry["declaration"]
            hit = False
            for index_in_port_list_upd, port_entry_upd in enumerate(port_list2):
                port_declaration_upd = port_entry_upd["declaration"]
                if port_declaration_upd==port_declaration:
                    hit = True
                else:
                    port_name    , port_direction    , _ = self.symbol.get_port_name_and_direction_and_range(port_declaration)
                    port_name_upd, port_direction_upd, _ = self.symbol.get_port_name_and_direction_and_range(port_declaration_upd)
                    if port_name_upd==port_name:
                        hit = True
                        # direction or range or both have changed
                        if port_direction_upd!=port_direction:
                            direction_has_changed = True
                        else:
                            direction_has_changed = False
                        type_has_changed.append({"index_in_port_list": index_in_port_list, "index_in_port_list_upd": index_in_port_list_upd,
                                                 "direction_change": direction_has_changed, "declaration": port_declaration})
            if hit is False:
                ports_to_remove.append(index_in_port_list)
        return ports_to_remove, type_has_changed
