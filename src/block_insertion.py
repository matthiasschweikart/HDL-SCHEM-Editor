""" Class for the insertion of a blocks """
import tkinter as tk
from tkinter import messagebox
import re
import block_rectangle
import block_edit
import listbox_animated
import color_changer
import constants

class Block():
    def __init__(self,
                 window,      # : schematic_window.SchematicWindow,
                 diagram_tab, # : notebook_diagram_tab.NotebookDiagramTab,
                 # When called by button "new Block" then the following parameters are empty:
                 rect_coords=None,
                 rect_color=constants.BLOCK_DEFAULT_COLOR,
                 text_coords=None,
                 text="",
                 block_tag=None):
        self.window                    = window
        self.diagram_tab               = diagram_tab
        self.event_x                   = 0
        self.event_y                   = 0
        self.canvas_id                 = 0
        self.rectangle_canvas_id       = 0
        self.rectangle_reference       = None
        self.block_edit_ref            = None
        self.funcid_delete             = None
        self.func_id_motion            = None
        self.func_id_button            = None
        self.func_id_leave             = None
        self.func_id_escape            = None
        self.func_id_button_release    = None
        self.sym_bind_funcid_button    = None
        self.sym_bind_funcid_dbutton   = None
        self.sym_bind_funcid_enter1    = None
        self.sym_bind_funcid_leave1    = None
        self.sym_bind_funcid_enter     = None
        self.sym_bind_funcid_leave     = None
        self.sym_bind_funcid_edit_ex   = None
        self.sym_bind_funcid_edit_er   = None
        self.sym_bind_funcid_showmen1  = None
        self.sym_bind_funcid_showmen2  = None
        if block_tag is None:
            self.object_tag = "block_" + str(self.window.design.get_block_id())
            self.window.design.inc_block_id()
            self.diagram_tab.remove_canvas_bindings()
            self.window.config(cursor="cross")
            self.__create_bindings_for_insertion_at_canvas(rect_color)
        else:
            self.object_tag = block_tag
            text = self.fill_all_lines_with_blanks_to_equal_length(text)
            self.__draw_at_location(rect_coords, rect_color, text_coords, text) #, push_design_to_stack)

    def fill_all_lines_with_blanks_to_equal_length(self, text):
        lines = text.splitlines()
        max_line_length = 0
        for line in lines:
            if len(line)>max_line_length:
                max_line_length = len(line)
        new_text = ""
        for line in lines:
            line += " " * (max_line_length - len(line)) + "\n"
            new_text += line
        if text.endswith("\n"):
            return new_text
        return new_text[:-1]

    def __draw_once_at_event_location(self, event, rect_color):
        self.event_x = self.diagram_tab.canvas.canvasx(event.x)
        self.event_y = self.diagram_tab.canvas.canvasy(event.y)
        # Positions the text at a "beautiful" position inside the rectangle by subtracting half the grid size:
        self.event_x -= self.event_x%self.diagram_tab.design.get_grid_size() - self.diagram_tab.design.get_grid_size()/2
        self.event_y -= self.event_y%self.diagram_tab.design.get_grid_size() - self.diagram_tab.design.get_grid_size()/2
        if self.window.design.get_language()=="VHDL":
            text="-- Insert code by double-click or by Ctrl+e"
        else:
            text="// Insert code by double-click or by Ctrl+e"
        self.__draw(None, [self.event_x, self.event_y], rect_color, text=text)
        references_to_connected_wires = []
        self.func_id_motion = self.diagram_tab.canvas.bind("<Motion>", lambda event: self.__move_to(event, references_to_connected_wires, "middle"))

    def __draw(self, rect_coords, text_coords, rect_color, text):
        self.canvas_id = self.diagram_tab.canvas.create_text(text_coords[0], text_coords[1], text=text, anchor="nw", activefill="red",
                                                                  tags=("block-text", self.object_tag, "layer3", "schematic-element"),
                                                                  font=("Courier", self.window.design.get_font_size()))
        if rect_coords is None: # None when inserting by mouse, not None when inserting by file read.
            rect_coords = self.diagram_tab.canvas.bbox(self.canvas_id)
            rect_coords = self.__get_coords_expanded_to_grid(rect_coords)
        self.rectangle_reference = block_rectangle.BlockRectangle(self.window, self.diagram_tab, rect_coords, rect_color, self.object_tag, push_design_to_stack=False)
        self.rectangle_canvas_id = self.rectangle_reference.get_canvas_id()
        #self.diagram_tab.canvas.tag_lower(self.canvas_id          )# puts the text in the background, so that it cannot "hide" other objects by exceeding the block-rectangle
        #self.diagram_tab.canvas.tag_lower(self.rectangle_canvas_id)
        self.diagram_tab.sort_layers()

    def __get_coords_expanded_to_grid(self, enclosing_rectangle, old_height_before_zoom=0, old_width_before_zoom=0):
        new_enclosing_rectangle = list(enclosing_rectangle)
        remainder_1 = enclosing_rectangle[0]%self.window.design.get_grid_size() # Remember: the result of the %-operation gets the sign from the divisor!
        if remainder_1!=0:
            new_enclosing_rectangle[0] -= remainder_1 # increase the rectangle!
        remainder_2 = enclosing_rectangle[2]%self.window.design.get_grid_size()
        if remainder_2!=0:
            if remainder_1>remainder_2: # increase by remainder_1 is bigger than decrease by remainder_2
                new_enclosing_rectangle[2] -= remainder_2 # decrease the rectangle, but in sum an increase for the rectangle.
            else:
                new_enclosing_rectangle[2] += self.window.design.get_grid_size() - remainder_2 # increase the rectangle
        remainder_1 = enclosing_rectangle[1]%self.window.design.get_grid_size()
        if remainder_1!=0:
            new_enclosing_rectangle[1] -= remainder_1 # increase!
        remainder_2 = enclosing_rectangle[3]%self.window.design.get_grid_size()
        if remainder_2!=0:
            if remainder_1>remainder_2: # increase by remainder_1 is bigger than decrease by remainder_2
                new_enclosing_rectangle[3] -= remainder_2 # decrease!
            else:
                new_enclosing_rectangle[3] += self.window.design.get_grid_size() - remainder_2 # increase the rectangle
        # Increase to at least 2*grid_size x 2*grid_size:
        if abs(new_enclosing_rectangle[2] - new_enclosing_rectangle[0] - self.window.design.get_grid_size())<=self.window.design.get_grid_size()/10:
            new_enclosing_rectangle[2] += self.window.design.get_grid_size()
        if abs(new_enclosing_rectangle[3] - new_enclosing_rectangle[1] - self.window.design.get_grid_size())<=self.window.design.get_grid_size()/10:
            new_enclosing_rectangle[3] += self.window.design.get_grid_size()
        if old_height_before_zoom!=0: # Only true, when zoom is involved.
            new_height = (new_enclosing_rectangle[3] - new_enclosing_rectangle[1])/self.window.design.get_grid_size()
            while int(new_height)<int(old_height_before_zoom):
                new_enclosing_rectangle[3] += self.window.design.get_grid_size()
                new_height = (new_enclosing_rectangle[3] - new_enclosing_rectangle[1])/self.window.design.get_grid_size()
        if old_width_before_zoom!=0: # Only true, when zoom is involved.
            new_width = (new_enclosing_rectangle[2] - new_enclosing_rectangle[0])/self.window.design.get_grid_size()
            while int(new_width)<int(old_width_before_zoom):
                new_enclosing_rectangle[2] += self.window.design.get_grid_size()
                new_width = (new_enclosing_rectangle[2] - new_enclosing_rectangle[0])/self.window.design.get_grid_size()
        return new_enclosing_rectangle

    def __end_inserting(self):
        references_to_connected_wires = []
        self.move_to_grid(references_to_connected_wires)
        self.__add_bindings_to_block()
        self.__restore_diagram_tab_canvas_bindings()
        self.store_item(push_design_to_stack=True, signal_design_change=True)

    def move_to_grid(self, references_to_connected_wires, touching_point="middle"):
        rectangle_coords = self.diagram_tab.canvas.coords(self.rectangle_canvas_id)
        if touching_point in ["middle", "top_left"]:
            remainder_x = rectangle_coords[0] % self.window.design.get_grid_size()
            remainder_y = rectangle_coords[1] % self.window.design.get_grid_size()
        elif touching_point=="top_right":
            remainder_x = rectangle_coords[2] % self.window.design.get_grid_size()
            remainder_y = rectangle_coords[1] % self.window.design.get_grid_size()
        elif touching_point=="bottom_right":
            remainder_x = rectangle_coords[2] % self.window.design.get_grid_size()
            remainder_y = rectangle_coords[3] % self.window.design.get_grid_size()
        else: #if touching_point=="bottom_left":
            remainder_x = rectangle_coords[0] % self.window.design.get_grid_size()
            remainder_y = rectangle_coords[3] % self.window.design.get_grid_size()
        delta_x = - remainder_x
        delta_y = - remainder_y
        if remainder_x>self.window.design.get_grid_size()/2:
            delta_x += self.window.design.get_grid_size()
        if remainder_y>self.window.design.get_grid_size()/2:
            delta_y += self.window.design.get_grid_size()
        delta_x, delta_y = self.__move_item(delta_x, delta_y, touching_point)
        self.__move_connected_wires(references_to_connected_wires, touching_point, delta_x, delta_y, "last_time")

    def __reject(self):
        if self.rectangle_reference is not None:
            self.__restore_diagram_tab_canvas_bindings()
            self.diagram_tab.canvas.focus_set() # needed to catch Ctrl-z, which is bound to Canvas.
            self.diagram_tab.canvas.delete(self.canvas_id)
            self.rectangle_reference.delete_item(push_design_to_stack=False)
            del self # Once the last reference to an object is deleted, the object will be removed by garbage collection.

    def __restore_diagram_tab_canvas_bindings(self):
        self.window.config(cursor="arrow")
        self.__remove_insertion_bindings_from_canvas()
        self.diagram_tab.create_canvas_bindings()

    def __move_start(self, event):
        self.event_x = self.diagram_tab.canvas.canvasx(event.x)
        self.event_y = self.diagram_tab.canvas.canvasy(event.y)
        block_coords = self.diagram_tab.canvas.coords(self.rectangle_canvas_id)
        touching_point = self.__get_touching_point(block_coords)
        block_coords_ext = [] # Extend the coordinates, because after zoom sometimes overlapping is not guaranteed anymore.
        block_coords_ext.append(block_coords[0] - 1)
        block_coords_ext.append(block_coords[1] - 1)
        block_coords_ext.append(block_coords[2] + 1)
        block_coords_ext.append(block_coords[3] + 1)
        list_overlapping = self.diagram_tab.canvas.find_overlapping(*block_coords_ext)
        references_to_connected_wires = self.__get_references_to_connected_wires(block_coords, list_overlapping)
        self.func_id_motion         = self.diagram_tab.canvas.tag_bind(self.rectangle_canvas_id,
                                      "<Motion>"         , lambda event: self.__move_to(event, references_to_connected_wires, touching_point))
        self.func_id_button_release = self.diagram_tab.canvas.tag_bind(self.rectangle_canvas_id,
                                      "<ButtonRelease-1>", lambda event: self.__move_end(references_to_connected_wires, touching_point))

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

    def __get_references_to_connected_wires(self, block_coords, list_overlapping):
        references_to_connected_wires = []
        for canvas_id in list_overlapping:
            if self.diagram_tab.canvas.type(canvas_id)=="line" and "grid_line" not in self.diagram_tab.canvas.gettags(canvas_id):
                line_coords = self.diagram_tab.canvas.coords(canvas_id)
                # A wire is "connected" if a wire-end-point touches the block and the wire hits the block with a right angle in this point.
                if    (self.__coords_are_equal(line_coords[0], block_coords[0]) and # left of block
                       block_coords[1]<=line_coords[ 1]<=block_coords[3]):#        and # inside block
                    references_to_connected_wires.append((self.diagram_tab.design.get_references([canvas_id])[0], "first", "left"))
                elif  (self.__coords_are_equal(line_coords[0], block_coords[2]) and # right of block
                       block_coords[1]<=line_coords[ 1]<=block_coords[3]):#        and # inside block
                    references_to_connected_wires.append((self.diagram_tab.design.get_references([canvas_id])[0], "first", "right"))
                elif (self.__coords_are_equal(line_coords[1], block_coords[1]) and # top of block
                       block_coords[0]<=line_coords[ 0]<=block_coords[2]):#       and # inside block
                    references_to_connected_wires.append((self.diagram_tab.design.get_references([canvas_id])[0], "first", "top"))
                elif (self.__coords_are_equal(line_coords[1], block_coords[3]) and # bottom of block
                       block_coords[0]<=line_coords[ 0]<=block_coords[2]):#       and # inside block
                    references_to_connected_wires.append((self.diagram_tab.design.get_references([canvas_id])[0], "first", "bottom"))
                elif (self.__coords_are_equal(line_coords[-2], block_coords[0]) and
                       block_coords[1]<=line_coords[-1]<=block_coords[3]):#  and
                    references_to_connected_wires.append((self.diagram_tab.design.get_references([canvas_id])[0], "last", "left"))
                elif (self.__coords_are_equal(line_coords[-2], block_coords[2]) and
                       block_coords[1]<=line_coords[-1]<=block_coords[3]):#  and
                    references_to_connected_wires.append((self.diagram_tab.design.get_references([canvas_id])[0], "last", "right"))
                elif (self.__coords_are_equal(line_coords[-1], block_coords[1]) and
                       block_coords[0]<=line_coords[-2]<=block_coords[2]):#  and
                    references_to_connected_wires.append((self.diagram_tab.design.get_references([canvas_id])[0], "last", "top"))
                elif (self.__coords_are_equal(line_coords[-1], block_coords[3]) and
                       block_coords[0]<=line_coords[-2]<=block_coords[2]):#  and
                    references_to_connected_wires.append((self.diagram_tab.design.get_references([canvas_id])[0], "last", "bottom"))
                else:
                    pass # no wire is connected to the block", line_coords, block_coords)
        return references_to_connected_wires

    def __coords_are_equal(self, coord1, coord2):
        if abs(coord1 - coord2)<0.25 * self.window.design.get_grid_size():
            return True
        return False

    def __move_to(self, event, references_to_connected_wires, touching_point):
        new_event_x = self.diagram_tab.canvas.canvasx(event.x)
        new_event_y = self.diagram_tab.canvas.canvasy(event.y)
        delta_x = new_event_x-self.event_x
        delta_y = new_event_y-self.event_y
        delta_x, delta_y = self.__move_item(delta_x, delta_y, touching_point)
        self.__move_connected_wires(references_to_connected_wires, touching_point, delta_x, delta_y, "not move end")
        self.event_x = new_event_x
        self.event_y = new_event_y

    def __move_connected_wires(self, references_to_connected_wires, touching_point, delta_x, delta_y, move_phase):
        for reference in references_to_connected_wires:
            reference_to_wire = reference[0]
            moved_point       = reference[1] # first or last point of wire
            connected_to      = reference[2] # top, right, bottom, left side of block
            if touching_point=="middle":
                reference_to_wire.move_wire_end_point(move_phase, moved_point, delta_x, delta_y)
            else:
                if touching_point=="top_left":
                    if connected_to=="left":
                        reference_to_wire.move_wire_end_point(move_phase, moved_point, delta_x, 0)
                    elif connected_to=="top":
                        reference_to_wire.move_wire_end_point(move_phase, moved_point, 0, delta_y)
                elif touching_point=="top_right":
                    if connected_to=="right":
                        reference_to_wire.move_wire_end_point(move_phase, moved_point, delta_x, 0)
                    elif connected_to=="top":
                        reference_to_wire.move_wire_end_point(move_phase, moved_point, 0, delta_y)
                elif touching_point=="bottom_right":
                    if connected_to=="right":
                        reference_to_wire.move_wire_end_point(move_phase, moved_point, delta_x, 0)
                    elif connected_to=="bottom":
                        reference_to_wire.move_wire_end_point(move_phase, moved_point, 0, delta_y)
                elif touching_point=="bottom_left":
                    if connected_to=="left":
                        reference_to_wire.move_wire_end_point(move_phase, moved_point, delta_x, 0)
                    elif connected_to=="bottom":
                        reference_to_wire.move_wire_end_point(move_phase, moved_point, 0, delta_y)

    def __move_end(self, references_to_connected_wires, touching_point):
        self.diagram_tab.canvas.tag_unbind(self.rectangle_canvas_id, "<Motion>"         , self.func_id_motion)
        self.diagram_tab.canvas.tag_unbind(self.rectangle_canvas_id, "<ButtonRelease-1>", self.func_id_button_release)
        self.move_to_grid(references_to_connected_wires, touching_point)
        self.store_item(push_design_to_stack=True, signal_design_change=True)

    def __move_item(self, delta_x, delta_y, touching_point):
        if touching_point=="middle":
            self.rectangle_reference.move_item(delta_x, delta_y)
            self.diagram_tab.canvas.move(self.canvas_id, delta_x, delta_y)
        else:
            corner_was_moved = self.rectangle_reference.move_corner(delta_x, delta_y, touching_point)
            if corner_was_moved:
                if touching_point=="top_left":
                    self.diagram_tab.canvas.move(self.canvas_id, delta_x, delta_y)
                elif touching_point=="top_right":
                    self.diagram_tab.canvas.move(self.canvas_id, 0, delta_y)
                elif touching_point=="bottom_left":
                    self.diagram_tab.canvas.move(self.canvas_id, delta_x, 0)
                else: # touching_point=="bottom_right"
                    pass # As the ancher point of the text is top left, nothing has to be done here.
            else:
                return 0, 0
        return delta_x, delta_y

    def select_item(self):
        self.__remove_bindings_from_block()

    def unselect_item(self):
        self.__add_bindings_to_block()

    def __draw_at_location(self, rect_coords, rect_color, text_coords, text):
        self.__draw(rect_coords, text_coords, rect_color, text)
        self.__add_bindings_to_block()
        self.store_item(push_design_to_stack=False, signal_design_change=False)

    def __add_bindings_to_block(self):
        self.sym_bind_funcid_button   = self.diagram_tab.canvas.tag_bind(self.rectangle_canvas_id,"<Button-1>"       , self.__move_start              )
        self.sym_bind_funcid_enter1   = self.diagram_tab.canvas.tag_bind(self.rectangle_canvas_id,"<Enter>"          , lambda event: self.__at_enter())
        self.sym_bind_funcid_leave1   = self.diagram_tab.canvas.tag_bind(self.rectangle_canvas_id,"<Leave>"          , lambda event: self.__at_leave())
        self.sym_bind_funcid_showmen1 = self.diagram_tab.canvas.tag_bind(self.rectangle_canvas_id,"<Button-3>"       , self.__show_menu)
        self.sym_bind_funcid_enter    = self.diagram_tab.canvas.tag_bind(self.canvas_id          ,"<Enter>"          , lambda event: self.__at_enter())
        self.sym_bind_funcid_leave    = self.diagram_tab.canvas.tag_bind(self.canvas_id          ,"<Leave>"          , lambda event: self.__at_leave())
        self.sym_bind_funcid_dbutton  = self.diagram_tab.canvas.tag_bind(self.canvas_id          ,"<Double-Button-1>", self.__edit)
        self.sym_bind_funcid_edit_ex  = self.diagram_tab.canvas.tag_bind(self.canvas_id          ,"<Control-e>"      , lambda event: self.__edit_ext())
        self.sym_bind_funcid_edit_er  = self.diagram_tab.canvas.tag_bind(self.canvas_id          ,"<Control-E>"      , lambda event: self.__create_capslock_warning('E'))
        self.sym_bind_funcid_showmen2 = self.diagram_tab.canvas.tag_bind(self.canvas_id          ,"<Button-3>"       , self.__show_menu)

    def __remove_bindings_from_block(self):
        if self.sym_bind_funcid_button is not None:
            self.diagram_tab.canvas.tag_unbind(self.rectangle_canvas_id,"<Button-1>"       , self.sym_bind_funcid_button)
            self.diagram_tab.canvas.tag_unbind(self.rectangle_canvas_id,"<Enter>"          , self.sym_bind_funcid_enter1)
            self.diagram_tab.canvas.tag_unbind(self.rectangle_canvas_id,"<Leave>"          , self.sym_bind_funcid_leave1)
            self.diagram_tab.canvas.tag_unbind(self.rectangle_canvas_id,"<Button-3>"       , self.sym_bind_funcid_showmen1)
            self.diagram_tab.canvas.tag_unbind(self.canvas_id          ,"<Double-Button-1>", self.sym_bind_funcid_dbutton)
            self.diagram_tab.canvas.tag_unbind(self.canvas_id          ,"<Control-e>"      , self.sym_bind_funcid_edit_ex)
            self.diagram_tab.canvas.tag_unbind(self.canvas_id          ,"<Control-E>"      , self.sym_bind_funcid_edit_er)
            self.diagram_tab.canvas.tag_unbind(self.canvas_id          ,"<Enter>"          , self.sym_bind_funcid_enter)
            self.diagram_tab.canvas.tag_unbind(self.canvas_id          ,"<Leave>"          , self.sym_bind_funcid_leave)
            self.diagram_tab.canvas.tag_unbind(self.canvas_id          ,"<Button-3>"       , self.sym_bind_funcid_showmen2)
            self.sym_bind_funcid_button   = None
            self.sym_bind_funcid_dbutton  = None
            self.sym_bind_funcid_enter    = None
            self.sym_bind_funcid_leave    = None
            self.sym_bind_funcid_edit_ex  = None
            self.sym_bind_funcid_edit_er  = None
            self.sym_bind_funcid_showmen1 = None
            self.sym_bind_funcid_showmen2 = None

    def __create_bindings_for_insertion_at_canvas(self, rect_color):
        self.func_id_motion = self.diagram_tab.canvas.bind("<Motion>"  , lambda event, rect_color=rect_color: self.__draw_once_at_event_location(event, rect_color))
        self.func_id_button = self.diagram_tab.canvas.bind("<Button-1>", lambda event: self.__end_inserting())
        self.func_id_leave  = self.diagram_tab.canvas.bind("<Leave>"   , lambda event: self.__reject())
        self.func_id_escape = self.window.bind            ("<Escape>"  , lambda event: self.__reject())

    def __remove_insertion_bindings_from_canvas(self):
        self.diagram_tab.canvas.unbind ("<Motion>"  , self.func_id_motion)
        self.diagram_tab.canvas.unbind ("<Button-1>", self.func_id_button)
        self.diagram_tab.canvas.unbind ("<Leave>"   , self.func_id_leave )
        self.window.unbind             ("<Escape>"  , self.func_id_escape)
        self.func_id_motion = None
        self.func_id_button = None
        self.func_id_leave  = None
        self.func_id_escape = None

    def __show_menu(self, event):
        event_x = self.diagram_tab.canvas.canvasx(event.x)
        event_y = self.diagram_tab.canvas.canvasy(event.y)
        menu_entry_list = tk.StringVar()
        menu_entry_list.set(r"Change\ color")
        menu = listbox_animated.ListboxAnimated(self.diagram_tab.canvas, listvariable=menu_entry_list, height=1,
                                                bg='grey', width=25, activestyle='dotbox', relief="raised")
        menue_window = self.diagram_tab.canvas.create_window(event_x, event_y, window=menu)
        menu.bind("<Button-1>", lambda event: self.__evaluate_menu_after_idle(menue_window, menu))
        menu.bind("<Leave>"   , lambda event: self.__close_menu(menue_window, menu))

    def __evaluate_menu_after_idle(self, menue_window, menu):
        self.diagram_tab.canvas.after_idle(self.__evaluate_menu, menue_window, menu)

    def __evaluate_menu(self, menue_window, menu):
        selected_entry = menu.get(menu.curselection()[0])
        if 'Change color' in selected_entry:
            new_color = color_changer.ColorChanger(constants.BLOCK_DEFAULT_COLOR, self.window).get_new_color()
            if new_color is not None:
                self.diagram_tab.canvas.itemconfig(self.rectangle_canvas_id, fill=new_color)
        self.__close_menu(menue_window, menu)

    def __close_menu(self, menue_window, menu):
        menu.destroy()
        self.diagram_tab.canvas.delete(menue_window)

    def __at_enter(self):
        # if self.window.config()["cursor"][-1]=="arrow": # In all other cases a user action is active which already has overwritten the bindings,
        #     self.diagram_tab.remove_canvas_bindings()   # removing the canvas bindings would then destroy the bindings of the user action.
        if not self.diagram_tab.canvas.find_withtag("selected"):
            self.diagram_tab.canvas.focus_set()                # Needed for the next line.
            self.diagram_tab.canvas.focus(self.canvas_id) # Needed for Control-e to edit the text under the mouse.
            self.funcid_delete = self.diagram_tab.canvas.bind("<Delete>", lambda event: self.__delete_text_and_rectangle())

    def __at_leave(self):
        # if self.window.config()["cursor"][-1]=="arrow":
        #     self.diagram_tab.create_canvas_bindings()
        self.__restore_delete_binding()

    def __create_capslock_warning(self, character):
        messagebox.showwarning("HDl_SCHEM-Editor", "There is no shortcut for the capital letter '" + character + "'.\n" +
                               "Perhaps CapsLock is activated.")

    def __restore_delete_binding(self):
        if self.funcid_delete is not None: # Check is needed, because sometimes a select-rectangle and the delete-binding both perform a delete.
            self.diagram_tab.canvas.unbind("<Delete>", self.funcid_delete)
            self.funcid_delete = None
            self.diagram_tab.canvas.bind("<Delete>", lambda event: self.diagram_tab.delete_selection())

    def __delete_text_and_rectangle(self):
        self.rectangle_reference.delete_item(push_design_to_stack=False)
        self.delete_item(push_design_to_stack=True)

    def delete_item(self, push_design_to_stack):
        self.__restore_delete_binding()
        self.diagram_tab.canvas.delete(self.canvas_id)
        if self.block_edit_ref is not None:
            self.block_edit_ref.close_edit_window()
        self.window.design.remove_canvas_item_from_dictionary(self.canvas_id, push_design_to_stack)
        self.diagram_tab.create_canvas_bindings() # Needed because when "self" is deleted after entering the symbol, no __at_leave will take place.
        del self # Once the last reference to an object is deleted, the object will be removed by garbage collection.

    def store_item(self, push_design_to_stack, signal_design_change):
        rect_coords = self.diagram_tab.canvas.coords  (self.rectangle_canvas_id)
        rect_color  = self.diagram_tab.canvas.itemcget(self.rectangle_canvas_id, "fill")
        text_coords = self.diagram_tab.canvas.coords  (self.canvas_id     )
        text        = self.diagram_tab.canvas.itemcget(self.canvas_id, "text")
        text        = self.remove_blanks_at_line_ends(text)
        self.window.design.store_block_in_canvas_dictionary(self.canvas_id, self, rect_coords, rect_color, text_coords, text,
                                                            self.object_tag, push_design_to_stack, signal_design_change)

    def __edit(self, event):
        if self.block_edit_ref is None: # When BlockEdit is closed it sets block_edit_ref to None again.
            self.block_edit_ref = block_edit.BlockEdit(self, self.window, self.diagram_tab, self.rectangle_reference, self.canvas_id, self.rectangle_canvas_id,
                                                use_external_editor=False)
            self.__position_insertion_cursor_under_mouse(event)

    def edit_block(self): # Called by notebook_diagram through link_dictionary
        if self.block_edit_ref is not None: # When BlockEdit is closed it sets block_edit_ref to None again.
            self.block_edit_ref.close_edit_window()
            #print("close_edit_window is called: self.block_edit_ref =", self.block_edit_ref)
        self.block_edit_ref = block_edit.BlockEdit(self, self.window, self.diagram_tab, self.rectangle_reference, self.canvas_id, self.rectangle_canvas_id,
                                            use_external_editor=False)
        #print("new self.block_edit_ref =", self.block_edit_ref)
        return self.block_edit_ref.text_edit_widget

    def __position_insertion_cursor_under_mouse(self, event):
        # For @x,y positions the text widget uses a coordinate system which starts with 0,0 at the "nw" edge.
        canvas_x = self.diagram_tab.canvas.canvasx(event.x)
        canvas_y = self.diagram_tab.canvas.canvasy(event.y)
        canvas_window_coords = self.diagram_tab.canvas.coords(self.block_edit_ref.canvas_window_for_text_edit_widget)
        delta_x = int(-canvas_window_coords[0] + canvas_x)
        delta_y = int(-canvas_window_coords[1] + canvas_y)
        self.diagram_tab.canvas.after_idle(lambda: self.block_edit_ref.text_edit_widget.mark_set("insert", f"@{delta_x},{delta_y}"))

    def __edit_ext(self):
        block_edit.BlockEdit(self, self.window, self.diagram_tab, self.rectangle_reference, self.canvas_id, self.rectangle_canvas_id,
                             use_external_editor=True)

    def remove_blanks_at_line_ends(self, text):
        text_wo_blanks = re.sub("[ ]*$", "", text, flags=re.MULTILINE)
        return text_wo_blanks

    def get_ids(self):
        return [self.canvas_id, self.rectangle_canvas_id]

    def get_object_tag(self):
        return self.object_tag

    def add_pasted_tag_to_all_canvas_items(self):
        self.diagram_tab.canvas.addtag_withtag("pasted_tag", self.canvas_id)

    def adapt_coordinates_by_factor(self, factor):
        coords = self.diagram_tab.canvas.coords(self.canvas_id)
        coords = [value*factor for value in coords]
        self.diagram_tab.canvas.coords(self.canvas_id, coords)

    @classmethod
    def get_priority_from_text(cls, text):
        text = re.sub(r"--", "-- ", text) # make sure that a VHDL-comment can be separated by split at blanks.
        text = re.sub(r"//", "// ", text) # make sure that a Verilog-comment can be separated by split at blanks.
        word_list = text.split()
        if (word_list[0]=="--" or word_list[0]=="//") and word_list[1].isnumeric():
            return int(word_list[1])
        return -1
