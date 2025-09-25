"""
This class moves the symbol of an instance.
"""

class RectangleMove():
    def __init__(self, event,
                 window, #      : schematic_window.SchematicWindow,
                 diagram_tab, # : notebook_diagram_tab.NotebookDiagramTab,
                 parent,
                 symbol_definition
                 ):
        self.window            = window
        self.diagram_tab       = diagram_tab
        self.symbol_definition = symbol_definition
        self.event_x           = self.diagram_tab.canvas.canvasx(event.x)
        self.event_y           = self.diagram_tab.canvas.canvasy(event.y)
        self.rectangle_canvas_id = self.symbol_definition["rectangle"]["canvas_id"]
        self.rectangle_coords    = self.diagram_tab.canvas.coords(self.rectangle_canvas_id)
        dictionary_of_symbol_items_to_move = self.__create_dictionary_of_symbol_items_to_move(self.rectangle_coords)
        touching_point                     = self.__get_touching_point(self.rectangle_coords)
        minimal_rectangle                  = self.__get_minimal_rectangle(dictionary_of_symbol_items_to_move, touching_point, self.rectangle_coords)
        delta_mask_dict                    = self.__get_delta_mask_dict(touching_point)
        references_to_connected_wires      = self.__get_references_to_connected_wires(self.rectangle_coords)
        self.func_id_motion         = self.diagram_tab.canvas.tag_bind(self.symbol_definition["object_tag"], "<Motion>",
                                                                       lambda event : self.__move_by_motion(event, minimal_rectangle,
                                                                            dictionary_of_symbol_items_to_move, delta_mask_dict, references_to_connected_wires))
        self.func_id_button_release = self.diagram_tab.canvas.tag_bind(self.symbol_definition["object_tag"], "<ButtonRelease-1>",
                                                                       lambda event : self.__move_end(parent, touching_point, minimal_rectangle,
                                                                            dictionary_of_symbol_items_to_move, delta_mask_dict, references_to_connected_wires))

    def __create_dictionary_of_symbol_items_to_move(self, rectangle_coords):
        dictionary_of_symbol_items_to_move = {}
        dictionary_of_symbol_items_to_move["polygons_left"  ] = []
        dictionary_of_symbol_items_to_move["polygons_top"   ] = []
        dictionary_of_symbol_items_to_move["polygons_right" ] = []
        dictionary_of_symbol_items_to_move["polygons_bottom"] = []
        dictionary_of_symbol_items_to_move["text_left"      ] = []
        dictionary_of_symbol_items_to_move["text_top"       ] = []
        dictionary_of_symbol_items_to_move["text_right"     ] = []
        dictionary_of_symbol_items_to_move["text_bottom"    ] = []
        dictionary_of_symbol_items_to_move["generic_map"    ] = []
        dictionary_of_symbol_items_to_move["entity_name"    ] = []
        dictionary_of_symbol_items_to_move["instance_name"  ] = []
        dictionary_of_symbol_items_to_move["others"         ] = []
        canvas_ids = self.diagram_tab.canvas.find_withtag(self.symbol_definition["object_tag"])
        for canvas_id in canvas_ids:
            canvas_type = self.diagram_tab.canvas.type(canvas_id)
            if canvas_type=="polygon":
                polygon_coords = self.diagram_tab.canvas.coords(canvas_id)
                if   polygon_coords[0]<=rectangle_coords[0]:
                    dictionary_of_symbol_items_to_move["polygons_left"  ].append(canvas_id)
                elif polygon_coords[1]<=rectangle_coords[1]:
                    dictionary_of_symbol_items_to_move["polygons_top"   ].append(canvas_id)
                elif polygon_coords[0]>=rectangle_coords[2]:
                    dictionary_of_symbol_items_to_move["polygons_right" ].append(canvas_id)
                elif polygon_coords[1]>=rectangle_coords[3]:
                    dictionary_of_symbol_items_to_move["polygons_bottom"].append(canvas_id)
            elif canvas_type=="text":
                if "generic-map" in self.diagram_tab.canvas.gettags(canvas_id):
                    dictionary_of_symbol_items_to_move["generic_map"].append(canvas_id)
                elif (self.diagram_tab.canvas.itemcget(canvas_id, "text").startswith(self.symbol_definition["entity_name"]["name"]+'.') or # VHDL
                      self.diagram_tab.canvas.itemcget(canvas_id, "text")==self.symbol_definition["entity_name"]["name"]):                 # Verilog
                    dictionary_of_symbol_items_to_move["entity_name"].append(canvas_id)
                elif self.symbol_definition["instance_name"]["name"]==self.diagram_tab.canvas.itemcget(canvas_id, "text"):
                    dictionary_of_symbol_items_to_move["instance_name"].append(canvas_id)
                else:
                    anchor = self.diagram_tab.canvas.itemcget(canvas_id, "anchor")
                    angle  = self.diagram_tab.canvas.itemcget(canvas_id, "angle" )
                    if   float(angle)==0.0 and anchor=="w":
                        dictionary_of_symbol_items_to_move["text_left"  ].append(canvas_id)
                    elif float(angle)==0.0 and anchor=="e":
                        dictionary_of_symbol_items_to_move["text_right" ].append(canvas_id)
                    elif float(angle)==270.0: # and anchor=="e":
                        dictionary_of_symbol_items_to_move["text_bottom"].append(canvas_id)
                    elif float(angle)==90.0: # and anchor=="e":
                        dictionary_of_symbol_items_to_move["text_top"   ].append(canvas_id)
            elif canvas_type=="rectangle":
                pass
            else:
                dictionary_of_symbol_items_to_move["others"].append(canvas_id)
        return dictionary_of_symbol_items_to_move

    def __get_touching_point(self, rectangle_coords):
        distance = 10
        if (self.event_x<rectangle_coords[0] + distance and
            self.event_y<rectangle_coords[1] + distance):
            return "top_left"
        if (self.event_x>rectangle_coords[2] - distance and
            self.event_y<rectangle_coords[1] + distance):
            return "top_right"
        if (self.event_x<rectangle_coords[0] + distance and
            self.event_y>rectangle_coords[3] - distance):
            return "bottom_left"
        if (self.event_x>rectangle_coords[2] - distance and
            self.event_y>rectangle_coords[3] - distance):
            return "bottom_right"
        return "middle"

    def __get_minimal_rectangle(self, dictionary_of_symbol_items_to_move, touching_point, rectangle_coords):
        minimal_rectangle = [0, 0, 0, 0]
        # Create a minimal rectangle for a symbol without any ports,
        # to which the the symbol can be shrinked, when a specific corner is moved:
        if   touching_point=="top_left":
            minimal_rectangle[0] = rectangle_coords[2] - self.window.design.get_grid_size()
            minimal_rectangle[1] = rectangle_coords[3] - self.window.design.get_grid_size()
            minimal_rectangle[2] = rectangle_coords[2]
            minimal_rectangle[3] = rectangle_coords[3]
        elif touching_point=="top_right":
            minimal_rectangle[0] = rectangle_coords[0]
            minimal_rectangle[1] = rectangle_coords[3] - self.window.design.get_grid_size()
            minimal_rectangle[2] = rectangle_coords[0] + self.window.design.get_grid_size()
            minimal_rectangle[3] = rectangle_coords[3]
        elif touching_point=="bottom_right":
            minimal_rectangle[0] = rectangle_coords[0]
            minimal_rectangle[1] = rectangle_coords[1]
            minimal_rectangle[2] = rectangle_coords[0] + self.window.design.get_grid_size()
            minimal_rectangle[3] = rectangle_coords[1] + self.window.design.get_grid_size()
        elif touching_point=="bottom_left":
            minimal_rectangle[0] = rectangle_coords[2] - self.window.design.get_grid_size()
            minimal_rectangle[1] = rectangle_coords[1]
            minimal_rectangle[2] = rectangle_coords[2]
            minimal_rectangle[3] = rectangle_coords[1] + self.window.design.get_grid_size()
        # Increase the minimal rectangle when ports exist and are positioned outside it:
        for kind in dictionary_of_symbol_items_to_move:
            if kind in ["polygons_left", "polygons_right"]:
                canvas_id_list = dictionary_of_symbol_items_to_move[kind]
                for canvas_id in canvas_id_list: # self.diagram_tab.canvas.coords(canvas_id)[0:2] is the polygon connection-point lying at the grid.
                    if self.diagram_tab.canvas.coords(canvas_id)[1]<minimal_rectangle[1] + 0.5 * self.window.design.get_grid_size():
                        minimal_rectangle[1] = self.diagram_tab.canvas.coords(canvas_id)[1] - 0.5 * self.window.design.get_grid_size()
                    if self.diagram_tab.canvas.coords(canvas_id)[1]>minimal_rectangle[3] - 0.5 * self.window.design.get_grid_size():
                        minimal_rectangle[3] = self.diagram_tab.canvas.coords(canvas_id)[1] + 0.5 * self.window.design.get_grid_size()
        for kind in dictionary_of_symbol_items_to_move:
            if kind in ["polygons_top", "polygons_bottom"]:
                canvas_id_list = dictionary_of_symbol_items_to_move[kind]
                for canvas_id in canvas_id_list: # self.diagram_tab.canvas.coords(canvas_id)[0:2] is the polygon connection-point lying at the grid.
                    if self.diagram_tab.canvas.coords(canvas_id)[0]<minimal_rectangle[0] - 0.5 * self.window.design.get_grid_size():
                        minimal_rectangle[0] = self.diagram_tab.canvas.coords(canvas_id)[0] + 0.5 * self.window.design.get_grid_size()
                    if self.diagram_tab.canvas.coords(canvas_id)[0]>minimal_rectangle[2] + 0.5 * self.window.design.get_grid_size():
                        minimal_rectangle[2] = self.diagram_tab.canvas.coords(canvas_id)[0] - 0.5 * self.window.design.get_grid_size()
        return minimal_rectangle
    def __get_delta_mask_dict(self, touching_point):
        delta_mask_dict = {}
        if touching_point=="top_left":
            delta_mask_dict["rectangle"      ] = [1, 1, 0, 0]
            delta_mask_dict["polygons_left"  ] = [1, 0]
            delta_mask_dict["polygons_top"   ] = [0, 1]
            delta_mask_dict["polygons_right" ] = [0, 0]
            delta_mask_dict["polygons_bottom"] = [0, 0]
            delta_mask_dict["text_left"      ] = [1, 0]
            delta_mask_dict["text_top"       ] = [0, 1]
            delta_mask_dict["text_right"     ] = [0, 0]
            delta_mask_dict["text_bottom"    ] = [0, 0]
            delta_mask_dict["generic_map"    ] = [1, 1]
            delta_mask_dict["entity_name"    ] = [1, 0]
            delta_mask_dict["instance_name"  ] = [1, 0]
            delta_mask_dict["others"         ] = [0, 0]
            return delta_mask_dict
        if touching_point=="top_right":
            delta_mask_dict["rectangle"      ] = [0, 1, 1, 0]
            delta_mask_dict["polygons_left"  ] = [0, 0]
            delta_mask_dict["polygons_top"   ] = [0, 1]
            delta_mask_dict["polygons_right" ] = [1, 0]
            delta_mask_dict["polygons_bottom"] = [0, 0]
            delta_mask_dict["text_left"      ] = [0, 0]
            delta_mask_dict["text_top"       ] = [0, 1]
            delta_mask_dict["text_right"     ] = [1, 0]
            delta_mask_dict["text_bottom"    ] = [0, 0]
            delta_mask_dict["generic_map"    ] = [0, 1]
            delta_mask_dict["entity_name"    ] = [0, 0]
            delta_mask_dict["instance_name"  ] = [0, 0]
            delta_mask_dict["others"         ] = [0, 0]
            return delta_mask_dict
        if touching_point=="bottom_left":
            delta_mask_dict["rectangle"      ] = [1, 0, 0, 1]
            delta_mask_dict["polygons_left"  ] = [1, 0]
            delta_mask_dict["polygons_top"   ] = [0, 0]
            delta_mask_dict["polygons_right" ] = [0, 0]
            delta_mask_dict["polygons_bottom"] = [0, 1]
            delta_mask_dict["text_left"      ] = [1, 0]
            delta_mask_dict["text_top"       ] = [0, 0]
            delta_mask_dict["text_right"     ] = [0, 0]
            delta_mask_dict["text_bottom"    ] = [0, 1]
            delta_mask_dict["generic_map"    ] = [1, 0]
            delta_mask_dict["entity_name"    ] = [1, 1]
            delta_mask_dict["instance_name"  ] = [1, 1]
            delta_mask_dict["others"         ] = [0, 0]
            return delta_mask_dict
        if touching_point=="bottom_right":
            delta_mask_dict["rectangle"      ] = [0, 0, 1, 1]
            delta_mask_dict["polygons_left"  ] = [0, 0]
            delta_mask_dict["polygons_top"   ] = [0, 0]
            delta_mask_dict["polygons_right" ] = [1, 0]
            delta_mask_dict["polygons_bottom"] = [0, 1]
            delta_mask_dict["text_left"      ] = [0, 0]
            delta_mask_dict["text_top"       ] = [0, 0]
            delta_mask_dict["text_right"     ] = [1, 0]
            delta_mask_dict["text_bottom"    ] = [0, 1]
            delta_mask_dict["generic_map"    ] = [0, 0]
            delta_mask_dict["entity_name"    ] = [0, 1]
            delta_mask_dict["instance_name"  ] = [0, 1]
            delta_mask_dict["others"         ] = [0, 0]
            return delta_mask_dict
        # touching_point=="middle"
        delta_mask_dict["rectangle"      ] = [1, 1, 1, 1]
        delta_mask_dict["polygons_left"  ] = [1, 1]
        delta_mask_dict["polygons_top"   ] = [1, 1]
        delta_mask_dict["polygons_right" ] = [1, 1]
        delta_mask_dict["polygons_bottom"] = [1, 1]
        delta_mask_dict["text_left"      ] = [1, 1]
        delta_mask_dict["text_top"       ] = [1, 1]
        delta_mask_dict["text_right"     ] = [1, 1]
        delta_mask_dict["text_bottom"    ] = [1, 1]
        delta_mask_dict["generic_map"    ] = [1, 1]
        delta_mask_dict["others"         ] = [1, 1]
        delta_mask_dict["entity_name"    ] = [1, 1]
        delta_mask_dict["instance_name"  ] = [1, 1]
        return delta_mask_dict

    def __get_references_to_connected_wires(self, rectangle_coords):
        references_to_connected_wires = {}
        references_to_connected_wires["left"  ] = []
        references_to_connected_wires["top"   ] = []
        references_to_connected_wires["right" ] = []
        references_to_connected_wires["bottom"] = []
         # A line can overlap several times with the ports of a symbol:
         # The line start point can be connected to a port.
         # The line end point can be connected to a port
         # It is possible that both line start and line end point are connected to a port.
        list_of_overlapping_line_points_dict = self.__get_canvas_ids_of_lines_which_overlap_polygons_at_start_or_end()
        for line_points_dict in list_of_overlapping_line_points_dict:
            canvas_id   = line_points_dict["canvas_id"]
            moved_point = line_points_dict["point"]
            line_coords            = self.diagram_tab.canvas.coords(canvas_id)
            if moved_point=="first":
                touching_line_coords = line_coords[0:2]
            else: # moved_point=="last"
                touching_line_coords = line_coords[-2:]
            if touching_line_coords[0]<rectangle_coords[0]:
                references_to_connected_wires["left"  ].append([self.diagram_tab.design.get_references([canvas_id])[0], moved_point])
            if touching_line_coords[0]>rectangle_coords[2]:
                references_to_connected_wires["right" ].append([self.diagram_tab.design.get_references([canvas_id])[0], moved_point])
            if touching_line_coords[1]<rectangle_coords[1]:
                references_to_connected_wires["top"   ].append([self.diagram_tab.design.get_references([canvas_id])[0], moved_point])
            if touching_line_coords[1]>rectangle_coords[3]:
                references_to_connected_wires["bottom"].append([self.diagram_tab.design.get_references([canvas_id])[0], moved_point])
        return references_to_connected_wires

    def __get_canvas_ids_of_lines_which_overlap_polygons_at_start_or_end(self):
        list_overlapping = []
        canvas_ids = self.diagram_tab.canvas.find_withtag(self.symbol_definition["object_tag"])
        for canvas_id in canvas_ids:
            if self.diagram_tab.canvas.type(canvas_id)=="polygon":
                bbox = list(self.diagram_tab.canvas.bbox(canvas_id))
                # Das Vergrößern hatte zur Folge, dass einem Wire 2 Polygons zugeordnet wurde, deshalb entfernt.
                # bbox[0] = bbox[0] - self.diagram_tab.design.get_grid_size()/10 # 2
                # bbox[1] = bbox[1] - self.diagram_tab.design.get_grid_size()/10 # 2
                # bbox[2] = bbox[2] + self.diagram_tab.design.get_grid_size()/10 # 2
                # bbox[3] = bbox[3] + self.diagram_tab.design.get_grid_size()/10 # 2
                #print("polygon blackbox 2=", bbox)
                pin_overlappings = self.diagram_tab.canvas.find_overlapping(*bbox)
                for pin_overlapping in pin_overlappings:
                    if self.diagram_tab.canvas.type(pin_overlapping)=="line" and "grid_line" not in self.diagram_tab.canvas.gettags(pin_overlapping):
                        line_coords = self.diagram_tab.canvas.coords(pin_overlapping)
                        if self.__check_if_line_start_touches(bbox, line_coords):
                            list_overlapping.append({"canvas_id": pin_overlapping, "point": "first"})
                        if self.__check_if_line_end_touches(bbox, line_coords):
                            list_overlapping.append({"canvas_id": pin_overlapping, "point": "last"})
        return list_overlapping

    def __check_if_line_start_touches(self, bbox, line_coords):
        if (bbox[0]<line_coords[0]<bbox[2] and bbox[1]<line_coords[1]<bbox[3]):
            return True
        return False

    def __check_if_line_end_touches(self, bbox, line_coords):
        if (bbox[0]<line_coords[-2]<bbox[2] and bbox[1]<line_coords[-1]<bbox[3]):
            return True
        return False

    def __move_by_motion(self, event, minimal_rectangle, dictionary_of_symbol_items_to_move, delta_mask_dict, references_to_connected_wires):
        new_event_x = self.diagram_tab.canvas.canvasx(event.x)
        new_event_y = self.diagram_tab.canvas.canvasy(event.y)
        delta_x = new_event_x-self.event_x
        delta_y = new_event_y-self.event_y
        if delta_x!=0.0 or delta_y!=0.0:
            self.__move(minimal_rectangle, delta_mask_dict, dictionary_of_symbol_items_to_move, references_to_connected_wires, delta_x, delta_y, "not move end")
            self.event_x = new_event_x
            self.event_y = new_event_y

    def __move(self, minimal_rectangle, delta_mask_dict, dictionary_of_symbol_items_to_move, references_to_connected_wires, delta_x, delta_y, movement_phase):
        if delta_mask_dict["rectangle"]==[1, 1, 1, 1]:
            self.diagram_tab.canvas.move(self.symbol_definition["rectangle"]["canvas_id"], delta_x, delta_y)
            rectangle_was_moved = True
        else:
            rectangle_delta = [delta_x, delta_y, delta_x, delta_y]
            coords = self.diagram_tab.canvas.coords(self.symbol_definition["rectangle"]["canvas_id"])
            new_coords = [0, 0, 0, 0]
            for index, coord in enumerate(coords):
                new_coords[index] = coord + rectangle_delta[index]*delta_mask_dict["rectangle"][index]
            if self.__new_rectangle_is_bigger_minimum(new_coords, minimal_rectangle, delta_mask_dict):
                self.diagram_tab.canvas.coords(self.symbol_definition["rectangle"]["canvas_id"], new_coords)
                rectangle_was_moved = True
            else:
                rectangle_was_moved = False
        if rectangle_was_moved:
            for rectangle_add_on in dictionary_of_symbol_items_to_move:
                for canvas_id in dictionary_of_symbol_items_to_move[rectangle_add_on]:
                    self.diagram_tab.canvas.move(canvas_id, delta_x*delta_mask_dict[rectangle_add_on][0], delta_y*delta_mask_dict[rectangle_add_on][1])
            for rectangle_side in references_to_connected_wires:
                if rectangle_side=="left":
                    delta_mask_x = delta_mask_dict["polygons_left"  ][0]
                    delta_mask_y = delta_mask_dict["polygons_left"  ][1]
                elif rectangle_side=="top":
                    delta_mask_x = delta_mask_dict["polygons_top"   ][0]
                    delta_mask_y = delta_mask_dict["polygons_top"   ][1]
                elif rectangle_side=="right":
                    delta_mask_x = delta_mask_dict["polygons_right" ][0]
                    delta_mask_y = delta_mask_dict["polygons_right" ][1]
                else:
                    delta_mask_x = delta_mask_dict["polygons_bottom"][0]
                    delta_mask_y = delta_mask_dict["polygons_bottom"][1]
                for entry in references_to_connected_wires[rectangle_side]:
                    wire_reference     = entry[0]
                    wire_point_to_move = entry[1]
                    wire_reference.move_wire_end_point(movement_phase, wire_point_to_move, delta_x*delta_mask_x, delta_y*delta_mask_y)

    def __new_rectangle_is_bigger_minimum(self, new_coords, minimal_rectangle, delta_mask_dict):
        # The fixed coordinates of the minimal_rectangle might not have exact the same values as the fixed coordinates of the
        # rectangle of the symbol due to small discrepancies.
        # Therefore the fixed coordinates can create wrong comparison results and must be masked here:
        if ((new_coords[0]<=minimal_rectangle[0] or delta_mask_dict["rectangle"][0]==0)and
            (new_coords[1]<=minimal_rectangle[1] or delta_mask_dict["rectangle"][1]==0) and
            (new_coords[2]>=minimal_rectangle[2] or delta_mask_dict["rectangle"][2]==0) and
            (new_coords[3]>=minimal_rectangle[3] or delta_mask_dict["rectangle"][3]==0)):
            return True
        return False

    def __move_end(self, parent, touching_point, minimal_rectangle, dictionary_of_symbol_items_to_move, delta_mask_dict, references_to_connected_wires):
        self.diagram_tab.canvas.tag_unbind(self.symbol_definition["object_tag"], "<Motion>"         , self.func_id_motion)
        self.diagram_tab.canvas.tag_unbind(self.symbol_definition["object_tag"], "<ButtonRelease-1>", self.func_id_button_release)
        self.func_id_motion = None
        self.func_id_button_release = None
        self.__move_to_grid(parent, touching_point, minimal_rectangle, dictionary_of_symbol_items_to_move, delta_mask_dict, references_to_connected_wires)

    def __move_to_grid(self, parent, touching_point, minimal_rectangle, dictionary_of_symbol_items_to_move, delta_mask_dict, references_to_connected_wires):
        delta_x, delta_y = self.__get_delta_to_grid(touching_point)
        # Very small deltas are created by inaccuracies and should not lead to a "move":
        if abs(delta_x)>0.1 or abs(delta_y)>0.1: # Smaller deltas shall not be executed, because they would signal a design change.
            self.__move(minimal_rectangle, delta_mask_dict, dictionary_of_symbol_items_to_move, references_to_connected_wires, delta_x, delta_y, "last_time")
            new_rectangle_coords  = self.diagram_tab.canvas.coords(self.rectangle_canvas_id)
            if new_rectangle_coords!=self.rectangle_coords:
                parent.store_item(push_design_to_stack=True, signal_design_change=True)

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
