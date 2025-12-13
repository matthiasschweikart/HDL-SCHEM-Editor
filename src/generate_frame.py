"""
This class is used to add a "Generate Frame" around blocks or instances in the schematic.
The data of the generate-frame is stored in a dictionary called generate_definition.
"""
from tkinter import ttk
import re

class GenerateFrame:
    generate_frame_id = 0
    def __init__(self, root, window, diagram_tab, generate_definition): # generate_definition is an empty dictionary when called from GUI.
        self.root                     = root                            # generate_definition is a filled dictionary when called from reading from file.
        self.window                   = window
        self.diagram_tab              = diagram_tab
        self.generate_definition      = generate_definition
        self.funcid_button1_rectangle = None
        self.funcid_button1_condition = None
        self.funcid_enter_rectangle   = None
        self.funcid_enter_condition   = None
        self.funcid_leave_rectangle   = None
        self.funcid_leave_condition   = None
        self.funcid_button1_double    = None
        self.funcid_delete            = None
        self.event_x                  = None
        self.event_y                  = None
        self.func_id_motion           = None
        self.func_id_button_release   = None
        self.condition_entry_text_box = None
        if self.generate_definition:
            self._draw_from_file()
        else:
            self.generate_definition["object_tag"] = "generate_frame_" + str(self.window.design.get_generate_frame_id())
            self.window.design.increment_generate_frame_id()
            self.diagram_tab.remove_canvas_bindings()
            self.window.config(cursor="cross")
            self.func_id_button         = None
            self.funcid_motion          = None
            self.funcid_button1_release = None
            self._create_bindings_for_generate_frame_insertion()

    def _draw_from_file(self):
        self.generate_definition["generate_rectangle_id"] = self.diagram_tab.canvas.create_rectangle(self.generate_definition["generate_rectangle_coords"],
                                                                                                         dash=(3,5),activeoutline="red", activewidth=3,
                                                                                                         tag=(self.generate_definition["object_tag"], "schematic-element"))
        self.generate_definition["generate_condition_id"] = self.diagram_tab.canvas.create_text(self.generate_definition["generate_rectangle_coords"][0:2],
                                                                        text=self.generate_definition["generate_condition"],
                                                                        font=("Courier", self.window.design.get_font_size()),
                                                                        anchor="sw", activefill="red",
                                                                        tag=(self.generate_definition["object_tag"], "instance-text", "generate-frame", "schematic-element"))
        self._add_bindings_for_generate_frame_handling()
        self.store_item(push_design_to_stack=False, signal_design_change=False)

    def _create_bindings_for_generate_frame_insertion(self):
        self.func_id_button = self.diagram_tab.canvas.bind("<Button-1>", self._start_inserting)
        self.func_id_leave  = self.diagram_tab.canvas.bind("<Leave>"   , lambda event: self._reject())
        self.func_id_escape = self.window.bind            ("<Escape>"  , lambda event: self._reject())

    def _start_inserting(self, event):
        event_x = self.diagram_tab.canvas.canvasx(event.x, gridspacing=self.window.design.get_grid_size())
        event_y = self.diagram_tab.canvas.canvasy(event.y, gridspacing=self.window.design.get_grid_size())
        self.generate_definition["generate_rectangle_id"]     = self.diagram_tab.canvas.create_rectangle(event_x, event_y, event_x, event_y,
                                                                                                         dash=(3,5),activeoutline="red", activewidth=3,
                                                                                                         tag=(self.generate_definition["object_tag"], "schematic-element"))
        self.generate_definition["generate_rectangle_coords"] = [event_x, event_y, event_x, event_y]
        self.funcid_motion          = self.diagram_tab.canvas.bind("<Motion>"         , self._expand_rectangle)
        self.funcid_button1_release = self.diagram_tab.canvas.bind("<ButtonRelease-1>", self._finish_inserting)

    def _reject(self):
        if "generate_rectangle_id" in self.generate_definition: # False after clicking to "new Generate"-button and not clicking into canvas.
            self.diagram_tab.canvas.delete(self.generate_definition["generate_rectangle_id"])
        self.diagram_tab.canvas.focus_set() # needed to catch Ctrl-z
        self._remove_bindings_for_generate_frame_insertion()
        del self # Once the last reference to an object is deleted, the object will be removed by garbage collection.

    def _expand_rectangle(self, event):
        # gridspacing deactivated to get smoother expand:
        event_x = self.diagram_tab.canvas.canvasx(event.x)#, gridspacing=self.window.design.get_grid_size())
        event_y = self.diagram_tab.canvas.canvasy(event.y)#, gridspacing=self.window.design.get_grid_size())
        self.diagram_tab.canvas.coords( self.generate_definition["generate_rectangle_id"],
                                       *self.generate_definition["generate_rectangle_coords"][0:2], event_x, event_y)
        self.generate_definition["generate_rectangle_coords"][2] = event_x
        self.generate_definition["generate_rectangle_coords"][3] = event_y

    def _finish_inserting(self, event):
        event_x, event_y = self._move_event_coordinates_to_grid(event)
        event_x, event_y = self._move_event_coordinates_to_guarantee_a_minimal_rectangle_size(event_x, event_y)
        self._put_event_coordinates_into_generate_defintion(event_x, event_y)
        self._resize_rectangle_to_coordinates_from_generate_definition()
        self._add_generate_condition_to_generate_definition_and_graphic()
        self._remove_bindings_for_generate_frame_insertion()
        self._add_bindings_for_generate_frame_handling()
        self.store_item(push_design_to_stack=True, signal_design_change=True)

    def _move_event_coordinates_to_grid(self, event):
        event_x = self.diagram_tab.canvas.canvasx(event.x, gridspacing=self.window.design.get_grid_size())
        event_y = self.diagram_tab.canvas.canvasy(event.y, gridspacing=self.window.design.get_grid_size())
        return event_x, event_y

    def _move_event_coordinates_to_guarantee_a_minimal_rectangle_size(self, event_x, event_y):
        if event_x-self.generate_definition["generate_rectangle_coords"][0]<2*self.window.design.get_grid_size():
            event_x = self.generate_definition["generate_rectangle_coords"][0]+2*self.window.design.get_grid_size()
        if event_y-self.generate_definition["generate_rectangle_coords"][1]<2*self.window.design.get_grid_size():
            event_y = self.generate_definition["generate_rectangle_coords"][1]+2*self.window.design.get_grid_size()
        return event_x, event_y

    def _put_event_coordinates_into_generate_defintion(self, event_x, event_y):
        self.generate_definition["generate_rectangle_coords"][2] = event_x
        self.generate_definition["generate_rectangle_coords"][3] = event_y

    def _resize_rectangle_to_coordinates_from_generate_definition(self):
        self.diagram_tab.canvas.coords(self.generate_definition["generate_rectangle_id"], *self.generate_definition["generate_rectangle_coords"])

    def _add_generate_condition_to_generate_definition_and_graphic(self):
        self.generate_definition["generate_condition"] = "label_g: if <condition> generate"
        self.generate_definition["generate_condition_id"] = self.diagram_tab.canvas.create_text(self.generate_definition["generate_rectangle_coords"][0:2],
                                                                        text=self.generate_definition["generate_condition"],
                                                                        font=("Courier", self.window.design.get_font_size()),
                                                                        anchor="sw", activefill="red",
                                                                        tag=(self.generate_definition["object_tag"], "instance-text", "generate-frame", "schematic-element"))

    def _remove_bindings_for_generate_frame_insertion(self):
        self.diagram_tab.canvas.unbind("<Button-1>"       , self.func_id_button        )
        self.diagram_tab.canvas.unbind("<Leave>"          , self.func_id_leave         )
        self.diagram_tab.canvas.unbind("<Motion>"         , self.funcid_motion         )
        self.diagram_tab.canvas.unbind("<ButtonRelease-1>", self.funcid_button1_release)
        self.window.unbind            ("<Escape>"         , self.func_id_escape        )
        del self.func_id_button
        del self.func_id_leave
        del self.func_id_escape
        del self.funcid_motion
        del self.funcid_button1_release
        self.diagram_tab.create_canvas_bindings()
        self.window.config(cursor="arrow")

    def select_item(self):
        self._highlight()
        self._remove_bindings_from_generate_frame()

    def unselect_item(self):
        self.__unhighlight()
        self._add_bindings_for_generate_frame_handling()

    def _highlight(self):
        self.diagram_tab.canvas.itemconfigure(self.generate_definition["generate_rectangle_id"], outline="red")
        self.diagram_tab.canvas.itemconfigure(self.generate_definition["generate_condition_id"], fill   ="red")

    def __unhighlight(self):
        self.diagram_tab.canvas.itemconfigure(self.generate_definition["generate_rectangle_id"], outline="black")
        self.diagram_tab.canvas.itemconfigure(self.generate_definition["generate_condition_id"], fill   ="black")

    def store_item(self, push_design_to_stack, signal_design_change):
        # Called in diagram_tab by zoom, replace, move_selection_end.
        self._update_generate_definition()
        self.window.design.store_generate_frame_in_canvas_dictionary(self.generate_definition["generate_rectangle_id"],
                                                                                             self, self.generate_definition, push_design_to_stack, signal_design_change)

    def get_object_tag(self):
        return self.generate_definition["object_tag"]

    def _update_generate_definition(self):
        self.generate_definition["generate_rectangle_coords"] = self.diagram_tab.canvas.coords  (self.generate_definition["generate_rectangle_id"])
        self.generate_definition["generate_condition_coords"] = self.diagram_tab.canvas.coords  (self.generate_definition["generate_condition_id"])
        self.generate_definition["generate_condition"       ] = self.diagram_tab.canvas.itemcget(self.generate_definition["generate_condition_id"], "text")

    def _add_bindings_for_generate_frame_handling(self):
        self.funcid_button1_rectangle = self.diagram_tab.canvas.tag_bind(self.generate_definition["generate_rectangle_id"],"<Button-1>"       , self._move_start               )
        self.funcid_button1_condition = self.diagram_tab.canvas.tag_bind(self.generate_definition["generate_condition_id"],"<Button-1>"       , self._move_start_from_condition)
        self.funcid_enter_rectangle   = self.diagram_tab.canvas.tag_bind(self.generate_definition["generate_rectangle_id"],"<Enter>"          , lambda event: self._at_enter() )
        self.funcid_enter_condition   = self.diagram_tab.canvas.tag_bind(self.generate_definition["generate_condition_id"],"<Enter>"          , lambda event: self._at_enter() )
        self.funcid_leave_rectangle   = self.diagram_tab.canvas.tag_bind(self.generate_definition["generate_rectangle_id"],"<Leave>"          , lambda event: self._at_leave() )
        self.funcid_leave_condition   = self.diagram_tab.canvas.tag_bind(self.generate_definition["generate_condition_id"],"<Leave>"          , lambda event: self._at_leave() )
        self.funcid_button1_double    = self.diagram_tab.canvas.tag_bind(self.generate_definition["generate_condition_id"],"<Double-Button-1>", lambda event: self.edit    () )

    def _remove_bindings_from_generate_frame(self):
        self.diagram_tab.canvas.tag_unbind(self.generate_definition["generate_rectangle_id"],"<Button-1>"       , self.funcid_button1_rectangle)
        self.diagram_tab.canvas.tag_unbind(self.generate_definition["generate_condition_id"],"<Button-1>"       , self.funcid_button1_condition)
        self.diagram_tab.canvas.tag_unbind(self.generate_definition["generate_rectangle_id"],"<Enter>"          , self.funcid_enter_rectangle  )
        self.diagram_tab.canvas.tag_unbind(self.generate_definition["generate_condition_id"],"<Enter>"          , self.funcid_enter_condition  )
        self.diagram_tab.canvas.tag_unbind(self.generate_definition["generate_rectangle_id"],"<Leave>"          , self.funcid_leave_rectangle  )
        self.diagram_tab.canvas.tag_unbind(self.generate_definition["generate_condition_id"],"<Leave>"          , self.funcid_leave_condition  )
        self.diagram_tab.canvas.tag_unbind(self.generate_definition["generate_condition_id"],"<Double-Button-1>", self.funcid_button1_double   )

    def _at_enter(self):
        if not self.diagram_tab.canvas.find_withtag("selected"):
            self.diagram_tab.canvas.focus_set()
            self.funcid_delete = self.diagram_tab.canvas.bind("<Delete>", lambda event: self.delete_item(push_design_to_stack=True))

    def _at_leave(self):
        self._restore_delete_binding()

    def _restore_delete_binding(self):
        if self.funcid_delete is not None:
            self.diagram_tab.canvas.unbind("<Delete>", self.funcid_delete)
            self.funcid_delete = None
            self.diagram_tab.canvas.bind("<Delete>", lambda event: self.diagram_tab.delete_selection())

    def delete_item(self, push_design_to_stack):
        self._restore_delete_binding()
        self.window.design.remove_canvas_item_from_dictionary(self.generate_definition["generate_rectangle_id"], push_design_to_stack)
        self.diagram_tab.canvas.delete(self.generate_definition["generate_rectangle_id"])
        self.diagram_tab.canvas.delete(self.generate_definition["generate_condition_id"])
        self.diagram_tab.create_canvas_bindings() # Needed because when "self" is deleted after entering the symbol, no _at_leave will take place.
        del self # Once the last reference to an object is deleted, the object will be removed by garbage collection.

    def _move_start_from_condition(self, event):
        self.event_x = self.diagram_tab.canvas.canvasx(event.x, gridspacing=self.window.design.get_grid_size())
        self.event_y = self.diagram_tab.canvas.canvasy(event.y, gridspacing=self.window.design.get_grid_size())
        self.func_id_motion         = self.diagram_tab.canvas.tag_bind(self.generate_definition["generate_condition_id"],
                                      "<Motion>"         , lambda event: self._move_to(event, "middle"))
        self.func_id_button_release = self.diagram_tab.canvas.tag_bind(self.generate_definition["generate_condition_id"],
                                      "<ButtonRelease-1>", lambda event: self._move_end("condition"))

    def _move_start(self, event):
        self.event_x = self.diagram_tab.canvas.canvasx(event.x, gridspacing=self.window.design.get_grid_size())
        self.event_y = self.diagram_tab.canvas.canvasy(event.y, gridspacing=self.window.design.get_grid_size())
        block_coords = self.diagram_tab.canvas.coords(self.generate_definition["generate_rectangle_id"])
        touching_point = self._get_touching_point(block_coords)
        self.func_id_motion         = self.diagram_tab.canvas.tag_bind(self.generate_definition["generate_rectangle_id"],
                                      "<Motion>"         , lambda event: self._move_to(event, touching_point))
        self.func_id_button_release = self.diagram_tab.canvas.tag_bind(self.generate_definition["generate_rectangle_id"],
                                      "<ButtonRelease-1>", lambda event: self._move_end("rectangle"))

    def _get_touching_point(self, rectangle_coords):
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

    def _move_to(self, event, touching_point):
        new_event_x = self.diagram_tab.canvas.canvasx(event.x, gridspacing=self.window.design.get_grid_size())
        new_event_y = self.diagram_tab.canvas.canvasy(event.y, gridspacing=self.window.design.get_grid_size())
        delta_x = new_event_x-self.event_x
        delta_y = new_event_y-self.event_y
        self._move_item(delta_x, delta_y, touching_point)
        self.event_x = new_event_x
        self.event_y = new_event_y

    def _move_end(self, moved_object):
        if moved_object=="rectangle":
            self.diagram_tab.canvas.tag_unbind(self.generate_definition["generate_rectangle_id"], "<Motion>"         , self.func_id_motion)
            self.diagram_tab.canvas.tag_unbind(self.generate_definition["generate_rectangle_id"], "<ButtonRelease-1>", self.func_id_button_release)
        else:
            self.diagram_tab.canvas.tag_unbind(self.generate_definition["generate_condition_id"], "<Motion>"         , self.func_id_motion)
            self.diagram_tab.canvas.tag_unbind(self.generate_definition["generate_condition_id"], "<ButtonRelease-1>", self.func_id_button_release)
        if (self.generate_definition["generate_rectangle_coords"]!=self.diagram_tab.canvas.coords(self.generate_definition["generate_rectangle_id"]) or
            self.generate_definition["generate_condition_coords"]!=self.diagram_tab.canvas.coords(self.generate_definition["generate_condition_id"])):
            self.store_item(push_design_to_stack=True, signal_design_change=True)

    def _move_item(self, delta_x, delta_y, touching_point):
        if touching_point=="middle":
            self.diagram_tab.canvas.move(self.generate_definition["generate_rectangle_id"], delta_x, delta_y)
            self.diagram_tab.canvas.move(self.generate_definition["generate_condition_id"], delta_x, delta_y)
        else:
            corner_was_moved = self._move_corner(delta_x, delta_y, touching_point)
            if corner_was_moved:
                if touching_point=="top_left":
                    self.diagram_tab.canvas.move(self.generate_definition["generate_condition_id"], delta_x, delta_y)
                elif touching_point=="top_right":
                    self.diagram_tab.canvas.move(self.generate_definition["generate_condition_id"], 0, delta_y)
                elif touching_point=="bottom_left":
                    self.diagram_tab.canvas.move(self.generate_definition["generate_condition_id"], delta_x, 0)
                else: # touching_point=="bottom_right"
                    pass # As the anchor point of the text is top left, nothing has to be done here.

    def _move_corner(self, delta_x, delta_y, touching_point):
        coords = self.diagram_tab.canvas.coords(self.generate_definition["generate_rectangle_id"])
        new_coords = list(coords)
        if touching_point=="top_left":
            new_coords[0] = coords[0] + delta_x
            new_coords[1] = coords[1] + delta_y
        elif touching_point=="top_right":
            new_coords[1] = coords[1] + delta_y
            new_coords[2] = coords[2] + delta_x
        elif touching_point=="bottom_left":
            new_coords[0] = coords[0] + delta_x
            new_coords[3] = coords[3] + delta_y
        elif touching_point=="bottom_right":
            new_coords[2] = coords[2] + delta_x
            new_coords[3] = coords[3] + delta_y
        # Guarantee a minimal rectangle size of 2 times grid_size.
        # Use factor 1.999 instead of factor 2 for compensating a not exact calculation:
        if (new_coords[2]-new_coords[0]>=1.999*self.window.design.get_grid_size() and
            new_coords[3]-new_coords[1]>=1.999*self.window.design.get_grid_size()):
            self.diagram_tab.canvas.coords(self.generate_definition["generate_rectangle_id"], new_coords)
            return True
        return False

    def edit(self):
        self.condition_entry_text_box = ttk.Entry(self.diagram_tab.canvas, width=len(self.generate_definition["generate_condition"]),
                                                  font=("Courier", self.window.design.get_font_size()))
        self.condition_entry_text_box.insert("end", self.generate_definition["generate_condition"])
        self.condition_entry_text_box.focus_set()
        self.condition_entry_text_box.bind('<Key>'   , lambda event: self._increase_length_after_idle())
        self.condition_entry_text_box.bind('<Return>', lambda event: self._update_generate_condition ())
        self.condition_entry_text_box.bind('<Escape>', lambda event: self._delete_entry_window       ())
        self.diagram_tab.canvas.create_window(self.generate_definition["generate_rectangle_coords"][0:2],
                                              window=self.condition_entry_text_box, anchor="sw", tag='entry-window')

    def _increase_length_after_idle(self):
        self.diagram_tab.canvas.after_idle(self._increase_length)

    def _increase_length(self):
        new_length = len(self.condition_entry_text_box.get())
        if new_length>len(self.generate_definition["generate_condition"]):
            self.condition_entry_text_box.configure(width=new_length)

    def _update_generate_condition(self):
        new_text = self.condition_entry_text_box.get()
        self._delete_entry_window()
        if new_text!=self.generate_definition["generate_condition"]:
            self.generate_definition["generate_condition"] = new_text
            self.diagram_tab.canvas.itemconfigure(self.generate_definition["generate_condition_id"], text=self.generate_definition["generate_condition"])
            self.store_item(push_design_to_stack=True, signal_design_change=True)

    def _delete_entry_window(self):
        self.condition_entry_text_box.destroy()
        self.condition_entry_text_box = None
        self.diagram_tab.canvas.delete("entry-window")

    def add_pasted_tag_to_all_canvas_items(self):
        list_of_canvas_ids = [self.generate_definition["generate_rectangle_id"],
                              self.generate_definition["generate_condition_id"]]
        for canvas_id in list_of_canvas_ids:
            self.diagram_tab.canvas.addtag_withtag("pasted_tag", canvas_id)

    def adapt_coordinates_by_factor(self, factor):
        list_of_canvas_ids = [self.generate_definition["generate_rectangle_id"],
                              self.generate_definition["generate_condition_id"]]
        for canvas_id in list_of_canvas_ids:
            coords = self.diagram_tab.canvas.coords(canvas_id)
            coords = [value*factor for value in coords]
            self.diagram_tab.canvas.coords(canvas_id, coords)

    @classmethod
    def get_generate_definition_shifted(cls, generate_definition, offset):
        generate_definition["generate_rectangle_coords"] = [coord + offset for coord in generate_definition["generate_rectangle_coords"]]
        return generate_definition

    @classmethod
    def get_priority_from_generate_definition(cls, generate_definition):
        comment = ""
        if "--" in generate_definition["generate_condition"]:
            comment = re.sub(r".*--", "", generate_definition["generate_condition"])
        elif "//" in generate_definition["generate_condition"]:
            comment = re.sub(r".*//", "", generate_definition["generate_condition"])
        if comment!="":
            word_list = comment.split()
            if word_list[0].isnumeric():
                return int(word_list[0])
        return -1

    @classmethod
    def get_rectangle_coords_from_generate_definition(cls, generate_definition):
        return generate_definition["generate_rectangle_coords"]

    @classmethod
    def get_canvas_id_and_condition_from_generate_definition(cls, generate_definition):
        return generate_definition["generate_rectangle_id"], generate_definition["generate_condition"]
