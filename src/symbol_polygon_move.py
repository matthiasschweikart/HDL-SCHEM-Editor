"""
Moves the port (connection-point) of a symbol, which is formed by a polygon.
Each port of a symbol has a binding to this class.
Whenever a port is picked by the mouse an instance of this class is generated.
Then also the polygon_move_list of of the diagram is analysed.
If there are other polygons selected, then these are also moved.
"""
import constants

class PolygonMove():
    def __init__(self, event,
                 window,      # : schematic_window.SchematicWindow,
                 diagram_tab, # : notebook_diagram_tab.NotebookDiagramTab,
                 symbol,
                 polygon_canvas_id,
                 port_name_canvas_id,
                 create_binding
                 ):
        self.window              = window
        self.diagram_tab         = diagram_tab
        self.symbol              = symbol
        self.polygon_canvas_id   = polygon_canvas_id
        self.port_name_canvas_id = port_name_canvas_id
        self.event_x             = self.diagram_tab.canvas.canvasx(event.x)
        self.event_y             = self.diagram_tab.canvas.canvasy(event.y)
        polygon_coords           = self.diagram_tab.canvas.coords(polygon_canvas_id)
        self.rectangle_coords    = self.diagram_tab.canvas.coords(self.symbol.symbol_definition["rectangle"]["canvas_id"])
        self.wire_ref, self.move_point = self.__get_information_from_connected_line(polygon_coords)
        if create_binding:
            self.func_id_motion         = self.diagram_tab.canvas.tag_bind(self.symbol.symbol_definition["object_tag"], "<Motion>", self.__move_polygon)
            self.func_id_button_release = self.diagram_tab.canvas.tag_bind(self.symbol.symbol_definition["object_tag"], "<ButtonRelease-1>",
                                                                           lambda event : self.__move_polygon_end())
        self.__create_polygon_move_objects_for_other_polygons(event)

    def __create_polygon_move_objects_for_other_polygons(self, event):
        polygon_move_list = self.diagram_tab.get_polygon_move_list() # polygon_move_list = [[symbol_reference, canvas_id_selected], ...]
        self.foreign_polygon_move_objects = []
        for polygon_move_list_entry in polygon_move_list:
            foreign_polygon_canvas_id = polygon_move_list_entry[1]
            if polygon_move_list_entry[1]!=self.polygon_canvas_id:
                foreign_symbol = polygon_move_list_entry[0]
                for port_list_entry in foreign_symbol.symbol_definition["port_list"]:
                    if port_list_entry["canvas_id"]==foreign_polygon_canvas_id:
                        foreign_port_name_canvas_id = port_list_entry["canvas_id_text"]
                        self.foreign_polygon_move_objects.append(PolygonMove(event, self.window, self.diagram_tab, foreign_symbol,
                                                                     foreign_polygon_canvas_id, foreign_port_name_canvas_id, False))

    def __get_information_from_connected_line(self,polygon_coords):
        polygon_connection_point_x = polygon_coords[0]
        polygon_connection_point_y = polygon_coords[1]
        overlapping_ids            = self.diagram_tab.canvas.find_overlapping(polygon_connection_point_x - 0.5*self.window.design.get_grid_size(),
                                                                              polygon_connection_point_y - 0.5*self.window.design.get_grid_size(),
                                                                              polygon_connection_point_x + 0.5*self.window.design.get_grid_size(),
                                                                              polygon_connection_point_y + 0.5*self.window.design.get_grid_size())
        wire_ref   = None
        move_point = None
        for canvas_id in overlapping_ids:
            if self.diagram_tab.canvas.type(canvas_id)=="line" and "grid_line" not in self.diagram_tab.canvas.gettags(canvas_id):
                line_coords = self.diagram_tab.canvas.coords(canvas_id)
                if   (abs(line_coords[ 0]-polygon_connection_point_x)<self.window.design.get_grid_size()/10 and
                      abs(line_coords[ 1]-polygon_connection_point_y)<self.window.design.get_grid_size()/10):
                    move_point = "first"
                    wire_ref = self.window.design.get_references([canvas_id])[0]
                elif (abs(line_coords[-2]-polygon_connection_point_x)<self.window.design.get_grid_size()/10 and
                      abs(line_coords[-1]-polygon_connection_point_y)<self.window.design.get_grid_size()/10):
                    move_point = "last"
                    wire_ref = self.window.design.get_references([canvas_id])[0]
        return wire_ref, move_point

    def __move_polygon(self, event):
        new_event_x = self.diagram_tab.canvas.canvasx(event.x)
        new_event_y = self.diagram_tab.canvas.canvasy(event.y)
        delta_x = new_event_x - self.event_x
        delta_y = new_event_y - self.event_y
        sum_in_rotation_direction = self.move_by_delta_or_by_sum(delta_x, delta_y, None, last_move=False)
        for foreign_polygon_move_object in self.foreign_polygon_move_objects:
            foreign_polygon_move_object.move_by_delta_or_by_sum(0, 0, sum_in_rotation_direction, last_move=False)
        self.event_x = new_event_x
        self.event_y = new_event_y

    def move_by_delta_or_by_sum(self, delta_x, delta_y, sum_in_rotation_direction, last_move):
        connection_point_delta_x, connection_point_delta_y = 0, 0
        delta_x_fix_for_text = 0
        delta_y_fix_for_text = 0
        text_angle     = self.diagram_tab.canvas.itemcget(self.port_name_canvas_id, "angle")
        text_anchor    = self.diagram_tab.canvas.itemcget(self.port_name_canvas_id, "anchor")
        polygon_coords = self.diagram_tab.canvas.coords(self.polygon_canvas_id)
        polygon_connection_point_x = polygon_coords[0]
        polygon_connection_point_y = polygon_coords[1]
        polygon_rectangle_point_x  = polygon_coords[4]
        polygon_rectangle_point_y  = polygon_coords[5]
        if   (abs(polygon_rectangle_point_x - self.rectangle_coords[0]  )<self.window.design.get_grid_size()/10 and
              abs(polygon_rectangle_point_y - polygon_connection_point_y)<self.window.design.get_grid_size()/10): # left
            if sum_in_rotation_direction is None:
                polygon_rectangle_point_y_new = polygon_rectangle_point_y + delta_y
            else:
                polygon_rectangle_point_y_new = polygon_rectangle_point_y + sum_in_rotation_direction
            if   polygon_rectangle_point_y_new>=self.rectangle_coords[3]:
                # Move from left to bottom:
                delta_y = self.rectangle_coords[3] - polygon_rectangle_point_y
                if sum_in_rotation_direction is None:
                    delta_x = 0.5 * self.window.design.get_grid_size() # Push polygon around the edge, so when is snaps to grid it always stays touching the rectangle.
                    sum_in_rotation_direction = delta_x + delta_y
                else:
                    delta_x = sum_in_rotation_direction - delta_y
                connection_point_delta_x, connection_point_delta_y = self.__rotate_polygon("positive", self.polygon_canvas_id, polygon_coords)
                connection_point_delta_x += 0.5 * self.window.design.get_grid_size() # # Compensate distance from connection-point to rectangle.
                text_angle  = "90"
                text_anchor = "w"
                delta_x_fix_for_text = - 0.1 * self.window.design.get_grid_size()
                delta_y_fix_for_text = - 0.1 * self.window.design.get_grid_size()
            elif polygon_rectangle_point_y_new<=self.rectangle_coords[1]:
                # Move from left to top:
                delta_y = self.rectangle_coords[1] - polygon_rectangle_point_y
                if sum_in_rotation_direction is None:
                    delta_x = 0.5 * self.window.design.get_grid_size()
                    sum_in_rotation_direction = - delta_x + delta_y
                else:
                    delta_x = - sum_in_rotation_direction + delta_y
                connection_point_delta_x, connection_point_delta_y = self.__rotate_polygon("negative", self.polygon_canvas_id, polygon_coords)
                connection_point_delta_x += 0.5 * self.window.design.get_grid_size() # Compensate distance from connection-point to rectangle.
                text_angle  = "90"
                text_anchor = "e"
                delta_x_fix_for_text = - 0.1 * self.window.design.get_grid_size()
                delta_y_fix_for_text = + 0.1 * self.window.design.get_grid_size()
            else:
                # Stay at left:
                delta_x = 0
                if sum_in_rotation_direction is None:
                    sum_in_rotation_direction = delta_y
                else:
                    delta_y = sum_in_rotation_direction
        elif (abs(polygon_rectangle_point_x - self.rectangle_coords[2]  )<self.window.design.get_grid_size()/10 and
              abs(polygon_rectangle_point_y - polygon_connection_point_y)<self.window.design.get_grid_size()/10): # right
            if sum_in_rotation_direction is None:
                polygon_rectangle_point_y_new = polygon_rectangle_point_y + delta_y
            else:
                polygon_rectangle_point_y_new = polygon_rectangle_point_y - sum_in_rotation_direction
            if polygon_rectangle_point_y_new>=self.rectangle_coords[3]:
                # move from right to bottom:
                delta_y = self.rectangle_coords[3] - polygon_rectangle_point_y
                if sum_in_rotation_direction is None:
                    delta_x = -0.5 * self.window.design.get_grid_size()
                    sum_in_rotation_direction = delta_x - delta_y
                else:
                    delta_x = sum_in_rotation_direction + delta_y
                connection_point_delta_x, connection_point_delta_y = self.__rotate_polygon("negative", self.polygon_canvas_id, polygon_coords)
                connection_point_delta_x -= 0.5 * self.window.design.get_grid_size() # Compensate distance from connection-point to rectangle.
                text_angle  = "90"
                text_anchor = "w"
                delta_x_fix_for_text = + 0.1 * self.window.design.get_grid_size()
                delta_y_fix_for_text = - 0.1 * self.window.design.get_grid_size()
            elif polygon_rectangle_point_y_new<=self.rectangle_coords[1]: #
                # move from right to top:
                delta_y = self.rectangle_coords[1] - polygon_rectangle_point_y
                if sum_in_rotation_direction is None:
                    delta_x = -0.5 * self.window.design.get_grid_size()
                    sum_in_rotation_direction = - delta_x - delta_y
                else:
                    delta_x = - sum_in_rotation_direction - delta_y
                connection_point_delta_x, connection_point_delta_y = self.__rotate_polygon("positive", self.polygon_canvas_id, polygon_coords)
                connection_point_delta_x -= 0.5 * self.window.design.get_grid_size() # Compensate distance from connection-point to rectangle.
                text_angle  = "90"
                text_anchor = "e"
                delta_x_fix_for_text = + 0.1 * self.window.design.get_grid_size()
                delta_y_fix_for_text = + 0.1 * self.window.design.get_grid_size()
            else:
                # Stay at right:
                delta_x = 0
                if sum_in_rotation_direction is None:
                    sum_in_rotation_direction = - delta_y
                else:
                    delta_y = - sum_in_rotation_direction
        elif (abs(polygon_rectangle_point_y - self.rectangle_coords[1]  )<self.window.design.get_grid_size()/10 and
              abs(polygon_rectangle_point_x - polygon_connection_point_x)<self.window.design.get_grid_size()/10): # top
            if sum_in_rotation_direction is None:
                polygon_rectangle_point_x_new = polygon_rectangle_point_x + delta_x
            else:
                polygon_rectangle_point_x_new = polygon_rectangle_point_x - sum_in_rotation_direction
            if polygon_rectangle_point_x_new>=self.rectangle_coords[2]:
                # move from top to right:
                delta_x = self.rectangle_coords[2] - polygon_rectangle_point_x
                if sum_in_rotation_direction is None:
                    delta_y = 0.5 * self.window.design.get_grid_size()
                    sum_in_rotation_direction = - delta_x - delta_y
                else:
                    delta_y = - sum_in_rotation_direction - delta_x
                connection_point_delta_x, connection_point_delta_y = self.__rotate_polygon("negative", self.polygon_canvas_id, polygon_coords)
                connection_point_delta_y += 0.5 * self.window.design.get_grid_size() # Compensate distance from connection-point to rectangle.
                text_angle  = "0"
                text_anchor = "e"
                delta_x_fix_for_text = - 0.1 * self.window.design.get_grid_size()
                delta_y_fix_for_text = - 0.1 * self.window.design.get_grid_size()
            elif polygon_rectangle_point_x_new<=self.rectangle_coords[0]:
                # move from top to left:
                delta_x = self.rectangle_coords[0] - polygon_rectangle_point_x
                if sum_in_rotation_direction is None:
                    delta_y = 0.5 * self.window.design.get_grid_size()
                    sum_in_rotation_direction = - delta_x + delta_y
                else:
                    delta_y = sum_in_rotation_direction + delta_x
                connection_point_delta_x, connection_point_delta_y = self.__rotate_polygon("positive", self.polygon_canvas_id, polygon_coords)
                connection_point_delta_y += 0.5 * self.window.design.get_grid_size() # Compensate distance from connection-point to rectangle.
                text_angle  = "0"
                text_anchor = "w"
                delta_x_fix_for_text = + 0.1 * self.window.design.get_grid_size()
                delta_y_fix_for_text = - 0.1 * self.window.design.get_grid_size()
            else:
                # Stay at top:
                delta_y = 0
                if sum_in_rotation_direction is None:
                    sum_in_rotation_direction = - delta_x
                else:
                    delta_x = - sum_in_rotation_direction
        elif (abs(polygon_rectangle_point_y - self.rectangle_coords[3]  )<self.window.design.get_grid_size()/10 and
              abs(polygon_rectangle_point_x - polygon_connection_point_x)<self.window.design.get_grid_size()/10): # bottom
            if sum_in_rotation_direction is None:
                polygon_rectangle_point_x_new = polygon_rectangle_point_x + delta_x
            else:
                polygon_rectangle_point_x_new = polygon_rectangle_point_x + sum_in_rotation_direction
            if polygon_rectangle_point_x_new>=self.rectangle_coords[2]:
                # move from bottom to right:
                delta_x = self.rectangle_coords[2] - polygon_rectangle_point_x
                if sum_in_rotation_direction is None:
                    delta_y = -0.5 * self.window.design.get_grid_size()
                    sum_in_rotation_direction = delta_x - delta_y
                else:
                    delta_y = - sum_in_rotation_direction + delta_x
                connection_point_delta_x, connection_point_delta_y = self.__rotate_polygon("positive", self.polygon_canvas_id, polygon_coords)
                connection_point_delta_y -= 0.5 * self.window.design.get_grid_size() # Compensate distance from connection-point to rectangle.
                text_angle  = "0"
                text_anchor = "e"
                delta_x_fix_for_text = - 0.1 * self.window.design.get_grid_size()
                delta_y_fix_for_text = + 0.1 * self.window.design.get_grid_size()
            elif polygon_rectangle_point_x_new<=self.rectangle_coords[0]:
                # move from bottom to left:
                delta_x = self.rectangle_coords[0] - polygon_rectangle_point_x
                if sum_in_rotation_direction is None:
                    delta_y = -0.5 * self.window.design.get_grid_size()
                    sum_in_rotation_direction = delta_x + delta_y
                else:
                    delta_y = sum_in_rotation_direction - delta_x
                connection_point_delta_x, connection_point_delta_y = self.__rotate_polygon("negative", self.polygon_canvas_id, polygon_coords)
                connection_point_delta_y -= 0.5 * self.window.design.get_grid_size() # Compensate distance from connection-point to rectangle.
                text_angle  = "0"
                text_anchor = "w"
                delta_x_fix_for_text = + 0.1 * self.window.design.get_grid_size()
                delta_y_fix_for_text = + 0.1 * self.window.design.get_grid_size()
            else:
                # Stay at bottom:
                delta_y = 0
                if sum_in_rotation_direction is None:
                    sum_in_rotation_direction = delta_x
                else:
                    delta_x = sum_in_rotation_direction
        else:
            print("move_by_delta_or_by_sum: Fatal, rectangle side not determined.")
        delta_x_text = delta_x + delta_x_fix_for_text
        delta_y_text = delta_y + delta_y_fix_for_text
        self.diagram_tab.canvas.itemconfigure(self.port_name_canvas_id, angle=text_angle)
        self.diagram_tab.canvas.itemconfigure(self.port_name_canvas_id, anchor=text_anchor)
        self.diagram_tab.canvas.move(self.polygon_canvas_id  , delta_x     , delta_y)
        self.diagram_tab.canvas.move(self.port_name_canvas_id, delta_x_text, delta_y_text)
        if last_move:
            if "symbol_color" in self.symbol.symbol_definition["rectangle"]:
                symbol_color = self.symbol.symbol_definition["rectangle"]["symbol_color"]
            else:
                symbol_color = constants.SYMBOL_DEFAULT_COLOR
            self.diagram_tab.canvas.itemconfigure(self.polygon_canvas_id, fill=symbol_color)
            self.diagram_tab.canvas.dtag         (self.polygon_canvas_id, "selected")
        if self.wire_ref is not None:
            wire_delta_x = delta_x + connection_point_delta_x
            wire_delta_y = delta_y + connection_point_delta_y
            if last_move:
                self.wire_ref.move_wire_end_point("last_time", self.move_point, wire_delta_x, wire_delta_y)
            else:
                self.wire_ref.move_wire_end_point("not move end", self.move_point, wire_delta_x, wire_delta_y)
        return sum_in_rotation_direction

    def __rotate_polygon(self, direction, polygon_canvas_id, polygon_coords):
        polygon_coords_new = [0, 0, 0, 0, 0, 0, 0, 0]
        polygon_rectangle_point_x = polygon_coords[4]
        polygon_rectangle_point_y = polygon_coords[5]
        for point in range(4):
            diff_x, diff_y = polygon_coords[2*point] - polygon_rectangle_point_x, polygon_coords[2*point+1] - polygon_rectangle_point_y
            if direction=="negative":
                diff_x_rot = -diff_y
                diff_y_rot =  diff_x
            else:
                diff_x_rot =  diff_y
                diff_y_rot = -diff_x
            polygon_coords_new[2*point], polygon_coords_new[2*point+1] = polygon_rectangle_point_x + diff_x_rot, polygon_rectangle_point_y + diff_y_rot
            if point==0:
                connection_point_delta_x = diff_x_rot
                connection_point_delta_y = diff_y_rot
        self.diagram_tab.canvas.coords(polygon_canvas_id, polygon_coords_new)
        return connection_point_delta_x, connection_point_delta_y

    def __move_polygon_end(self):
        self.diagram_tab.canvas.tag_unbind(self.symbol.symbol_definition["object_tag"], "<Motion>"         , self.func_id_motion)
        self.diagram_tab.canvas.tag_unbind(self.symbol.symbol_definition["object_tag"], "<ButtonRelease-1>", self.func_id_button_release)
        self.func_id_motion         = None
        self.func_id_button_release = None
        delta_x, delta_y = self.__calculate_delta_to_grid(self.polygon_canvas_id)
        sum_in_rotation_direction = self.move_by_delta_or_by_sum(delta_x, delta_y, None, last_move=True)
        for foreign_polygon_move_object in self.foreign_polygon_move_objects:
            foreign_polygon_move_object.move_by_delta_or_by_sum(0, 0, sum_in_rotation_direction, last_move=True)
        self.symbol.store_item(push_design_to_stack=True, signal_design_change=True)

    def __calculate_delta_to_grid(self, polygon_canvas_id):
        polygon_coords = self.diagram_tab.canvas.coords(polygon_canvas_id)
        connecting_point_x = polygon_coords[0]
        connecting_point_y = polygon_coords[1]
        remainder_x = connecting_point_x % self.window.design.get_grid_size()
        remainder_y = connecting_point_y % self.window.design.get_grid_size()
        delta_x = - remainder_x
        delta_y = - remainder_y
        if remainder_x>self.window.design.get_grid_size()/2:
            delta_x += self.window.design.get_grid_size()
        if remainder_y>self.window.design.get_grid_size()/2:
            delta_y += self.window.design.get_grid_size()
        return delta_x, delta_y
