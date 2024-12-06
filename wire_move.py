"""
Features for moving wires:
To move a wire, you have to pick it up with the left mouse button.

If the wire is not connected to any pin or block:
1. If the wire has 1 segment, and is picked up in the middle, then the complete wire is moved.
2. If the wire has 1 segment, and is picked at an end, then the other wire end is fixed during moving.
3. If the wire has more than 1 segment, then only the touched segment is moved.
4. If a wire end is picked up and additional the Shift-Key is pressed, then an additional edge is inserted in the wire.

If a wire end is connected to a pin and is moved:
If the Shift-Key is not pressed, then the connection to the pin is kept at any move of the wire end.
If the Shift-Key is pressed, then the connection to the pin is disconnected.

If a wire end is connected to a block, then the point where the wire touches the block is handled like a pin.
"""

class WireMove():
    def __init__(self, event,
                 window,      #: schematic_window.SchematicWindow,
                 diagram_tab, #: notebook_diagram_tab.NotebookDiagramTab,
                 parent,
                 canvas_id, wire_tag, shift_was_pressed):
        self.window      = window
        self.diagram_tab = diagram_tab
        self.parent      = parent
        self.canvas_id   = canvas_id
        self.wire_tag    = wire_tag
        if self.window.config()["cursor"][4]=="cross":
            return # During wire insertion Button-1 clicks shall not move a wire.
        self.event_x        = self.diagram_tab.canvas.canvasx(event.x)
        self.event_y        = self.diagram_tab.canvas.canvasy(event.y)
        wire_coords         = self.diagram_tab.canvas.coords(self.canvas_id)
        number_of_points    = len(wire_coords)//2
        number_of_segments  = number_of_points - 1
        end_point_connected = self.parent.determine_connected_endpoints(wire_coords) # May have values: "none", "first", "last", "both"
        touched_segment     = self.__get_touched_segment(wire_coords) # May have values "[first|last]_[horizontal|vertical]" or "middle".
        segment_to_move, direction_of_segment = self.__determine_segment_to_move(number_of_segments, wire_coords) # May have values 0, 1, 2, ... and "horizontal"/"vertical"
        if number_of_segments==1:
            how_to_move_the_signal_name = "move_x_and_y"
        else:
            how_to_move_the_signal_name = self.__determine_how_to_move_the_signal_name_by_measuring_the_distance_to_event(segment_to_move, wire_coords, direction_of_segment)
        #print("touched_segment      =", touched_segment)
        #print("segment_to_move      =", segment_to_move)
        #print("direction_of_segment =", direction_of_segment)
        #print("how_to_move_the_signal_name =", how_to_move_the_signal_name)
        if touched_segment=="middle":
            x_coordinate_to_change = [False] * number_of_points
            y_coordinate_to_change = [False] * number_of_points
            if direction_of_segment=="horizontal":
                y_coordinate_to_change[segment_to_move  ] = True
                y_coordinate_to_change[segment_to_move+1] = True
                if how_to_move_the_signal_name!="not":
                    how_to_move_the_signal_name = "move_y" # A "middle" segment shall not move the signalname depending from the touching point.
            else:
                x_coordinate_to_change[segment_to_move  ] = True
                x_coordinate_to_change[segment_to_move+1] = True
                if how_to_move_the_signal_name!="not":
                    how_to_move_the_signal_name = "move_x" # A "middle" segment shall not move the signalname depending from the touching point.
        else: # touched_segment!="middle"
            if end_point_connected=="none" and number_of_segments==1:
                if shift_was_pressed is False: # No new edge is inserted in the wire.
                    x_coordinate_to_change = [True] * number_of_points
                    y_coordinate_to_change = [True] * number_of_points
                    if touched_segment=="first_horizontal":
                        if   (abs(self.event_x - wire_coords[ 0])<self.window.design.get_grid_size()/2 and
                              abs(self.event_y - wire_coords[ 1])<self.window.design.get_grid_size()/2):   # The first point of the wire is moved.
                            x_coordinate_to_change[1] = False
                        elif (abs(self.event_x - wire_coords[-2])<self.window.design.get_grid_size()/2 and
                              abs(self.event_y - wire_coords[-1])<self.window.design.get_grid_size()/2):   # The last point of the wire is moved.
                            x_coordinate_to_change[0] = False
                        else: # The wire is touched in the "middle"
                            how_to_move_the_signal_name = "move_x_and_y" # The complete wire is moved, so the signal name must move in the same way.
                    else: # "first_vertical"
                        if   (abs(self.event_x - wire_coords[ 0])<self.window.design.get_grid_size()/2 and
                              abs(self.event_y - wire_coords[ 1])<self.window.design.get_grid_size()/2):   # The first point of the wire is moved.
                            y_coordinate_to_change[1] = False
                        elif (abs(self.event_x - wire_coords[-2])<self.window.design.get_grid_size()/2 and
                              abs(self.event_y - wire_coords[-1])<self.window.design.get_grid_size()/2):   # The last point of the wire is moved.
                            y_coordinate_to_change[0] = False
                        else: # The wire is touched in the "middle"
                            how_to_move_the_signal_name = "move_x_and_y" # The complete wire is moved, so the signal name must move in the same way.
                else: # A new edge is inserted in the wire.
                    how_to_move_the_signal_name = "not"
                    if abs(self.event_x-wire_coords[0])<abs(self.event_x-wire_coords[2]):
                        wire_coords[:0] = wire_coords[0:2] # duplicate first point of the wire.
                        self.diagram_tab.canvas.coords(self.canvas_id, wire_coords)
                        x_coordinate_to_change = [False] * (number_of_points + 1)
                        y_coordinate_to_change = [False] * (number_of_points + 1)
                        y_coordinate_to_change[0] = True
                    else:
                        wire_coords[len(wire_coords):] = wire_coords[-2:] # duplicate last point of the wire.
                        self.diagram_tab.canvas.coords(self.canvas_id, wire_coords)
                        x_coordinate_to_change = [False] * (number_of_points + 1)
                        y_coordinate_to_change = [False] * (number_of_points + 1)
                        y_coordinate_to_change[-1] = True
            elif touched_segment in ["first_horizontal", "first_vertical"]:
                if end_point_connected=="none": # number_of_segments > 1
                    if shift_was_pressed is False: # No new edge is inserted in the wire.
                        x_coordinate_to_change = [False] * number_of_points
                        y_coordinate_to_change = [False] * number_of_points
                        if touched_segment=="first_horizontal":
                            x_coordinate_to_change[0] = True
                            y_coordinate_to_change[0] = True
                            y_coordinate_to_change[1] = True
                        else:
                            x_coordinate_to_change[0] = True
                            y_coordinate_to_change[0] = True
                            x_coordinate_to_change[1] = True
                    else: # A new edge is inserted in the wire.
                        wire_coords[:0] = wire_coords[0:2] # duplicate first point of the wire.
                        self.diagram_tab.canvas.coords(self.canvas_id, wire_coords)
                        x_coordinate_to_change = [False] * (number_of_points + 1)
                        y_coordinate_to_change = [False] * (number_of_points + 1)
                        if touched_segment in ["first_horizontal"]:
                            y_coordinate_to_change[0] = True
                        else:
                            x_coordinate_to_change[0] = True
                elif number_of_segments==1: # end_point_connected!="none"
                    if end_point_connected=="first":
                        # If event is closer to first point than to second point:
                        if ((touched_segment=="first_horizontal" and abs(self.event_x-wire_coords[0])<abs(self.event_x-wire_coords[2])) or
                            (touched_segment=="first_vertical"   and abs(self.event_y-wire_coords[1])<abs(self.event_y-wire_coords[3]))):  # Disconnect
                            #print("Abtrennen first von 1 segment")
                            x_coordinate_to_change = [True] * number_of_points
                            y_coordinate_to_change = [True] * number_of_points
                        else:
                            if shift_was_pressed is True:
                                wire_coords[len(wire_coords):] = wire_coords[-2:] # duplicate last point of the wire.
                                self.diagram_tab.canvas.coords(self.canvas_id, wire_coords)
                                x_coordinate_to_change = [False] * (number_of_points + 1)
                                y_coordinate_to_change = [False] * (number_of_points + 1)
                                # make new last point movable
                                if touched_segment=="first_vertical":
                                    x_coordinate_to_change[-1] = True # Fix am 28.08.2023
                                else:
                                    y_coordinate_to_change[-1] = True
                            else: # A new edge is inserted in the wire.
                                wire_coords[:0] = wire_coords[0:2] # duplicate first point of the wire.
                                self.diagram_tab.canvas.coords(self.canvas_id, wire_coords)
                                x_coordinate_to_change = [False] * (number_of_points + 1)
                                y_coordinate_to_change = [False] * (number_of_points + 1)
                                if touched_segment=="first_horizontal":
                                    y_coordinate_to_change[1] = True
                                    x_coordinate_to_change[2] = True
                                    y_coordinate_to_change[2] = True
                                    how_to_move_the_signal_name = "move_y" # New
                                else: # touched_segment=="first_vertical"
                                    x_coordinate_to_change[1] = True
                                    x_coordinate_to_change[2] = True
                                    y_coordinate_to_change[2] = True
                                    how_to_move_the_signal_name = "move_x" # New
                    elif end_point_connected=="last":
                        # If event is closer to last point than to first point:
                        if ((touched_segment=="first_horizontal" and abs(self.event_x-wire_coords[2])<abs(self.event_x-wire_coords[0])) or
                            (touched_segment=="first_vertical"   and abs(self.event_y-wire_coords[3])<abs(self.event_y-wire_coords[1]))):  # Disconnect
                            #print("Abtrennen last von 1 segment")
                            x_coordinate_to_change = [True] * number_of_points
                            y_coordinate_to_change = [True] * number_of_points
                        else:
                            if shift_was_pressed is True:
                                wire_coords[:0] = wire_coords[0:2] # duplicate first point of the wire.
                                self.diagram_tab.canvas.coords(self.canvas_id, wire_coords)
                                x_coordinate_to_change = [False] * (number_of_points + 1)
                                y_coordinate_to_change = [False] * (number_of_points + 1)
                                # make new first point movable
                                if touched_segment=="first_horizontal":
                                    y_coordinate_to_change[0] = True
                                else:
                                    x_coordinate_to_change[0] = True
                            else:
                                wire_coords[len(wire_coords):] = wire_coords[-2:] # duplicate last point of the wire.
                                self.diagram_tab.canvas.coords(self.canvas_id, wire_coords)
                                x_coordinate_to_change = [False] * (number_of_points + 1)
                                y_coordinate_to_change = [False] * (number_of_points + 1)
                                if touched_segment=="first_horizontal":
                                    x_coordinate_to_change[0] = True
                                    y_coordinate_to_change[0] = True
                                    y_coordinate_to_change[1] = True
                                else: # touched_segment=="first_vertical"
                                    x_coordinate_to_change[0] = True
                                    y_coordinate_to_change[0] = True
                                    x_coordinate_to_change[1] = True
                    else: # end_point_connected is "both"
                        x_coordinate_to_change = [False] * (number_of_points + 1)
                        y_coordinate_to_change = [False] * (number_of_points + 1)
                        # If event was closer to first point than to second point:
                        if ((touched_segment=="first_horizontal" and abs(self.event_x-wire_coords[0])<abs(self.event_x-wire_coords[2])) or
                            (touched_segment=="first_vertical"   and abs(self.event_y-wire_coords[1])<abs(self.event_y-wire_coords[3]))):  # Disconnect
                            #print("Abtrennen first 1 segment both connected")
                            wire_coords[:0] = wire_coords[0:2] # duplicate first point of the wire.
                            self.diagram_tab.canvas.coords(self.canvas_id, wire_coords)
                            if touched_segment=="first_horizontal":
                                x_coordinate_to_change[0] = True
                                y_coordinate_to_change[0] = True
                                x_coordinate_to_change[1] = True
                                if how_to_move_the_signal_name!="not":
                                    how_to_move_the_signal_name = "move_x_and_y"
                            else:
                                x_coordinate_to_change[0] = True
                                y_coordinate_to_change[0] = True
                                y_coordinate_to_change[1] = True
                                if how_to_move_the_signal_name!="not":
                                    how_to_move_the_signal_name = "move_x_and_y"
                        else:
                            #print("Abtrennen last 1 segment both connected")
                            wire_coords[len(wire_coords):] = wire_coords[-2:] # duplicate last point of the wire.
                            self.diagram_tab.canvas.coords(self.canvas_id, wire_coords)
                            if touched_segment=="first_horizontal":
                                x_coordinate_to_change[1] = True
                                x_coordinate_to_change[2] = True
                                y_coordinate_to_change[2] = True
                                if how_to_move_the_signal_name!="not":
                                    how_to_move_the_signal_name = "move_x_and_y"
                            else:
                                y_coordinate_to_change[1] = True
                                x_coordinate_to_change[2] = True
                                y_coordinate_to_change[2] = True
                                if how_to_move_the_signal_name!="not":
                                    how_to_move_the_signal_name = "move_x_and_y"
                else: # end_point_connected!="none" and number_of_segments>1
                    if end_point_connected in ["first", "both"]:
                        #print("Abtrennen first horizontal mehr segmente")
                        x_coordinate_to_change = [False] * number_of_points
                        y_coordinate_to_change = [False] * number_of_points
                        if touched_segment=="first_horizontal":
                            x_coordinate_to_change[0] = True
                            y_coordinate_to_change[0] = True
                            y_coordinate_to_change[1] = True
                        else: # touched_segment=="first_vertical"
                            x_coordinate_to_change[0] = True
                            y_coordinate_to_change[0] = True
                            x_coordinate_to_change[1] = True
                    else: # end_point_connected=="last"
                        if shift_was_pressed is False: # No new edge but first segment can be moved free.
                            x_coordinate_to_change = [False] * number_of_points
                            y_coordinate_to_change = [False] * number_of_points
                            if touched_segment=="first_horizontal":
                                x_coordinate_to_change[0] = True
                                y_coordinate_to_change[0] = True
                                y_coordinate_to_change[1] = True
                            else: # touched_segment=="first_vertical"
                                x_coordinate_to_change[0] = True
                                y_coordinate_to_change[0] = True
                                x_coordinate_to_change[1] = True
                        else: # Insert new edge into the wire.
                            wire_coords[:0] = wire_coords[0:2] # duplicate first point of the wire.
                            self.diagram_tab.canvas.coords(self.canvas_id, wire_coords)
                            x_coordinate_to_change = [False] * (number_of_points + 1)
                            y_coordinate_to_change = [False] * (number_of_points + 1)
                            # make first point movable
                            if touched_segment=="first_horizontal":
                                y_coordinate_to_change[0] = True
                            else:
                                x_coordinate_to_change[0] = True
            else: # touched_segment in ["last_horizontal", "last_vertical"]
                if end_point_connected=="none": # number_of_segments > 1
                    if shift_was_pressed is False: # No new edge but last segment can be moved free.
                        x_coordinate_to_change = [False] * number_of_points
                        y_coordinate_to_change = [False] * number_of_points
                        if touched_segment=="last_horizontal":
                            x_coordinate_to_change[-1] = True
                            y_coordinate_to_change[-1] = True
                            y_coordinate_to_change[-2] = True
                        else:
                            x_coordinate_to_change[-1] = True
                            y_coordinate_to_change[-1] = True
                            x_coordinate_to_change[-2] = True
                    else: # Insert new edge into the wire.
                        wire_coords[len(wire_coords):] = wire_coords[-2:] # duplicate last point of the wire.
                        self.diagram_tab.canvas.coords(self.canvas_id, wire_coords)
                        x_coordinate_to_change = [False] * (number_of_points + 1)
                        y_coordinate_to_change = [False] * (number_of_points + 1)
                        if touched_segment in ["last_horizontal"]:
                            y_coordinate_to_change[-1] = True
                        else:
                            x_coordinate_to_change[-1] = True
                elif number_of_segments==1: # end_point_connected!="none"
                    pass # cannot be reached, as 1 segment always is handled in "first_horizontal/vertical" branch.
                else: # end_point_connected!="none" and number_of_segments>1
                    if end_point_connected in ["last", "both"]:
                        #print("Abtrennen last-horizontal mehr segmente")
                        x_coordinate_to_change = [False] * number_of_points
                        y_coordinate_to_change = [False] * number_of_points
                        if touched_segment=="last_horizontal":
                            x_coordinate_to_change[-1] = True
                            y_coordinate_to_change[-1] = True
                            y_coordinate_to_change[-2] = True
                        else: # touched_segment=="first_vertical"
                            x_coordinate_to_change[-1] = True
                            y_coordinate_to_change[-1] = True
                            x_coordinate_to_change[-2] = True
                    else: # end_point_connected=="first"
                        if shift_was_pressed is False: # No new edge, but the last segment can be moved freely.
                            x_coordinate_to_change = [False] * number_of_points
                            y_coordinate_to_change = [False] * number_of_points
                            if touched_segment=="last_horizontal":
                                x_coordinate_to_change[-1] = True
                                y_coordinate_to_change[-1] = True
                                y_coordinate_to_change[-2] = True
                            else: # touched_segment=="last_vertical"
                                x_coordinate_to_change[-1] = True
                                y_coordinate_to_change[-1] = True
                                x_coordinate_to_change[-2] = True
                        else:
                            wire_coords[len(wire_coords):] = wire_coords[-2:] # duplicate last point of the wire.
                            self.diagram_tab.canvas.coords(self.canvas_id, wire_coords)
                            x_coordinate_to_change = [False] * (number_of_points + 1)
                            y_coordinate_to_change = [False] * (number_of_points + 1)
                            # make last point movable
                            if touched_segment=="last_horizontal":
                                y_coordinate_to_change[-1] = True
                            else:
                                x_coordinate_to_change[-1] = True
        if how_to_move_the_signal_name=="move_x_and_y":
            # A signal name may have caused "move_x_and_y" although it does not "sit" at the moved segment, but at the neighbor segment.
            # But when only x or only y is changed, then the signal-name must behave in the same way:
            if True not in y_coordinate_to_change:
                how_to_move_the_signal_name = "move_x"
            if True not in x_coordinate_to_change:
                how_to_move_the_signal_name = "move_y"
        self.funcid_motion         = self.diagram_tab.canvas.tag_bind(self.canvas_id, "<Motion>",
                                                    lambda event, x_coordinate_to_change=x_coordinate_to_change, y_coordinate_to_change=y_coordinate_to_change:
                                                    self.__move_to(event, x_coordinate_to_change, y_coordinate_to_change, how_to_move_the_signal_name) )
        self.funcid_button_release = self.diagram_tab.canvas.tag_bind(self.canvas_id, "<ButtonRelease-1>",
                                                    lambda event, x_coordinate_to_change=x_coordinate_to_change, y_coordinate_to_change=y_coordinate_to_change:
                                                    self.__move_end (x_coordinate_to_change, y_coordinate_to_change, how_to_move_the_signal_name) )

    def __determine_how_to_move_the_signal_name_by_measuring_the_distance_to_event(self, segment_to_move, wire_coords, direction_of_segment):
        if self.parent.signal_name_not_near_segment(segment_to_move, wire_coords):
            #print("not near segment")
            return "not"
        segment_coords = wire_coords[2*segment_to_move:2*segment_to_move+4]
        signal_name_bbox = self.diagram_tab.canvas.bbox(self.wire_tag + "_signal_name")
        signal_name_center_x = (signal_name_bbox[0] + signal_name_bbox[2])/2
        signal_name_center_y = (signal_name_bbox[1] + signal_name_bbox[3])/2
        if direction_of_segment=="horizontal":
            segment_length = segment_coords[2] - segment_coords[0]
            distance_event_to_end_segment_left  = self.event_x - segment_coords[0]
            if distance_event_to_end_segment_left<=segment_length/2:
                event_position = "left"
            else:
                event_position = "right"
            distance_name_to_end_segment_left  = signal_name_center_x - segment_coords[0]
            signal_name_length = signal_name_bbox[2] - signal_name_bbox[0]
            if signal_name_length>0.7*segment_length:
                name_position = event_position
            else:
                if distance_name_to_end_segment_left<=segment_length/2:
                    name_position = "left"
                else:
                    name_position = "right"
            if event_position==name_position:
                return "move_x_and_y"
            if event_position=="right":
                return "move_y"
            if event_position=="left":
                return "move_x"
            return "not" # "move_y" führt dazu, dass der Name, obwohl er am festen Wire-Ende sitzt, bewegt wird.
        else:
            segment_height = segment_coords[3] - segment_coords[1]
            distance_event_to_end_segment_top = self.event_y - segment_coords[1]
            if distance_event_to_end_segment_top<segment_height/2:
                event_position = "top"
            else:
                event_position = "bottom"
            distance_name_to_end_segment_top = signal_name_center_y - segment_coords[1]
            signal_name_height = signal_name_bbox[3] - signal_name_bbox[1]
            if signal_name_height>0.7*segment_height:
                name_position = event_position
            else:
                if distance_name_to_end_segment_top<segment_height/2:
                    name_position = "top"
                else:
                    name_position = "bottom"
            if event_position==name_position:
                return "move_x_and_y"
            return "not" # "move_x" führt dazu, dass der Name, obwohl er am festen Wire-Ende sitzt, bewegt wird.

    def __get_touched_segment(self, wire_coords):
        limit = self.window.design.get_grid_size()/2
        if abs(wire_coords[1]-wire_coords[3])<limit/5: # coords are equal => first segment is horizontal
            if abs(self.event_y-wire_coords[1])<limit:
                if wire_coords[0]<=wire_coords[2]:
                    if wire_coords[0]<=self.event_x<=wire_coords[2]:
                        return "first_horizontal"
                else:
                    if wire_coords[2]<=self.event_x<=wire_coords[0]:
                        return "first_horizontal"
        else: # first segment is vertical (wire_coords[0]==wire_coords[2])
            if abs(self.event_x-wire_coords[0])<limit:
                if wire_coords[1]<=wire_coords[3]:
                    if wire_coords[1]<=self.event_y<=wire_coords[3]:
                        return "first_vertical"
                else:
                    if wire_coords[3]<=self.event_y<=wire_coords[1]:
                        return "first_vertical"
        if abs(wire_coords[-3]-wire_coords[-1])<limit/5: # coords are equal => last segment is horizontal
            if abs(self.event_y-wire_coords[-3])<limit:
                if wire_coords[-4]<=wire_coords[-2]:
                    if wire_coords[-4]<=self.event_x<=wire_coords[-2]:
                        return "last_horizontal"
                else:
                    if wire_coords[-2]<=self.event_x<=wire_coords[-4]:
                        return "last_horizontal"
        else: # last segment is vertical (wire_coords[-4]==wire_coords[-2])
            if abs(self.event_x-wire_coords[-4])<limit:
                if wire_coords[-3]<=wire_coords[-1]:
                    if wire_coords[-3]<=self.event_y<=wire_coords[-1]:
                        return "last_vertical"
                else:
                    if wire_coords[-1]<=self.event_y<=wire_coords[-3]:
                        return "last_vertical"
        return "middle"

    def __determine_segment_to_move(self, number_of_segments, wire_coords):
        direction_of_segment = None
        segment_to_move      = 0 # prevents crashes, when segment_number cannot be determined, when the wire is sloping, because of some misfunction.
        for segment_number in range(number_of_segments):
            segment_start_point_x = wire_coords[2*segment_number+0]
            segment_start_point_y = wire_coords[2*segment_number+1]
            segment_end_point_x   = wire_coords[2*segment_number+2]
            segment_end_point_y   = wire_coords[2*segment_number+3]
            if abs(segment_start_point_y - segment_end_point_y)<self.window.design.get_grid_size()/10 and abs(self.event_y-segment_start_point_y)<=2: # horizontal part of the wire
                if (segment_start_point_x<=self.event_x<=segment_end_point_x or
                    segment_start_point_x>=self.event_x>=segment_end_point_x):
                    segment_to_move = segment_number
                    direction_of_segment = "horizontal"
                    break
            elif abs(segment_start_point_x - segment_end_point_x)<self.window.design.get_grid_size()/10 and abs(self.event_x-segment_start_point_x)<=2: # vertical part of the wire
                if (segment_start_point_y<=self.event_y<=segment_end_point_y or
                    segment_start_point_y>=self.event_y>=segment_end_point_y):
                    segment_to_move = segment_number
                    direction_of_segment = "vertical"
                    break
        return segment_to_move, direction_of_segment

    def __move_to(self, event, x_coordinate_to_change, y_coordinate_to_change, how_to_move_the_signal_name):
        new_event_x = self.diagram_tab.canvas.canvasx(event.x)
        new_event_y = self.diagram_tab.canvas.canvasy(event.y)
        delta_x = new_event_x - self.event_x
        delta_y = new_event_y - self.event_y
        self.event_x = new_event_x
        self.event_y = new_event_y
        coords = self.diagram_tab.canvas.coords(self.canvas_id)
        for number in range(len(coords)//2):
            if x_coordinate_to_change[number] is True:
                coords[2*number  ] += delta_x
            if y_coordinate_to_change[number] is True:
                coords[2*number+1] += delta_y
        self.diagram_tab.canvas.coords(self.canvas_id, coords)
        if how_to_move_the_signal_name=="not":
            delta_x = 0
            delta_y = 0
        elif how_to_move_the_signal_name=="move_x":
            delta_y = 0
        elif how_to_move_the_signal_name=="move_y":
            delta_x = 0
        self.parent.move_signal_name(delta_x, delta_y)

    def __move_end(self, x_coordinate_to_change, y_coordinate_to_change, how_to_move_the_signal_name):
        # Determine the distance of the moved points of the wire to the grid:
        coords = self.diagram_tab.canvas.coords(self.canvas_id)
        coords, delta_x_for_signalname, delta_y_for_signalname = self.__move_modified_coordinates_to_the_grid(coords, x_coordinate_to_change, y_coordinate_to_change)
        coords = self.parent.remove_unnecessary_points(coords)
        if not (abs(coords[0] - coords[-2])<self.window.design.get_grid_size()/10 and
                abs(coords[1] - coords[-1])<self.window.design.get_grid_size()/10): # Wires with length 0 or wire-circles are not allowed.
            self.diagram_tab.canvas.tag_unbind(self.canvas_id, "<Motion>"         , self.funcid_motion)
            self.diagram_tab.canvas.tag_unbind(self.canvas_id, "<ButtonRelease-1>", self.funcid_button_release)
            self.funcid_motion = None
            self.funcid_button_release = None
            self.diagram_tab.canvas.coords(self.canvas_id, coords)
            self.parent.add_dots_new_for_all_wires()
            if how_to_move_the_signal_name=="not":
                delta_x_for_signalname = 0
                delta_y_for_signalname = 0
            elif how_to_move_the_signal_name=="move_x":
                delta_y_for_signalname = 0 # Ignore the movement of the wire end in y direction.
            elif how_to_move_the_signal_name=="move_y":
                delta_x_for_signalname = 0 # Ignore the movement of the wire end in x direction.
            self.parent.move_signal_name(delta_x_for_signalname, delta_y_for_signalname)
            wire_start_point_is_moved = bool(x_coordinate_to_change[ 0] is True or y_coordinate_to_change[ 0] is True)
            wire_end_point_is_moved   = bool(y_coordinate_to_change[-1] is True or y_coordinate_to_change[-1] is True)
            if wire_start_point_is_moved:
                self.__change_signal_name_if_connected_to_other_wire(coords[0], coords[1])
            if wire_end_point_is_moved:
                self.__change_signal_name_if_connected_to_other_wire(coords[-2], coords[-1])
            self.parent.store_item(push_design_to_stack=True, signal_design_change=True)

    def __change_signal_name_if_connected_to_other_wire(self, wire_coords_x, wire_coords_y):
        signal_name_reference_of_other_wire = self.parent.get_signal_name_reference_from_wire_under_coords(wire_coords_x, wire_coords_y)
        if signal_name_reference_of_other_wire is not None:
            signal_declaration_of_other_wire = signal_name_reference_of_other_wire.get_declaration()
            signal_name_reference_of_this_wire = self.parent.get_signal_name_reference()
            signal_name_reference_of_this_wire.set_declaration_if_signal_names_differ(signal_declaration_of_other_wire)

    def __move_modified_coordinates_to_the_grid(self, coords, x_coordinate_to_change, y_coordinate_to_change):
        new_x = new_y = 0
        for number in range(len(coords)//2):
            if x_coordinate_to_change[number] is True:
                new_x = coords[2*number  ]
            if y_coordinate_to_change[number] is True:
                new_y = coords[2*number+1]
        remainder_x = new_x % self.window.design.get_grid_size() # "%" always returns a remainder which has the same sign as the denominator.
        remainder_y = new_y % self.window.design.get_grid_size() # This means: remainder_x, remainder_y are always positive.
        delta_x = - remainder_x                            # This means: delta_x, delta_y are always negative.
        delta_y = - remainder_y
        if remainder_x>self.window.design.get_grid_size()/2:
            delta_x += self.window.design.get_grid_size()        # This means: round to "bigger" numbers
        if remainder_y>self.window.design.get_grid_size()/2:
            delta_y += self.window.design.get_grid_size()        # This means: round to "bigger" numbers
        for number in range(len(coords)//2):
            if x_coordinate_to_change[number] is True:
                coords[2*number  ] += delta_x
            if y_coordinate_to_change[number] is True:
                coords[2*number+1] += delta_y
        return coords, delta_x, delta_y
