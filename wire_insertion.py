""" 
Implement a wire in the schematic:
When created, each Wire gets a tag ("wire_<number>", also stored in self.wire_tag). This tag is handed over to the
signal_name object (the signal_name must be also an object, as a "selection" expects each Canvas object to have its own reference).
The signal_name uses the tag "wire_<number>" to draw a dotted line from the wire to the signal_name, when the signal_name is moved.
The signal_name uses the tag "wire_<number>" to reconfigure the thickness of the wire, when a change of the signal_name indicates,
that the wire was changed from bus to single signal or vice versa.
When the design is stored (at stack or in a file) the wire object together with its tag is stored.
When the design is stored (at stack or in a file) the signal_name object together with the handed over wire-tag information is stored.
So when a design is restored (from stack or from file), the wire object is recreated and tagged with the stored tag.
Also the signal_name object is restored together with the wire-tag information.
In order to prevent the creation of an identical wire tag during further editing, also the wire_id is stored and later recreated.
"""
from tkinter import messagebox
import tkinter as tk
import dot_insertion
import signal_name
import wire_move
import listbox_animated
import wire_highlight

class Wire():
    wire_insertion_is_running = False
    def __init__(self,
                 root,
                 window,      #: schematic_window.SchematicWindow,
                 diagram_tab, #: notebook_diagram_tab.NotebookDiagramTab,
                 coords=(0, 0), tags=(), arrow="none", width=3):
        self.root = root
        self.window      = window
        self.diagram_tab = diagram_tab
        if tags in ["adding_signal_stubs", ()]:
            self.wire_tag = "wire_" + str(self.window.design.get_wire_id())
            self.window.design.inc_wire_id()
            if tags=="adding_signal_stubs":
                wire_tags_for_draw_at_location = [self.wire_tag]
            else:
                wire_tags_for_draw_at_location = None
        else:
            for tag in tags:
                if tag.startswith("wire_"):
                    self.wire_tag = tag
            wire_tags_for_draw_at_location = tags
        self.canvas_id                = 0
        self.color                    = "black"
        self.start_dot                = None # Reference to a Canvas-Item with type "oval"
        self.end_dot                  = None # Reference to a Canvas-Item with type "oval"
        self.wire_direction           = "horizontal"
        self.event_x                  = 0
        self.event_y                  = 0
        self.canvas_bindings_are_disabled_by_enter = False
        self.endpoints_connected_at_symbol_move = None
        self.segment_direction_at_symbol_move   = None
        self.signal_name_showed_at_enter = 0
        self.wire_bind_funcid_button  = None
        self.wire_bind_funcid_cbutton = None
        self.wire_bind_funcid_sbutton = None
        self.wire_bind_funcid_enter   = None
        self.wire_bind_funcid_leave   = None
        self.wire_bind_funcid_menu    = None
        self.funcid_delete            = None
        self.funcid_button            = None
        self.funcid_motion            = None
        self.funcid_button_release    = None
        self.funcid_dbutton           = None
        self.funcid_leave             = None
        self.funcid_escape            = None
        self.menu_entry_list          = tk.StringVar()
        self.after_identifier         = None
        self.background_rectangle     = None
        menu_string1 = (
            r"""Highlight\ net
                Highlight\ net\ through\ hierarchy
                Remove\ highlighting\ of\ net
                Remove\ all\ highlighting
            """)
        self.menu_entry_list.set(menu_string1)
        if tags==():
            Wire.wire_insertion_is_running = True
            self.diagram_tab.remove_canvas_bindings()
            self.__create_bindings_for_wire_insertion_at_canvas(width)
            self.window.config(cursor="cross")
        else:
            self.__draw_at_location(coords, wire_tags_for_draw_at_location, arrow, width)

    def __start_wire(self, event, width):
        self.diagram_tab.canvas.itemconfigure("all", state="disabled") # No widget at the canvas will now react to mouse clicks (which are needed for the wire).
        start_x = self.diagram_tab.canvas.canvasx(event.x, gridspacing=self.window.design.get_grid_size())
        start_y = self.diagram_tab.canvas.canvasy(event.y, gridspacing=self.window.design.get_grid_size())
        self.canvas_id = self.diagram_tab.canvas.create_line(start_x, start_y, start_x, start_y, start_x, start_y, width=width, fill="red",
                                                             tags=(self.wire_tag, "schematic-element")) #, activefill="red")
        self.funcid_button = self.diagram_tab.canvas.bind("<Button-1>", self.__toogle_direction)
    def __toogle_direction(self, event):
        event_x = self.diagram_tab.canvas.canvasx(event.x, gridspacing=self.window.design.get_grid_size())
        event_y = self.diagram_tab.canvas.canvasy(event.y, gridspacing=self.window.design.get_grid_size())
        new_coords = [event_x, event_y]
        wire_coords = self.diagram_tab.canvas.coords(self.canvas_id)
        wire_coords.extend(new_coords)
        self.diagram_tab.canvas.coords(self.canvas_id, wire_coords)
        if self.wire_direction=="horizontal":
            self.wire_direction = "vertical"
        else:
            self.wire_direction = "horizontal"
    def __continue_wire(self, event):
        event_x = self.diagram_tab.canvas.canvasx(event.x, gridspacing=self.window.design.get_grid_size())
        event_y = self.diagram_tab.canvas.canvasy(event.y, gridspacing=self.window.design.get_grid_size())
        wire_coords = self.diagram_tab.canvas.coords(self.canvas_id)
        if wire_coords!=[]: # An empty list is caused by motion before the wire is inserted.
            if self.wire_direction=="horizontal":
                wire_coords[-4] = event_x
                wire_coords[-2] = event_x
                wire_coords[-1] = event_y
            else:
                wire_coords[-3] = event_y
                wire_coords[-2] = event_x
                wire_coords[-1] = event_y
            self.diagram_tab.canvas.coords(self.canvas_id, wire_coords)
    def __end_wire(self, width):
        wire_coords = self.diagram_tab.canvas.coords(self.canvas_id)
        if wire_coords!=[]: # A three-click at button-1 creates a new wire-object and calls immediately __end_wire() with empty wire_coords.
            if self.__wire_is_connected_to_2_wires(wire_coords):
                messagebox.showerror("Error in HDL-SCHEM-Editor", "You have connected both ends of a wire to a wire.\nThis is not supported.")
                return
            self.diagram_tab.canvas.itemconfigure(self.canvas_id, fill="black")
            wire_coords = self.__remove_identical_wire_points (wire_coords)
            wire_coords = self.__remove_3_wire_points_in_a_row(wire_coords)
            self.diagram_tab.canvas.coords(self.canvas_id, wire_coords)
            self.__add_bindings_to_wire()
            self.add_dots_for_wire() # Here the dots are added to the new wire which is not yet stored in the design.
            self.add_dots_new_for_all_wires() # Needed, because the new wire may touch open ends of other already stored wires.
            #self.store_item(push_design_to_stack=False, signal_design_change=True) # not written to stack, because signal name is still missing
            signal_declaration = self.__get_signal_declaration_of_wire_under_dot(width)
            signal_name.SignalName(self.window.design, self.diagram_tab, # push_design_to_stack=True,
                                   coords=[wire_coords[0] + self.window.design.get_grid_size(), wire_coords[1]], angle=0,
                                   wire_tag=self.wire_tag, declaration=signal_declaration)
            self.store_item(push_design_to_stack=True, signal_design_change=True)
            self.__restore_diagram_canvas_bindings()
            self.diagram_tab.canvas.itemconfigure("all", state="normal") # Items shall react to mouse clicks and keys again.
            Wire(self.root, self.window, self.diagram_tab,  width=width) #push_design_to_stack=True,)

    def __get_signal_declaration_of_wire_under_dot(self, width):
        signal_name_reference = None
        wire_coords = self.diagram_tab.canvas.coords(self.canvas_id)
        if self.start_dot is not None:
            signal_name_reference = self.get_signal_name_reference_from_wire_under_coords(wire_coords[0], wire_coords[1])
        elif self.end_dot is not None:
            signal_name_reference = self.get_signal_name_reference_from_wire_under_coords(wire_coords[-2], wire_coords[-1])
        if signal_name_reference is not None:
            signal_declaration = signal_name_reference.get_declaration()
        else:
            if self.window.design.get_language()=="VHDL":
                if width==1:
                    signal_declaration = "signal_" + str(self.window.design.get_wire_id()) + " : std_logic"
                else:
                    signal_declaration = "signal_" + str(self.window.design.get_wire_id()) + " : std_logic_vector(7 downto 0)"
            else:
                if width==1:
                    signal_declaration = "wire signal_" + str(self.window.design.get_wire_id())
                else:
                    signal_declaration = "wire [7:0] signal_" + str(self.window.design.get_wire_id())
        return signal_declaration

    def get_signal_name_reference_from_wire_under_coords(self, wire_end_coord_1, wire_end_coord_2):
        signal_name_reference = None
        overlapping_ids = self.diagram_tab.canvas.find_overlapping(wire_end_coord_1-1, wire_end_coord_2-1, wire_end_coord_1+1, wire_end_coord_2+1)
        for canvas_id in overlapping_ids:
            if canvas_id!=self.canvas_id and self.diagram_tab.canvas.type(canvas_id)=="line" and "grid_line" not in self.diagram_tab.canvas.gettags(canvas_id):
                signal_name_reference = self.__get_signal_name_reference_by_canvas_id(canvas_id)
        return signal_name_reference

    def __get_signal_name_reference_by_canvas_id(self, canvas_id):
        tag_of_signal_name = self.diagram_tab.canvas.gettags(canvas_id)[0] + "_signal_name"
        canvas_id_of_signal_name = self.diagram_tab.canvas.find_withtag(tag_of_signal_name)[0]
        signal_name_reference = self.window.design.get_references([canvas_id_of_signal_name])[0]
        return signal_name_reference

    def get_signal_name_reference(self):
        return self.__get_signal_name_reference_by_canvas_id(self.canvas_id)

    def __wire_is_connected_to_2_wires(self, wire_coords):
        end_points = [[wire_coords[0], wire_coords[1]], [wire_coords[-2], wire_coords[-1]]]
        connected_to_wire = False
        for end_point in end_points:
            overlapping_canvas_ids = self.diagram_tab.canvas.find_overlapping(end_point[0]-1, end_point[1]-1, end_point[0]+1, end_point[1]+1)
            for canvas_id in overlapping_canvas_ids:
                if canvas_id!=self.canvas_id and self.diagram_tab.canvas.type(canvas_id)=="line" and "grid_line" not in self.diagram_tab.canvas.gettags(canvas_id):
                    if connected_to_wire is True:
                        return True
                    connected_to_wire = True
        return False

    def add_dots_for_wire(self):
        coords = self.diagram_tab.canvas.coords(self.canvas_id)
        self.start_dot = self.__add_dot_if_needed_at(coords[ 0], coords[ 1])
        self.end_dot   = self.__add_dot_if_needed_at(coords[-2], coords[-1])

    def __add_dot_if_needed_at(self, dot_x, dot_y):
        overlapping_ids = self.diagram_tab.canvas.find_overlapping(dot_x, dot_y, dot_x, dot_y)
        dot_found  = False
        line_found = 0
        for canvas_id in overlapping_ids:
            if self.diagram_tab.canvas.type(canvas_id)=="oval":
                dot_found = True
            elif self.diagram_tab.canvas.type(canvas_id)=="line" and "grid_line" not in self.diagram_tab.canvas.gettags(canvas_id):
                line_found += 1
                line_size = self.diagram_tab.canvas.itemcget(canvas_id,"width")
        if line_found>1 and not dot_found:
            return dot_insertion.Dot(self.window, push_design_to_stack=False, coords=[dot_x, dot_y], line_size=line_size)
        return None

    def __remove_identical_wire_points(self, wire_coords):
        wire_coords_mod = []
        wire_coords_mod.append(wire_coords[0])
        wire_coords_mod.append(wire_coords[1])
        for index in range(len(wire_coords)//2 - 1):
            if not (
                abs(wire_coords[2*index+2] - wire_coords[2*index]  )<self.window.design.get_grid_size()/10 and
                abs(wire_coords[2*index+3] - wire_coords[2*index+1])<self.window.design.get_grid_size()/10
                ):
                wire_coords_mod.append(wire_coords[2*index+2])
                wire_coords_mod.append(wire_coords[2*index+3])
        return wire_coords_mod

    def __remove_3_wire_points_in_a_row(self, wire_coords):
        wire_coords_mod = []
        wire_coords_mod.append(wire_coords[0])
        wire_coords_mod.append(wire_coords[1])
        for index in range(len(wire_coords)//2 - 2):
            if not ((abs(wire_coords[2*index  ] - wire_coords[2*index+2])<self.window.design.get_grid_size()/10 and
                     abs(wire_coords[2*index+2] - wire_coords[2*index+4])<self.window.design.get_grid_size()/10) or
                    (abs(wire_coords[2*index+1] - wire_coords[2*index+3])<self.window.design.get_grid_size()/10 and
                     abs(wire_coords[2*index+3] - wire_coords[2*index+5])<self.window.design.get_grid_size()/10)
                    ):
                wire_coords_mod.append(wire_coords[2*index+2])
                wire_coords_mod.append(wire_coords[2*index+3])
        wire_coords_mod.append(wire_coords[-2])
        wire_coords_mod.append(wire_coords[-1])
        return wire_coords_mod

    def __draw_at_location(self, coords, tags, arrow, width):
        if "layer2" not in tags:
            tags.append("layer2")
        if "schematic-element" not in tags:
            tags.append("schematic-element")
        self.canvas_id = self.diagram_tab.canvas.create_line(*coords, tags=tags, width=width, arrow=arrow, activefill="red")
        self.__add_bindings_to_wire()
        self.store_item(push_design_to_stack=False, signal_design_change=False)
        self.diagram_tab.sort_layers()

    def signal_name_near_segment(self, segment_to_move, wire_coords): # segment_to_move = 0, 1, 2, ...
        segment_coords = wire_coords[2*segment_to_move:2*segment_to_move+4]
        # Sort the points of the segment in an ascending order:
        new_segment_coords = [0, 0, 0, 0]
        if (segment_coords[0]-segment_coords[2]>self.window.design.get_grid_size()/2 or # horizontal with wrong order
            segment_coords[1]-segment_coords[3]>self.window.design.get_grid_size()/2):  # vertical with wrong order
            new_segment_coords[0] = segment_coords[2]
            new_segment_coords[1] = segment_coords[3]
            new_segment_coords[2] = segment_coords[0]
            new_segment_coords[3] = segment_coords[1]
        else:
            new_segment_coords = segment_coords
        signal_name_anchor = self.diagram_tab.canvas.coords(self.wire_tag + "_signal_name")
        # Check if the anchor of the signal_name is in a window around the segment:
        if (new_segment_coords[0]-self.diagram_tab.design.get_grid_size()<=signal_name_anchor[0]<=new_segment_coords[2]+self.diagram_tab.design.get_grid_size() and
            new_segment_coords[1]-self.diagram_tab.design.get_grid_size()<=signal_name_anchor[1]<=new_segment_coords[3]+self.diagram_tab.design.get_grid_size()):
            return True
        return False

    def __signal_name_near_wire_end_point(self, segment_to_move, wire_coords, first_or_last): # segment_to_move = 0, 1, 2, ...
        segment_coords = wire_coords[2*segment_to_move:2*segment_to_move+4]
        # Sort the points of the segment in an ascending order:
        signal_name_anchor = self.diagram_tab.canvas.coords(self.wire_tag + "_signal_name")
        # Check if the anchor of the signal_name is in a window around the moved end point:
        if ((first_or_last=="first" and
            segment_coords[0]-self.diagram_tab.design.get_grid_size()<=signal_name_anchor[0]<=segment_coords[0]+self.diagram_tab.design.get_grid_size() and
            segment_coords[1]-self.diagram_tab.design.get_grid_size()<=signal_name_anchor[1]<=segment_coords[1]+self.diagram_tab.design.get_grid_size()) or
            (first_or_last=="last" and
            segment_coords[2]-self.diagram_tab.design.get_grid_size()<=signal_name_anchor[0]<=segment_coords[2]+self.diagram_tab.design.get_grid_size() and
            segment_coords[3]-self.diagram_tab.design.get_grid_size()<=signal_name_anchor[1]<=segment_coords[3]+self.diagram_tab.design.get_grid_size())):
            return True
        return False

    def determine_connected_endpoints(self, wire_coords):
        # Here distances are compared against the grid_size. When the design elements are very small (because of view all),
        # "things" are connected even if the distance is more than half of the grid size. The used factor 0.6 was determined by trial and error.
        end_point_connected = "none"
        overlapping_ids = self.diagram_tab.canvas.find_overlapping(wire_coords[0]-0.6*self.window.design.get_grid_size(), wire_coords[1]-0.6*self.window.design.get_grid_size(),
                                                                   wire_coords[0]+0.6*self.window.design.get_grid_size(), wire_coords[1]+0.6*self.window.design.get_grid_size())
        for canvas_id in overlapping_ids:
            if canvas_id!=self.canvas_id:
                if self.diagram_tab.canvas.type(canvas_id)=="line" and "grid_line" not in self.diagram_tab.canvas.gettags(canvas_id):
                    end_point_connected = "first"
                elif self.diagram_tab.canvas.type(canvas_id)=="polygon":
                    polygon_coords = self.diagram_tab.canvas.coords(canvas_id)
                    if (abs(wire_coords[0]-polygon_coords[0])<=0.6*self.window.design.get_grid_size() and
                        abs(wire_coords[1]-polygon_coords[1])<=0.6*self.window.design.get_grid_size()): # Check if the wire ends at the connection-point of the polygon.
                        end_point_connected = "first"
                elif self.diagram_tab.canvas.type(canvas_id)=="rectangle" and self.window.design.get_schematic_element_type_of(canvas_id)=="block-rectangle":
                    end_point_connected = "first"
        overlapping_ids = self.diagram_tab.canvas.find_overlapping(wire_coords[-2]-0.6*self.window.design.get_grid_size(), wire_coords[-1]-0.6*self.window.design.get_grid_size(),
                                                                   wire_coords[-2]+0.6*self.window.design.get_grid_size(), wire_coords[-1]+0.6*self.window.design.get_grid_size())
        for canvas_id in overlapping_ids:
            if canvas_id!=self.canvas_id:
                if self.diagram_tab.canvas.type(canvas_id)=="line" and "grid_line" not in self.diagram_tab.canvas.gettags(canvas_id):
                    if end_point_connected=="none":
                        end_point_connected = "last"
                        # A line may overlap with both rectangle and polygon. This is okay.
                        # But as the check for "none" is used as a flag here, the loop must be stopped after the first hit:
                        break
                elif self.diagram_tab.canvas.type(canvas_id)=="polygon":
                    # if end_point_connected=="none":
                    #     polygon_coords = self.diagram_tab.canvas.coords(canvas_id)
                    #     if (abs(wire_coords[-2]-polygon_coords[0])<=0.6*self.window.design.get_grid_size() and
                    #         abs(wire_coords[-1]-polygon_coords[1])<=0.6*self.window.design.get_grid_size()):
                    #         end_point_connected = "last"
                    #     # A line may overlap with both rectangle and polygon. This is okay.
                    #     # But as the check for "none" is used as a flag here, the loop must be stopped after the first hit:
                    #     break
                    # end_point_connected = "both"
                    polygon_coords = self.diagram_tab.canvas.coords(canvas_id)
                    if (abs(wire_coords[-2]-polygon_coords[0])<=0.6*self.window.design.get_grid_size() and
                        abs(wire_coords[-1]-polygon_coords[1])<=0.6*self.window.design.get_grid_size()):
                        if end_point_connected=="none":
                            end_point_connected = "last"
                            # A line may overlap with both rectangle and polygon. This is okay.
                            # But as the check for "none" is used as a flag here, the loop must be stopped after the first hit:
                            break
                        end_point_connected = "both"
                elif self.diagram_tab.canvas.type(canvas_id)=="rectangle" and self.window.design.get_schematic_element_type_of(canvas_id)=="block-rectangle":
                    if end_point_connected=="none":
                        end_point_connected = "last"
                        # A line may overlap with both rectangle and polygon. This is okay.
                        # But as the check for "none" is used as a flag here, the loop must be stopped after the first hit:
                        break
                    end_point_connected = "both"
        return end_point_connected

    def move_wire_end_point(self, movement_phase, first_or_last, delta_x, delta_y): # This method is used, when symbols with connected wires are moved.
        wire_coords = self.diagram_tab.canvas.coords(self.canvas_id)
        if first_or_last=="first":
            segment_to_move = 0
        else:
            segment_to_move = len(wire_coords)//2 - 2
        if self.__signal_name_near_wire_end_point(segment_to_move, wire_coords, first_or_last):
            move_the_signal_name = True
        else:
            move_the_signal_name = False
        if self.endpoints_connected_at_symbol_move is None: # True at each first call of move_wire_end_point for a moving.
            self.endpoints_connected_at_symbol_move = self.determine_connected_endpoints(wire_coords) # May have values: "first", "last", "both"
            # This check only works correctly at the start of the moving:
            if ((first_or_last=="first" and abs(wire_coords[ 0] - wire_coords[ 2])<self.window.design.get_grid_size()/10) or
                (first_or_last=="last"  and abs(wire_coords[-4] - wire_coords[-2])<self.window.design.get_grid_size()/10)):
                self.segment_direction_at_symbol_move = "vertical"
            else:
                self.segment_direction_at_symbol_move = "horizontal"
        if len(wire_coords)==4: # The wire is a straight line.
            if self.endpoints_connected_at_symbol_move!="both": # A straight line with one open end is connected to a symbol, so both ends must be moved.
                wire_coords[0] += delta_x
                wire_coords[1] += delta_y
                wire_coords[2] += delta_x
                wire_coords[3] += delta_y
                move_the_signal_name = True # Because both wire ends are moved, the signalname must also be moved (even if signalname is not near wire end point).
            else: # end_point_connected=="both"
                if first_or_last=="first":
                    wire_coords[len(wire_coords):] = wire_coords[-2:] # duplicate last point of the wire.
                    wire_coords[len(wire_coords):] = wire_coords[-2:] # duplicate again last point of the wire.
                    wire_coords[0] += delta_x
                    wire_coords[1] += delta_y
                    if self.segment_direction_at_symbol_move=="horizontal":
                        if wire_coords[0]<wire_coords[2]:
                            wire_coords[4] -= self.window.design.get_grid_size()
                            wire_coords[2] -= self.window.design.get_grid_size()
                        else:
                            wire_coords[4] += self.window.design.get_grid_size()
                            wire_coords[2] += self.window.design.get_grid_size()
                        wire_coords[3] += delta_y
                    else:
                        if wire_coords[1]<wire_coords[3]:
                            wire_coords[5] -= self.window.design.get_grid_size()
                            wire_coords[3] -= self.window.design.get_grid_size()
                        else:
                            wire_coords[5] += self.window.design.get_grid_size()
                            wire_coords[3] += self.window.design.get_grid_size()
                        wire_coords[2] += delta_x
                else: # first_or_last=="last"
                    wire_coords[:0] = wire_coords[0:2] # duplicate first point of the wire.
                    wire_coords[:0] = wire_coords[0:2] # duplicate againfirst point of the wire.
                    wire_coords[6] += delta_x
                    wire_coords[7] += delta_y
                    if self.segment_direction_at_symbol_move=="horizontal":
                        if wire_coords[4]<wire_coords[6]:
                            wire_coords[2] += self.window.design.get_grid_size()
                            wire_coords[4] += self.window.design.get_grid_size()
                        else:
                            wire_coords[2] -= self.window.design.get_grid_size()
                            wire_coords[4] -= self.window.design.get_grid_size()
                        wire_coords[5] += delta_y
                    else:
                        if wire_coords[5]<wire_coords[7]:
                            wire_coords[3] += self.window.design.get_grid_size()
                            wire_coords[5] += self.window.design.get_grid_size()
                        else:
                            wire_coords[3] -= self.window.design.get_grid_size()
                            wire_coords[5] -= self.window.design.get_grid_size()
                        wire_coords[4] += delta_x
        else: # A end segment of a wire with more than 3 points is moved.
            if first_or_last=="first":
                wire_coords[0] += delta_x
                wire_coords[1] += delta_y
                if self.segment_direction_at_symbol_move=="horizontal":
                    wire_coords[3] += delta_y
                else:
                    wire_coords[2] += delta_x
            else: #first_or_last=="last"
                wire_coords[-2] += delta_x
                wire_coords[-1] += delta_y
                if self.segment_direction_at_symbol_move=="horizontal":
                    wire_coords[-3] += delta_y
                else:
                    wire_coords[-4] += delta_x
        if move_the_signal_name:
            self.move_signal_name(delta_x, delta_y)
        if movement_phase!="last_time":
            self.diagram_tab.canvas.coords(self.canvas_id, wire_coords)
        else:
            wire_coords = self.remove_unnecessary_points(wire_coords)
            self.endpoints_connected_at_symbol_move = None
            self.diagram_tab.canvas.coords(self.canvas_id, wire_coords)
            self.add_dots_new_for_all_wires()
            self.store_item(push_design_to_stack=False, signal_design_change=True) # No push to stack, as the moved symbol will create a new entry there.

    def move_signal_name(self, delta_x, delta_y):
        canvas_id_signal_name = self.diagram_tab.canvas.find_withtag(self.wire_tag + "_signal_name")
        self.diagram_tab.canvas.move(canvas_id_signal_name, delta_x, delta_y)
        ref = self.window.design.get_references(canvas_id_signal_name)[0]
        ref.store_item(push_design_to_stack=False, signal_design_change=False)

    def remove_unnecessary_points(self, coords):
        coords_in_grid_size = [coord/self.window.design.get_grid_size() for coord in coords]
        new_coords = []
        new_coords.append(coords[0])
        new_coords.append(coords[1])
        if len(coords)>=6:
            for index in range(len(coords)//2-2):
                if not (
                    (abs(coords_in_grid_size[2*index  ]-coords_in_grid_size[2*index+2])<0.1 and abs(coords_in_grid_size[2*index+2]-coords_in_grid_size[2*index+4])<0.1) or
                    (abs(coords_in_grid_size[2*index+1]-coords_in_grid_size[2*index+3])<0.1 and abs(coords_in_grid_size[2*index+3]-coords_in_grid_size[2*index+5])<0.1)
                    ):
                    new_coords.append(coords[2*index+2])
                    new_coords.append(coords[2*index+3])
            new_coords.append(coords[-2])
            new_coords.append(coords[-1])
            return new_coords
        return coords

    def add_dots_new_for_all_wires(self):
        list_of_canvas_wire_references = self.window.design.get_list_of_canvas_wire_references()
        for wire_reference in list_of_canvas_wire_references:
            wire_reference.remove_dots()
            wire_reference.add_dots_for_wire()

    def __reject_wire(self):
        self.__restore_diagram_canvas_bindings()
        self.remove_dots()
        self.diagram_tab.canvas.focus_set() # needed to catch Ctrl-z
        self.diagram_tab.canvas.delete(self.canvas_id)
        self.diagram_tab.canvas.itemconfigure("all", state="normal") # Items shall react to mouse clicks and keys again.
        Wire.wire_insertion_is_running = False
        del self # Once the last reference to an object is deleted, the object will be removed by garbage collection.

    def __restore_diagram_canvas_bindings(self):
        self.__remove_bindings_for_wire_insertion_at_canvas()
        self.window.config(cursor="arrow")
        self.diagram_tab.create_canvas_bindings()

    def __create_bindings_for_wire_insertion_at_canvas(self, width):
        self.funcid_button  = self.diagram_tab.canvas.bind("<Button-1>"       , lambda event: self.__start_wire(event, width))
        self.funcid_motion  = self.diagram_tab.canvas.bind("<Motion>"         , self.__continue_wire)
        self.funcid_dbutton = self.diagram_tab.canvas.bind("<Double-Button-1>", lambda event: self.__end_wire(width))
        self.funcid_leave   = self.diagram_tab.canvas.bind("<Leave>"          , lambda event: self.__reject_wire())
        self.funcid_escape  = self.window.bind            ("<Escape>"         , lambda event: self.__reject_wire())

    def __remove_bindings_for_wire_insertion_at_canvas(self):
        self.diagram_tab.canvas.unbind("<Button-1>"       , self.funcid_button )
        self.diagram_tab.canvas.unbind("<Motion>"         , self.funcid_motion )
        self.diagram_tab.canvas.unbind("<Double-Button-1>", self.funcid_dbutton)
        self.diagram_tab.canvas.unbind("<Leave>"          , self.funcid_leave  )
        self.window.unbind            ("<Escape>"         , self.funcid_escape )
        self.funcid_button  = None
        self.funcid_motion  = None
        self.funcid_dbutton = None
        self.funcid_leave   = None
        self.funcid_escape  = None

    def select_item(self):
        self.__highlight()
        self.__remove_bindings_from_wire()

    def unselect_item(self):
        self.__unhighlight()
        self.__add_bindings_to_wire()

    def __highlight(self):
        self.color = self.diagram_tab.canvas.itemcget(self.canvas_id, "fill")
        self.diagram_tab.canvas.itemconfigure(self.canvas_id, fill="red")

    def __unhighlight(self):
        self.diagram_tab.canvas.itemconfigure(self.canvas_id, fill=self.color)

    def __add_bindings_to_wire(self):
        # When shift_was_pressed=True:
        # 1. Wires can be disconnected from symbol pins.
        # 2. A new segment can be added to an open wire end.
        self.wire_bind_funcid_button  = self.diagram_tab.canvas.tag_bind(self.canvas_id, "<Button-1>"        , lambda event:
                                            wire_move.WireMove(event, self.window, self.diagram_tab, self, self.canvas_id, self.wire_tag, shift_was_pressed=False))
        self.wire_bind_funcid_cbutton = self.diagram_tab.canvas.tag_bind(self.canvas_id, "<Shift-Button-1>"  , lambda event:
                                            wire_move.WireMove(event, self.window, self.diagram_tab, self, self.canvas_id, self.wire_tag, shift_was_pressed=True))
        self.wire_bind_funcid_sbutton = self.diagram_tab.canvas.tag_bind(self.canvas_id, "<Shift-Button-3>"  , lambda event: self.__add_arrow())
        self.wire_bind_funcid_enter   = self.diagram_tab.canvas.tag_bind(self.canvas_id, "<Enter>"           , self.__at_enter)
        self.wire_bind_funcid_leave   = self.diagram_tab.canvas.tag_bind(self.canvas_id, "<Leave>"           , lambda event: self.__at_leave())
        self.wire_bind_funcid_menu    = self.diagram_tab.canvas.tag_bind(self.canvas_id, "<Button-3>"        , self.__show_menu)

    def __remove_bindings_from_wire(self):
        if self.wire_bind_funcid_button is not None:
            self.diagram_tab.canvas.tag_unbind(self.canvas_id, "<Button-1>"        , self.wire_bind_funcid_button)
        if self.wire_bind_funcid_sbutton is not None:
            self.diagram_tab.canvas.tag_unbind(self.canvas_id, "<Control-Button-1>", self.wire_bind_funcid_cbutton)
        if self.wire_bind_funcid_enter is not None:
            self.diagram_tab.canvas.tag_unbind(self.canvas_id, "<Shift-Button-1>"  , self.wire_bind_funcid_sbutton)
        if self.wire_bind_funcid_enter is not None:
            self.diagram_tab.canvas.tag_unbind(self.canvas_id, "<Enter>"           , self.wire_bind_funcid_enter)
        if self.wire_bind_funcid_leave is not None:
            self.diagram_tab.canvas.tag_unbind(self.canvas_id, "<Leave>"           , self.wire_bind_funcid_leave)
        self.wire_bind_funcid_button  = None
        self.wire_bind_funcid_sbutton = None
        self.wire_bind_funcid_enter   = None
        self.wire_bind_funcid_enter   = None
        self.wire_bind_funcid_leave   = None

    def __at_enter(self, event):
        # if self.window.config()["cursor"][-1]=="arrow": # In all other cases a user action is active which already has overwritten the bindings.
        #     self.diagram_tab.remove_canvas_bindings()   # This removing would then destroy the bindings of the user action.
        if not self.diagram_tab.canvas.find_withtag("selected"):
            self.__highlight()
            for canvas_id in self.diagram_tab.canvas.find_withtag(self.wire_tag):
                if self.diagram_tab.canvas.type(canvas_id)=="text":
                    self.after_identifier = self.diagram_tab.canvas.after(2000, lambda event=event, canvas_id=canvas_id : self.__show_signal_declaration(event, canvas_id))
            # Wenn placing connectors at wires, the wire is sometimes entered, when the mouse click for placing the connector happens.
            # If then the canvas-mapping is deactivated, the connector cannot be placed anymore.
            # So it is a bad idea to remove the binding:
            # self.diagram_tab.remove_canvas_bindings() # prevents the selection rectangle from showing up at wire movements with the left mouse button.
            self.diagram_tab.canvas.focus_set()
            self.funcid_delete = self.diagram_tab.canvas.bind("<Delete>", lambda event: self.delete_item(push_design_to_stack=True))

    def __show_signal_declaration(self, event, canvas_id):
        if self.diagram_tab.design.get_declaration_of_signal_name(canvas_id) is not None: # Check needed, because of the delay the signal might be deleted in the meantime.
            self.signal_name_showed_at_enter = self.diagram_tab.canvas.create_text(self.diagram_tab.canvas.canvasx(event.x)+self.diagram_tab.design.get_grid_size(),
                                                                                self.diagram_tab.canvas.canvasy(event.y)-self.diagram_tab.design.get_grid_size(),
                                                                                anchor=tk.SW,
                                                                                text=self.diagram_tab.design.get_declaration_of_signal_name(canvas_id))
            self.background_rectangle = self.diagram_tab.canvas.create_rectangle(self.diagram_tab.canvas.bbox(self.signal_name_showed_at_enter), fill="white")
            self.diagram_tab.canvas.tag_lower(self.background_rectangle, self.signal_name_showed_at_enter)

    def __at_leave(self):
        # if self.window.config()["cursor"][-1]=="arrow":
        #     self.diagram_tab.create_canvas_bindings()
        self.__unhighlight()
        if self.after_identifier is not None:
            self.diagram_tab.canvas.after_cancel(self.after_identifier)
            self.diagram_tab.canvas.delete(self.signal_name_showed_at_enter)
            self.diagram_tab.canvas.delete(self.background_rectangle)
        self.__restore_delete_binding()

    def __restore_delete_binding(self):
        if self.funcid_delete is not None:
            self.diagram_tab.canvas.unbind("<Delete>", self.funcid_delete)
            self.funcid_delete = None
            self.diagram_tab.canvas.bind("<Delete>", lambda event: self.diagram_tab.delete_selection())

    def delete_item(self, push_design_to_stack):
        self.__restore_delete_binding()
        canvas_id_signal_name = self.diagram_tab.canvas.find_withtag(self.wire_tag + "_signal_name")[0]
        reference_signal_name = self.window.design.get_references([canvas_id_signal_name])[0]
        reference_signal_name.delete_item(push_design_to_stack=False)
        self.window.design.remove_canvas_item_from_dictionary(self.canvas_id, push_design_to_stack)
        self.diagram_tab.canvas.delete(self.canvas_id)
        self.remove_dots()
        self.add_dots_new_for_all_wires() # necessary, because remaining wires may have a start/end-dot to the removed wire.
        self.diagram_tab.canvas.delete(self.signal_name_showed_at_enter) # Needed when the wire is deleted during the time the signal name is shown.
        self.diagram_tab.canvas.delete(self.background_rectangle)
        self.diagram_tab.create_canvas_bindings() # Needed because when "self" is deleted after entering the symbol, no __at_leave will take place.
        del self # Once the last reference to an object is deleted, the object will be removed by garbage collection.

    def store_item(self, push_design_to_stack, signal_design_change):
        coords = self.diagram_tab.canvas.coords  (self.canvas_id)
        tags   = self.diagram_tab.canvas.gettags (self.canvas_id)
        arrow  = self.diagram_tab.canvas.itemcget(self.canvas_id, "arrow")
        width  = self.diagram_tab.canvas.itemcget(self.canvas_id, "width")
        self.window.design.store_wire_in_canvas_dictionary(self.canvas_id, self, coords, tags, arrow, width, push_design_to_stack, signal_design_change)

    def remove_dots(self):
        self.__remove_start_dot()
        self.__remove_end_dot()

    def __remove_start_dot(self):
        if self.start_dot is not None:
            self.start_dot.delete_item(push_design_to_stack=False)
            self.start_dot = None

    def __remove_end_dot(self):
        if self.end_dot is not None:
            self.end_dot.delete_item(push_design_to_stack=False)
            self.end_dot = None

    def __add_arrow(self):
        arrow = self.diagram_tab.canvas.itemcget(self.canvas_id, "arrow")
        if   arrow=="none":
            new_arrow="first"
        elif arrow=="first":
            new_arrow="last"
        elif arrow=="last":
            new_arrow="none"
        self.diagram_tab.canvas.itemconfigure(self.canvas_id, arrow=new_arrow)
        self.store_item(push_design_to_stack=True, signal_design_change=True)

    def get_object_tag(self):
        return self.wire_tag # "wire_<number>"

    def __show_menu(self, event):
        menu = listbox_animated.ListboxAnimated(self.diagram_tab.canvas, listvariable=self.menu_entry_list, height=4,
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
        if 'Remove all highlighting' in selected_entry and wire_highlight.WireHighlight.highlight_object is not None:
            wire_highlight.WireHighlight.highlight_object.unhighlight_all_and_delete_object()
        elif 'Remove highlighting of net' in selected_entry and wire_highlight.WireHighlight.highlight_object is not None:
            wire_highlight.WireHighlight.highlight_object.unhighlight_net(self.window, self.canvas_id)
        elif "Highlight net through hierarchy" in selected_entry:
            if wire_highlight.WireHighlight.highlight_object is None:
                wire_highlight.WireHighlight(self.root)
            wire_highlight.WireHighlight.highlight_object.add_to_highlight(self.window, self.canvas_id, "hierarchical")
        elif 'Highlight net' in selected_entry:
            if wire_highlight.WireHighlight.highlight_object is None:
                wire_highlight.WireHighlight(self.root)
            wire_highlight.WireHighlight.highlight_object.add_to_highlight(self.window, self.canvas_id, "flat")
        self.__close_menu(menue_window, menu)

    def __close_menu(self, menue_window, menu):
        menu.destroy()
        self.diagram_tab.canvas.delete(menue_window)

    def adapt_coordinates_by_factor(self, factor):
        coords = self.diagram_tab.canvas.coords(self.canvas_id)
        coords = [value*factor for value in coords]
        self.diagram_tab.canvas.coords(self.canvas_id, coords)

    def add_pasted_tag_to_all_canvas_items(self):
        self.diagram_tab.canvas.addtag_withtag("pasted_tag", self.canvas_id)
