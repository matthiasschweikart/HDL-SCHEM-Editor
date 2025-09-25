"""
Parent class for the insertion of all polygon symbols
"""

class InterfaceInsertion():
    def __init__(self,
                 window,      # : schematic_window.SchematicWindow,
                 diagram_tab, # : notebook_diagram_tab.NotebookDiagramTab,
                 points, follow_mouse):
        self.window                  = window
        self.diagram_tab             = diagram_tab
        self.orientation             = 0
        self.event_x                 = 0
        self.event_y                 = 0
        self.canvas_id               = 0
        self.funcid_delete           = None
        self.func_id_motion          = None
        self.func_id_button          = None
        self.func_id_leave           = None
        self.func_id_escape          = None
        self.func_id_button_release  = None
        self.sym_bind_funcid_button  = None
        self.sym_bind_funcid_dbutton = None
        self.sym_bind_funcid_rbutton = None
        self.sym_bind_funcid_enter   = None
        self.sym_bind_funcid_leave   = None
        self.type                    = "" # Will be overwritten by the child class.
        self.symbol_coords           = []
        if follow_mouse:
            self.diagram_tab.remove_canvas_bindings()
            self.__create_bindings_for_interface_insertion_at_canvas(points)
            self.window.config(cursor="cross")

    def __draw_symbol_once_at_event_location(self, event, points):
        self.event_x = self.diagram_tab.canvas.canvasx(event.x)
        self.event_y = self.diagram_tab.canvas.canvasy(event.y)
        self.__draw(self.event_x, self.event_y, points)
        references_to_connected_wires = []
        self.func_id_motion = self.diagram_tab.canvas.bind("<Motion>"  , lambda event: self.__move_to(event, references_to_connected_wires))

    def __draw(self, location_x, location_y, points):
        points_moved = self.__move_polygon_points_from_origin_to_location(location_x, location_y, points)
        self.canvas_id = self.diagram_tab.canvas.create_polygon(points_moved, fill="violet", activefill="red", outline="black",
                                                                tags=("layer2", "schematic-element"))
        self.diagram_tab.sort_layers()

    def __move_polygon_points_from_origin_to_location(self, location_x, location_y, points):
        for point in points:
            point[0] += location_x
            point[1] += location_y
        return points

    def __end_inserting(self, event, points):
        new_event_x = self.diagram_tab.canvas.canvasx(event.x, gridspacing=self.window.design.get_grid_size())
        new_event_y = self.diagram_tab.canvas.canvasy(event.y, gridspacing=self.window.design.get_grid_size())
        self.diagram_tab.canvas.move(self.canvas_id,new_event_x-self.event_x, new_event_y-self.event_y)
        self.__add_bindings_to_symbol()
        self.__restore_diagram_tab_canvas_bindings_after_inserting()
        self.store_item(push_design_to_stack=True, signal_design_change=True)
        # Create a new connector, so that the user can directly proceed (for example with the next input connector; type(self) is the class name):
        type(self)(self.window, self.diagram_tab, points, follow_mouse=True)

    def __reject_symbol(self):
        self.__restore_diagram_tab_canvas_bindings_after_inserting()
        self.diagram_tab.canvas.focus_set() # needed to catch Ctrl-z
        self.diagram_tab.canvas.delete(self.canvas_id)
        self.window.config(cursor="arrow")
        del self # Once the last reference to an object is deleted, the object will be removed by garbage collection.

    def __restore_diagram_tab_canvas_bindings_after_inserting(self):
        self.__remove_interface_insertion_bindings_from_canvas()
        self.diagram_tab.create_canvas_bindings()

    def __rotate_after_idle(self):
        # "After" got necessary because ButtonRelease-3 is bound to 2 actions:
        #   __zoom_area (in notebook_diagram_tab, not only used for zoom but also for the drawing-area-background-menu)
        #   self.__rotate
        # If __zoom_area detects a zoom-rectangle with size 0, the background-menu is opened (workaround to have zoom and background-menu both at Button-3).
        # The background-menu will only be drawn if the mouse pointer is not over any other object.
        # So when a connector is rotated by Button-3 no background-menu should show, as the mouse-pointer is over the connector.
        # But as (for unknown reasons) always first the connector is rotated and disappears from the mouse-pointer,
        # afterwards always the background-menu showed.
        # By using "after" now first the button3 event __zoom_area is handled and as the connector is not rotated yet,
        # it is still under the mouse-pointer and no background-menu pops up.
        # Then after idle the connector is rotated.
        self.diagram_tab.canvas.after_idle(self.__rotate)

    def __rotate(self, by_mouse):
        coords = self.diagram_tab.canvas.coords(self.canvas_id)
        for index in range(len(coords)//2-1):
            delta_x_from_anchor_to_corner = - coords[0] + coords[2 + 2*index    ]
            delta_y_from_anchor_to_corner = - coords[1] + coords[2 + 2*index + 1]
            coords[2 + 2*index    ] = coords[0] - delta_y_from_anchor_to_corner
            coords[2 + 2*index + 1] = coords[1] + delta_x_from_anchor_to_corner
        self.diagram_tab.canvas.coords(self.canvas_id, coords)
        self.orientation = (self.orientation + 1) % 4
        self.store_item(push_design_to_stack=by_mouse, signal_design_change=by_mouse)

    def __move_start(self, event):
        self.event_x = self.diagram_tab.canvas.canvasx(event.x)
        self.event_y = self.diagram_tab.canvas.canvasy(event.y)
        self.symbol_coords = self.diagram_tab.canvas.coords(self.canvas_id)
        list_overlapping_at_any_place = self.diagram_tab.canvas.find_overlapping(self.symbol_coords[0]-0.1*self.window.design.get_grid_size(),
                                                                                 self.symbol_coords[1]-0.1*self.window.design.get_grid_size(),
                                                                                 self.symbol_coords[0]+0.1*self.window.design.get_grid_size(),
                                                                                 self.symbol_coords[1]+0.1*self.window.design.get_grid_size())
        list_overlapping = []
        for canvas_id in list_overlapping_at_any_place:
            if self.diagram_tab.canvas.type(canvas_id)=="line" and "grid_line" not in self.diagram_tab.canvas.gettags(canvas_id):
                line_coords = self.diagram_tab.canvas.coords(canvas_id)
                if ((line_coords[ 0]>=self.symbol_coords[0]-0.1*self.window.design.get_grid_size() and
                     line_coords[ 0]<=self.symbol_coords[0]+0.1*self.window.design.get_grid_size() and
                     line_coords[ 1]>=self.symbol_coords[1]-0.1*self.window.design.get_grid_size() and
                     line_coords[ 1]<=self.symbol_coords[1]+0.1*self.window.design.get_grid_size())
                    or
                    (line_coords[-2]>=self.symbol_coords[0]-0.1*self.window.design.get_grid_size() and
                     line_coords[-2]<=self.symbol_coords[0]+0.1*self.window.design.get_grid_size() and
                     line_coords[-1]>=self.symbol_coords[1]-0.1*self.window.design.get_grid_size() and
                     line_coords[-1]<=self.symbol_coords[1]+0.1*self.window.design.get_grid_size())):
                    list_overlapping.append(canvas_id)
        references_to_connected_wires = self.__get_references_to_connected_wires(self.symbol_coords, list_overlapping)
        self.func_id_motion         = self.diagram_tab.canvas.tag_bind(self.canvas_id, "<Motion>"         , lambda event : self.__move_to (event, references_to_connected_wires))
        self.func_id_button_release = self.diagram_tab.canvas.tag_bind(self.canvas_id, "<ButtonRelease-1>", lambda event : self.__move_end(references_to_connected_wires))

    def __get_references_to_connected_wires(self, symbol_coords, list_overlapping):
        references_to_connected_wires = []
        for canvas_id in list_overlapping:
            if self.diagram_tab.canvas.type(canvas_id)=="line" and "grid_line" not in self.diagram_tab.canvas.gettags(canvas_id):
                line_coords = self.diagram_tab.canvas.coords(canvas_id)
                if self.__first_line_point_touches_symbol_anchor(line_coords[0:2], symbol_coords[0:2]):
                    moved_point = "first"
                else:
                    moved_point = "last"
                references_to_connected_wires.append((self.diagram_tab.design.get_references([canvas_id])[0], moved_point))
        return references_to_connected_wires

    def __first_line_point_touches_symbol_anchor(self, first_line_point, symbol_anchor):
        if symbol_anchor[0]-1<=first_line_point[0]<=symbol_anchor[0]+1 and symbol_anchor[1]-1<=first_line_point[1]<=symbol_anchor[1]+1:
            return True
        return False

    def __move_to(self, event, references_to_connected_wires):
        new_event_x = self.diagram_tab.canvas.canvasx(event.x)
        new_event_y = self.diagram_tab.canvas.canvasy(event.y)
        self.diagram_tab.canvas.move(self.canvas_id, new_event_x-self.event_x, new_event_y-self.event_y)
        for reference in references_to_connected_wires:
            reference_to_wire = reference[0]
            moved_point       = reference[1] # first or "last"
            reference_to_wire.move_wire_end_point("not move end", moved_point, new_event_x-self.event_x, new_event_y-self.event_y)
        self.event_x = new_event_x
        self.event_y = new_event_y

    def __move_end(self, references_to_connected_wires):
        self.diagram_tab.canvas.tag_unbind(self.canvas_id, "<Motion>"         , self.func_id_motion)
        self.diagram_tab.canvas.tag_unbind(self.canvas_id, "<ButtonRelease-1>", self.func_id_button_release)
        self.func_id_motion = None
        self.func_id_button_release = None
        self.__move_to_grid(references_to_connected_wires)
        self.__unhighlight()
        new_symbol_coords = self.diagram_tab.canvas.coords(self.canvas_id)
        if new_symbol_coords!=self.symbol_coords:
            self.store_item(push_design_to_stack=True, signal_design_change=True)

    def __move_to_grid(self, references_to_connected_wires):
        # Determine the distance of the anchor point of the symbol to the grid:
        anchor_x, anchor_y = self.diagram_tab.canvas.coords(self.canvas_id)[0:2]
        remainder_x = anchor_x % self.window.design.get_grid_size()
        remainder_y = anchor_y % self.window.design.get_grid_size()
        # Move the symbol to the grid:
        delta_x = - remainder_x
        delta_y = - remainder_y
        if remainder_x>self.window.design.get_grid_size()/2:
            delta_x += self.window.design.get_grid_size()
        if remainder_y>self.window.design.get_grid_size()/2:
            delta_y += self.window.design.get_grid_size()
        self.diagram_tab.canvas.move(self.canvas_id, delta_x, delta_y)
        for reference in references_to_connected_wires:
            reference_to_wire = reference[0]
            moved_point       = reference[1] # first or "last"
            reference_to_wire.move_wire_end_point("last_time", moved_point, delta_x, delta_y)

    def select_item(self):
        self.__highlight()
        self.__remove_bindings_from_symbol()

    def unselect_item(self):
        self.__unhighlight()
        self.__add_bindings_to_symbol()

    def __highlight(self):
        self.diagram_tab.canvas.itemconfigure(self.canvas_id, fill="red") #, outline="black")

    def __unhighlight(self):
        self.diagram_tab.canvas.itemconfigure(self.canvas_id, fill="violet") #, outline="")

    def draw_at_location(self, location, orientation, points):
        self.__draw(*location, points)
        for _ in range(orientation):
            self.__rotate(by_mouse=False)
        self.__add_bindings_to_symbol()
        self.store_item(push_design_to_stack=False, signal_design_change=False)

    def __add_bindings_to_symbol(self):
        self.sym_bind_funcid_button  = self.diagram_tab.canvas.tag_bind(self.canvas_id, "<Button-1>"       , self.__move_start              )
        self.sym_bind_funcid_dbutton = self.diagram_tab.canvas.tag_bind(self.canvas_id, "<Double-Button-1>", lambda event: self.__rotate(by_mouse=True)  )
        self.sym_bind_funcid_rbutton = self.diagram_tab.canvas.tag_bind(self.canvas_id, "<ButtonRelease-3>", lambda event: self.__rotate_after_idle()  )
        self.sym_bind_funcid_enter   = self.diagram_tab.canvas.tag_bind(self.canvas_id, "<Enter>"          , lambda event: self.__at_enter())
        self.sym_bind_funcid_leave   = self.diagram_tab.canvas.tag_bind(self.canvas_id, "<Leave>"          , lambda event: self.__at_leave())

    def __remove_bindings_from_symbol(self):
        self.diagram_tab.canvas.tag_unbind(self.canvas_id,"<Button-1>"       , self.sym_bind_funcid_button)
        self.diagram_tab.canvas.tag_unbind(self.canvas_id,"<Double-Button-1>", self.sym_bind_funcid_dbutton)
        self.diagram_tab.canvas.tag_unbind(self.canvas_id,"<ButtonRelease-3>", self.sym_bind_funcid_rbutton)
        self.diagram_tab.canvas.tag_unbind(self.canvas_id,"<Enter>"          , self.sym_bind_funcid_enter)
        self.diagram_tab.canvas.tag_unbind(self.canvas_id,"<Leave>"          , self.sym_bind_funcid_leave)
        self.sym_bind_funcid_button  = None
        self.sym_bind_funcid_dbutton = None
        self.sym_bind_funcid_rbutton = None
        self.sym_bind_funcid_enter   = None
        self.sym_bind_funcid_leave   = None

    def __create_bindings_for_interface_insertion_at_canvas(self, points):
        self.func_id_motion = self.diagram_tab.canvas.bind("<Motion>"  , lambda event: self.__draw_symbol_once_at_event_location(event, points))
        self.func_id_button = self.diagram_tab.canvas.bind("<Button-1>", lambda event: self.__end_inserting(event, points))
        self.func_id_leave  = self.diagram_tab.canvas.bind("<Leave>"   , lambda event: self.__reject_symbol())
        self.func_id_escape = self.window.bind            ("<Escape>"  , lambda event: self.__reject_symbol())

    def __remove_interface_insertion_bindings_from_canvas(self):
        self.diagram_tab.canvas.unbind ("<Motion>"  , self.func_id_motion)
        self.diagram_tab.canvas.unbind ("<Button-1>", self.func_id_button)
        self.diagram_tab.canvas.unbind ("<Leave>"   , self.func_id_leave )
        self.window.unbind             ("<Escape>"  , self.func_id_escape)
        self.func_id_motion = None
        self.func_id_button = None
        self.func_id_leave  = None
        self.func_id_escape = None

    def __at_enter(self):
        if not self.diagram_tab.canvas.find_withtag("selected"):
            self.diagram_tab.canvas.focus_set()
            self.funcid_delete = self.diagram_tab.canvas.bind("<Delete>", lambda event: self.delete_item(push_design_to_stack=True))

    def __at_leave(self):
        self.__restore_delete_binding()

    def __restore_delete_binding(self):
        if self.funcid_delete is not None: # Check is needed, because sometimes a select-rectangle and the delete-binding both perform a delete.
            self.diagram_tab.canvas.unbind("<Delete>", self.funcid_delete)
            self.funcid_delete = None
            self.diagram_tab.canvas.bind("<Delete>", lambda event: self.diagram_tab.delete_selection())

    def delete_item(self, push_design_to_stack):
        self.__restore_delete_binding()
        self.window.design.remove_canvas_item_from_dictionary(self.canvas_id, push_design_to_stack)
        self.diagram_tab.canvas.delete(self.canvas_id)
        self.diagram_tab.create_canvas_bindings() # Needed because when "self" is deleted after entering the symbol, no __at_leave will take place.
        del self # Once the last reference to an object is deleted, the object will be removed by garbage collection.

    def store_item(self, push_design_to_stack, signal_design_change):
        coords = self.diagram_tab.canvas.coords(self.canvas_id)
        self.window.design.store_interface_in_canvas_dictionary(self.canvas_id, self, self.type,
                                                             coords[0:2], self.orientation, push_design_to_stack, signal_design_change)

    def get_object_tag(self):
        return self.canvas_id

    def add_pasted_tag_to_all_canvas_items(self):
        self.diagram_tab.canvas.addtag_withtag("pasted_tag", self.canvas_id)

    def adapt_coordinates_by_factor(self, factor):
        coords = self.diagram_tab.canvas.coords(self.canvas_id)
        delta_x_list = []
        delta_y_list = []
        for index, coord in enumerate(coords):
            if index%2==0: # x-coordinates
                if index==0:
                    delta_x_list.append(0)
                else:
                    delta_x_list.append(coord-coords[0])
            else: # y-coordinates
                if index==1:
                    delta_y_list.append(0)
                else:
                    delta_y_list.append(coord-coords[1])
        coords[0] = factor*coords[0]
        coords[1] = factor*coords[1]
        for index, coord in enumerate(coords):
            if index%2==0:
                coords[index] = coords[0] + delta_x_list.pop(0)
            else:
                coords[index] = coords[1] + delta_y_list.pop(0)
        self.diagram_tab.canvas.coords(self.canvas_id, coords)
