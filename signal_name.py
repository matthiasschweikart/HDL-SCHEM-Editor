""" Implements all stuff for signal names
The signal declaration shall always use the selected language.
The signal declaration can be extended by defining a range for the signal:
VHDL   : data_bus(7 downto 4) : std_logic_vector(31 downto 0) := X"12345678" -- comment
Verilog: reg [31:0] data_bus : [7:4]
The visible part of this declaration is only the name and the range,
this means for this example:
"data_bus(7 downto 4)" VHDL
"data_bus[7:4]" verilog
"""
from tkinter import ttk
from tkinter import messagebox
import re

import hdl_generate_functions

class SignalName:
    signal_name_under_edit = None
    def __init__(self,
                 design,      #: design_data.DesignData,
                 diagram_tab, #: notebook_diagram_tab.NotebookDiagramTab,
                 coords,
                 angle,
                 wire_tag,
                 declaration
                 ):
        self.angle                    = angle
        self.diagram_tab              = diagram_tab
        self.design                   = design
        self.wire_tag                 = wire_tag
        self.anchor_line              = 0
        self.event_x                  = 0
        self.event_y                  = 0
        self.anchor_line_coords       = [0, 0]
        self.text_box                 = None
        self.funcid_delete            = None
        self.func_id_motion           = None
        self.func_id_button           = None
        self.func_id_leave            = None
        self.func_id_escape           = None
        self.func_id_button_release   = None
        self.sym_bind_funcid_button1  = None
        self.sym_bind_funcid_dbutton1 = None
        self.sym_bind_funcid_button3  = None
        self.sym_bind_funcid_enter    = None
        self.sym_bind_funcid_leave    = None
        self.background_rectangle     = None
        self.old_signal_name_coords   = None
        self.after_identifier         = None
        if self.design.get_language()=="VHDL":
            self.declaration = "dummy : std_logic"
        else:
            self.declaration = "wire dummy"
        # The tag self.wire_tag is needed by notebook_diagram_tab.__complete_selection().
        # The tag self.wire_tag_signal_name is needed by wire_insertion.move_signal_name().
        self.canvas_id = diagram_tab.canvas.create_text(coords,
                                                        text=self.declaration, activefill="red",
                                                        anchor="sw", angle=self.angle, font=("Courier", self.design.get_font_size()),
                                                        tags=("signal-name", self.wire_tag, self.wire_tag + "_signal_name", "layer1", "schematic-element"))
        self.__process_new_declaration(declaration, False) # The given declaration overwrites the "dummy".
        self.store_item(push_design_to_stack=False, signal_design_change=False)
        self.__add_bindings_to_signal_name()

    def select_item(self):
        self.__highlight()
        self.__remove_bindings_from_signal_name()

    def unselect_item(self):
        self.__unhighlight()
        self.__add_bindings_to_signal_name()

    def get_declaration(self):
        return self.declaration

    def __highlight(self):
        self.diagram_tab.canvas.itemconfigure(self.canvas_id, fill="red")

    def __unhighlight(self):
        self.diagram_tab.canvas.itemconfigure(self.canvas_id, fill="black")

    def get_canvas_id(self):
        return self.canvas_id

    def store_item(self, push_design_to_stack, signal_design_change):
        coords = self.diagram_tab.canvas.coords(self.canvas_id)
        self.design.store_signal_name_in_canvas_dictionary(self.canvas_id, self, coords, self.angle, self.declaration, self.wire_tag,
                                                           push_design_to_stack, signal_design_change)

    def __add_bindings_to_signal_name(self):
        self.sym_bind_funcid_button1  = self.diagram_tab.canvas.tag_bind(self.canvas_id,"<Button-1>"       , self.__move_start_signal_name          )
        self.sym_bind_funcid_dbutton1 = self.diagram_tab.canvas.tag_bind(self.canvas_id,"<Double-Button-1>", lambda event: self.__edit_signal_name())
        self.sym_bind_funcid_button3  = self.diagram_tab.canvas.tag_bind(self.canvas_id,"<ButtonRelease-3>", lambda event: self.__rotate_after_idle()          )
        self.sym_bind_funcid_enter    = self.diagram_tab.canvas.tag_bind(self.canvas_id,"<Enter>"          , lambda event: self.__at_enter()        )
        self.sym_bind_funcid_leave    = self.diagram_tab.canvas.tag_bind(self.canvas_id,"<Leave>"          , lambda event: self.__at_leave()        )

    def __rotate_after_idle(self):
        # "After" got necessary because ButtonRelease-3 is bound to 2 actions:
        #   __zoom_area (in notebook_diagram_tab, not only used for zoom but also for the drawing-area-background-menu)
        #   self.__rotate
        # If __zoom_area detects a zoom-rectangle with size 0, the background-menu is opened (workaround to have zoom and background-menu both at Button-3).
        # The background-menu will only be drawn if the mouse pointer is not over any other object.
        # So when a signal-name is rotated by Button-3 no background-menu should show, as the mouse-pointer is over the signal-name.
        # But as (for unknown reasons) always first the signal-name is rotated and disappears from the mouse-pointer,
        # afterwards always the background-menu showed.
        # By using "after" now first the button3 event __zoom_area is handled and as the signal-name is not rotated yet,
        # it is still under the mouse-pointer and no background-menu pops up.
        # Then after idle the signal-name is rotated.
        self.diagram_tab.canvas.after_idle(self.__rotate)

    def __rotate(self):
        self.angle = float(self.diagram_tab.canvas.itemcget(self.canvas_id, "angle"))
        self.angle += 90 % 360
        self.diagram_tab.canvas.itemconfigure(self.canvas_id, angle=str(self.angle))
        self.store_item(push_design_to_stack=True, signal_design_change=True)

    def __remove_bindings_from_signal_name(self):
        self.diagram_tab.canvas.tag_unbind(self.canvas_id,"<Button-1>"       , self.sym_bind_funcid_button1 )
        self.diagram_tab.canvas.tag_unbind(self.canvas_id,"<Double-Button-1>", self.sym_bind_funcid_dbutton1)
        self.diagram_tab.canvas.tag_unbind(self.canvas_id,"<Button-3>"       , self.sym_bind_funcid_button3 )
        self.diagram_tab.canvas.tag_unbind(self.canvas_id,"<Enter>"          , self.sym_bind_funcid_enter   )
        self.diagram_tab.canvas.tag_unbind(self.canvas_id,"<Leave>"          , self.sym_bind_funcid_leave   )
        self.sym_bind_funcid_button1  = None
        self.sym_bind_funcid_dbutton1 = None
        self.sym_bind_funcid_button3  = None
        self.sym_bind_funcid_enter    = None
        self.sym_bind_funcid_leave    = None

    def __move_start_signal_name(self, event):
        self.func_id_motion         = self.diagram_tab.canvas.tag_bind(self.canvas_id, "<Motion>"         , self.__move_to )
        self.func_id_button_release = self.diagram_tab.canvas.tag_bind(self.canvas_id, "<ButtonRelease-1>", self.__move_end)
        self.event_x = self.diagram_tab.canvas.canvasx(event.x)
        self.event_y = self.diagram_tab.canvas.canvasy(event.y)
        self.old_signal_name_coords = self.diagram_tab.canvas.coords(self.canvas_id)
        for canvas_item in self.diagram_tab.canvas.find_withtag(self.wire_tag):
            if self.diagram_tab.canvas.type(canvas_item)=="line":
                wire_coords = self.diagram_tab.canvas.coords(canvas_item)
                if wire_coords[0]==wire_coords[2]: # Vertical
                    self.anchor_line_coords[0] = wire_coords[0]
                    self.anchor_line_coords[1] = (wire_coords[1] + wire_coords[3])/2
                else:
                    self.anchor_line_coords[0] = (wire_coords[0] + wire_coords[2])/2
                    self.anchor_line_coords[1] = wire_coords[1]
                self.anchor_line = self.diagram_tab.canvas.create_line(self.anchor_line_coords[0], self.anchor_line_coords[1], self.event_x, self.event_y, dash=(2,3), fill="red")

    def __move_to(self, event):
        new_event_x = self.diagram_tab.canvas.canvasx(event.x)
        new_event_y = self.diagram_tab.canvas.canvasy(event.y)
        self.diagram_tab.canvas.move(self.canvas_id, new_event_x-self.event_x, new_event_y-self.event_y)
        self.event_x = new_event_x
        self.event_y = new_event_y
        self.diagram_tab.canvas.coords(self.anchor_line, self.anchor_line_coords[0], self.anchor_line_coords[1], self.event_x, self.event_y)

    def __move_end(self, event):
        self.diagram_tab.canvas.tag_unbind(self.canvas_id, "<Motion>"         , self.func_id_motion)
        self.diagram_tab.canvas.tag_unbind(self.canvas_id, "<ButtonRelease-1>", self.func_id_button_release)
        self.func_id_motion = None
        self.func_id_button_release = None
        self.__move_to_grid()
        self.diagram_tab.canvas.delete(self.anchor_line)
        self.__unhighlight()
        new_signal_name_coords = self.diagram_tab.canvas.coords(self.canvas_id)
        if new_signal_name_coords!=self.old_signal_name_coords:
            self.store_item(push_design_to_stack=True, signal_design_change=True)

    def __move_to_grid(self):
        # Determine the distance of the anchor point of the symbol to the grid:
        anchor_x, anchor_y = self.diagram_tab.canvas.coords(self.canvas_id)[0:2]
        remainder_x = anchor_x % self.design.get_grid_size()
        remainder_y = anchor_y % self.design.get_grid_size()
        # Move the symbol to the grid:
        delta_x = - remainder_x
        delta_y = - remainder_y
        if remainder_x>self.design.get_grid_size()/2:
            delta_x += self.design.get_grid_size()
        if remainder_y>self.design.get_grid_size()/2:
            delta_y += self.design.get_grid_size()
        self.diagram_tab.canvas.move(self.canvas_id, delta_x, delta_y)

    def __at_enter(self):
        self.__highlight()
        self.after_identifier = self.diagram_tab.canvas.after(1000, self.__show_full_declaration)

    def __show_full_declaration(self):
        self.diagram_tab.canvas.itemconfigure(self.canvas_id, text=self.declaration, font=("Courier", 10))
        self.background_rectangle = self.diagram_tab.canvas.create_rectangle(self.diagram_tab.canvas.bbox(self.canvas_id), fill="white")
        list_of_canvas_items = self.diagram_tab.canvas.find_overlapping(*self.diagram_tab.canvas.bbox(self.canvas_id))
        for item in list_of_canvas_items:
            self.diagram_tab.canvas.tag_raise(self.canvas_id, item)
        self.diagram_tab.canvas.tag_lower (self.background_rectangle, self.canvas_id)

    def __at_leave(self):
        if self.after_identifier is not None:
            self.diagram_tab.canvas.after_cancel(self.after_identifier)
        if self.background_rectangle is not None:
            self.diagram_tab.canvas.delete(self.background_rectangle)
            self.background_rectangle = None
        self.diagram_tab.canvas.itemconfigure(self.canvas_id, text=self.__get_part_to_show_from_declaration(self.declaration), font=("Courier", self.design.get_font_size()))
        self.__unhighlight()

    def delete_item(self, push_design_to_stack):
        self.delete_entry_window()
        self.design.remove_canvas_item_from_dictionary(self.canvas_id, push_design_to_stack)
        self.diagram_tab.canvas.delete(self.canvas_id)
        del self # Once the last reference to an object is deleted, the object will be removed by garbage collection.

    def __edit_signal_name(self):
        if SignalName.signal_name_under_edit is not None: # Then another signal is edited at this moment.
            SignalName.signal_name_under_edit.update_signal_name(all_signals=False)
        SignalName.signal_name_under_edit = self
        self.text_box = ttk.Entry(self.diagram_tab.canvas, width=len(self.declaration), justify="left", font=("Courier", self.design.get_font_size()) )
        self.text_box.insert("end", self.declaration)
        self.text_box.icursor(0)
        self.text_box.focus_set()
        coords = self.diagram_tab.canvas.coords(self.canvas_id)
        self.diagram_tab.canvas.create_window(coords, window=self.text_box, anchor="sw", tag="entry-window")
        self.text_box.bind('<Key>'           , lambda event: self.__increase_length())
        self.text_box.bind('<Return>'        , lambda event, all_signals=False: self.update_signal_name(all_signals))
        self.text_box.bind('<Control-Return>', lambda event, all_signals=True : self.update_signal_name(all_signals))
        self.text_box.bind('<Escape>'        , lambda event: self.delete_entry_window())
        self.design.signal_name_edit_list_append(self)

    def __increase_length(self):
        new_length = len(self.text_box.get())
        if new_length>len(self.declaration):
            self.text_box.configure(width=new_length)

    def update_signal_name(self, all_signals):
        new_declaration = self.text_box.get()
        if   self.design.get_language()=="VHDL" and (new_declaration.find(":")==-1 or
                                               new_declaration.startswith(":")     or
                                               new_declaration.endswith  (":")):
            messagebox.showerror("Error in HDL-SCHEM-Editor",
                                 "The signal-name must be entered in this form:\n<signal-name>[(sub-range)] : <signal_type with range> [:= <init-value]")
        elif self.design.get_language()=="Verilog" and ((new_declaration.find("reg")==-1 and new_declaration.find("wire")==-1) or
                                                         new_declaration.find("("  )!=-1 or
                                                         new_declaration.find(")"  )!=-1 ):
            messagebox.showerror("Error in HDL-SCHEM-Editor",
                                 "The signal-name must be entered in this form:\nreg|wire [7:4] <signal-name (w/o range)> <: sub-range of signal-range>")
        elif self.design.get_language()=="SystemVerilog" and ((new_declaration.find("reg")==-1 and new_declaration.find("wire")==-1 and new_declaration.find("logic")==-1) or
                                                         new_declaration.find("("  )!=-1 or
                                                         new_declaration.find(")"  )!=-1 ):
            messagebox.showerror("Error in HDL-SCHEM-Editor",
                                 "The signal-name must be entered in this form:\nreg|wire|logic [7:4] <signal-name (w/o range)> <: sub-range of signal-range>")
        else:
            self.__process_new_declaration(new_declaration, all_signals)
            for canvas_item in self.diagram_tab.canvas.find_withtag(self.wire_tag):
                if self.diagram_tab.canvas.type(canvas_item)=="line":
                    wire_ref = self.diagram_tab.design.get_references([canvas_item])[0]
                    wire_ref.store_item(push_design_to_stack=True, signal_design_change=True) # Must be stored, as the width of the wire may have changed.
        self.delete_entry_window()

    def delete_entry_window(self):
        self.design.signal_name_edit_list_remove(self) # Needed if an entry window is open, when the wire and the signal-name are deleted.
        SignalName.signal_name_under_edit = None
        if self.text_box is not None:
            self.text_box.destroy()
            self.text_box = None
            self.diagram_tab.canvas.delete("entry-window")

    def __get_part_to_show_from_declaration(self, declaration):
        signal_name, signal_sub_range, signal_type, _, _, signal_record_slice = hdl_generate_functions.HdlGenerateFunctions.split_declaration(declaration, self.design.get_language())
        #print("signal_type =", signal_type)
        if signal_sub_range!="":
            visible_range = signal_sub_range
            # When a sub_range exists the complete range must be removed from the signal name (is only part of the signal_name in Verilog designs):
            signal_name = re.sub(r"\[.*\]", "", signal_name)
        else:
            # If there is no subrange but the signal is an array, then the array range shall be shown:
            if self.design.get_language()=="VHDL":
                open_bracket  = '('
                close_bracket = ')'
            else:
                open_bracket  = '['
                close_bracket = ']'
            open_bracket_index = signal_type.find(open_bracket)
            # The check for " range " is only a check for VHDL, it is not clear if something similar is needed for Verilog:
            if open_bracket_index!=-1 and " range " not in signal_type:
                close_bracket_index = signal_type.rfind(close_bracket)
                visible_range = signal_type[open_bracket_index:close_bracket_index+1]
            else:
                visible_range = ""
        visible_range = re.sub(r" downto ", ":", visible_range)
        visible_range = re.sub(r" to "    , ":", visible_range)
        # Do not show unnecessary blanks around ':', '+', '-', '*', '/':
        visible_range = re.sub(r"\s*:\s*" , ":" , visible_range)
        visible_range = re.sub(r"\s*\+\s*", "+" , visible_range)
        visible_range = re.sub(r"\s*-\s*" , "-" , visible_range)
        visible_range = re.sub(r"\s*\*\s*", "*" , visible_range)
        visible_range = re.sub(r"\s*\/\s*", "/" , visible_range)
        return signal_name + visible_range + signal_record_slice

    def get_object_tag(self):
        return self.wire_tag + "_signal_name"

    def __process_new_declaration(self, new_declaration, all_signals):
        # The new declaration has all the information about the wire.
        # If the signal name was not changed (Change net properties):
        #  Then sub_range or type or init-value or comment may got changed.
        #  The new declaration can be completely used for this wire.
        #  If there is any other wire with this name (implicitely CTRL-pressed):
        #     The new type       will be used for all wires which have the not changed signal name.
        #     The new init-value will be used for all wires which have the not changed signal name.
        #     The new comment    will be used for all wires which have the not changed signal name.
        # If the signal name was changed and CTRL was not pressed:
        #  If there is no other wire which has the new signal name (Rename signal).
        #     The new declaration can be directly used for this wire.
        #  Else (Reconnect signal):
        #     This wire is now connected to an already existing wire.
        #     From the new declaration only signal name and signal range are used for this wire, all other information is copied from the already existing wire.
        #     From the new declaration the signal type is not used (if it would be used, then the type of the new declaration
        #     must be adapted by the user to the type of the existing wire in most of the cases).
        # If the signal name was changed and CTRL was pressed (All other wires which have the old signal name shall also get the changes):
        #  If there is no other wire which has the new signal name  (Rename net).
        #     The new declaration can be directly used for this wire.
        #     The new declaration (except the subrange) can be directly used for all the wires with the old signal name.
        #  Else (Reconnect net):
        #     This wire is now connected to an already existing wire and the other signals with the old signal name are also connected to the already existing wire.
        #     From the new declaration only wire name and wire range are used for this wire, type, init, comment are copied from the already existing wire.
        #     From the new declaration only wire name is used for all other wires with old name, range is kept unchanged, type, init, comment are copied from the wire connected to.
        new_signal_name, new_sub_range, new_signal_type, new_comment, new_init, new_signal_record_slice = hdl_generate_functions.HdlGenerateFunctions.split_declaration(
                                                                                                                              new_declaration , self.design.get_language())
        # Build a new declaration without any obsolete blanks:
        if new_init!="": # init is only supported by a VHDL declaration
            new_init = ' ' + new_init
        if new_comment!="":
            new_comment = ' ' + new_comment
        if self.design.get_language()=="VHDL":
            new_declaration = new_signal_name + new_sub_range + new_signal_record_slice + " : "  + new_signal_type + new_init + new_comment
        else: # Verilog
            if new_sub_range!="":
                #new_sub_range += " "
                new_sub_range = " : " + new_sub_range + " "
            new_declaration = new_signal_type + ' ' + new_signal_name + new_sub_range + new_comment
        old_signal_name, _, _, _, _, _ = hdl_generate_functions.HdlGenerateFunctions.split_declaration(self.declaration, self.design.get_language())
        if new_signal_name==old_signal_name: # Only the other properties of wire (or net) are changed.
            self.change_declaration(new_declaration)
            self.__propagate_all_but_subrange_to_other_wires_with_old_signal_name(old_signal_name, new_signal_name, new_signal_type, new_init, new_comment)
        else:
            other_references = self.__get_signal_name_references_with_name(new_signal_name)
            if not other_references: # No other wire with new_signal_name exists, so rename wire (and update other properties).
                self.change_declaration(new_declaration)
                if all_signals: # Rename complete net (and update other properties)
                    self.__propagate_all_but_subrange_to_other_wires_with_old_signal_name(old_signal_name, new_signal_name, new_signal_type,
                                                                                          new_init, new_comment)
            else: # Connect wire to other wire.
                existing_signal_type, existing_init, existing_comment = self.__get_type_and_init_and_comment_from_a_wire_which_already_has_the_new_name(
                                                                               other_references, new_signal_type, new_comment)
                if existing_init!="": # init is only supported by a VHDL declaration
                    existing_init = " " + existing_init
                if existing_comment!="":
                    existing_comment = " " + existing_comment
                if self.design.get_language()=="VHDL":
                    modified_declaration = new_signal_name + new_sub_range + new_signal_record_slice + " : "  + existing_signal_type + existing_init + existing_comment
                else: # Verilog
                    modified_declaration = existing_signal_type + ' ' + new_signal_name + new_sub_range + existing_comment
                self.change_declaration(modified_declaration)
                if all_signals: # Connect complete net to other wire.
                    self.__propagate_all_but_subrange_to_other_wires_with_old_signal_name(old_signal_name, new_signal_name, existing_signal_type,
                                                                                          existing_init, existing_comment)

    def __get_type_and_init_and_comment_from_a_wire_which_already_has_the_new_name(self, signal_name_references_with_new_name, new_signal_type, new_comment):
        other_declaration = signal_name_references_with_new_name[0].get_declaration() # Read only 1 declaration.
        _, _, new_signal_type, new_comment, new_init, _ = hdl_generate_functions.HdlGenerateFunctions.split_declaration(other_declaration, self.design.get_language())
        return new_signal_type, new_init, new_comment

    def __propagate_all_but_subrange_to_other_wires_with_old_signal_name(self, old_signal_name, new_signal_name, new_signal_type, new_init, new_comment):
        signal_name_references_with_old_name = self.__get_signal_name_references_with_name(old_signal_name)
        if signal_name_references_with_old_name:
            for signal_name_reference_with_old_name in signal_name_references_with_old_name:
                if signal_name_reference_with_old_name!=self:
                    other_declaration = signal_name_reference_with_old_name.get_declaration()
                    _, other_signal_range, _, _, _, other_signal_record_slice = hdl_generate_functions.HdlGenerateFunctions.split_declaration(other_declaration,
                                                                                                                                              self.design.get_language())
                    if new_init!='' and not new_init.startswith(' '):
                        new_init = ' ' + new_init
                    if new_comment!='' and not new_comment.startswith(' '):
                        new_comment = ' ' + new_comment
                    if self.design.get_language()=="VHDL":
                        signal_name_reference_with_old_name.change_declaration(new_signal_name + other_signal_range + other_signal_record_slice + " : "
                                                                               + new_signal_type + new_init + new_comment)
                    else:
                        if other_signal_range!="":
                            other_signal_range = ':' + other_signal_range
                        signal_name_reference_with_old_name.change_declaration(new_signal_type + ' ' + new_signal_name + other_signal_range + new_comment)

    def __get_signal_name_references_with_name(self, signal_name):
        identical_name_references = []
        signal_name_references = self.design.get_list_of_canvas_signal_name_references()
        for signal_name_reference in signal_name_references:
            other_signal_name, _, _ , _, _, _ = hdl_generate_functions.HdlGenerateFunctions.split_declaration(signal_name_reference.declaration, self.design.get_language())
            if other_signal_name==signal_name:
                identical_name_references.append(signal_name_reference)
        return identical_name_references

    def set_declaration_if_signal_names_differ(self, new_declaration): # called from WireMove.__change_signal_name_if_connected_to_other_wire()
        old_signal_name, _, _, _, _, _ = hdl_generate_functions.HdlGenerateFunctions.split_declaration(self.declaration, self.design.get_language())
        new_signal_name, _, _, _, _, _ = hdl_generate_functions.HdlGenerateFunctions.split_declaration(new_declaration , self.design.get_language())
        if new_signal_name!=old_signal_name:
            self.change_declaration(new_declaration)

    def change_declaration(self, new_declaration):
        self.declaration = new_declaration
        self.diagram_tab.canvas.itemconfigure(self.canvas_id, text=self.__get_part_to_show_from_declaration(new_declaration))
        self.__adapt_line_thickness()
        self.store_item(push_design_to_stack=False, signal_design_change=False)

    def __adapt_line_thickness(self):
        canvas_id_line = None
        list_of_canvas_ids = self.diagram_tab.canvas.find_withtag(self.wire_tag)
        for canvas_id in list_of_canvas_ids:
            if self.diagram_tab.canvas.type(canvas_id)=="line" and "grid_line" not in self.diagram_tab.canvas.gettags(canvas_id):
                canvas_id_line = canvas_id
        # When reading from a file, there might be the corresponding wire not be inserted into the canvas.
        # But then the thickness is stored in file and must not be updated after the wire was drawn.
        if canvas_id_line:
            declaration = self.declaration.lower()
            if self.design.get_language()=="VHDL":
                declaration_without_comment = re.sub(r"--.*", "", declaration)
                bus_identifiers = ['(', "integer", "natural", "positive", "real"]
            else: # Verilog
                declaration_without_comment = re.sub(r"//.*", "", declaration)
                bus_identifiers = ['[', "integer", "time", "real"]
            if any(bus_identifier in declaration_without_comment for bus_identifier in bus_identifiers):
                self.diagram_tab.canvas.itemconfigure(canvas_id_line, width=3)
            else:
                self.diagram_tab.canvas.itemconfigure(canvas_id_line, width=1)

    def add_pasted_tag_to_all_canvas_items(self):
        self.diagram_tab.canvas.addtag_withtag("pasted_tag", self.canvas_id)

    def adapt_coordinates_by_factor(self, factor):
        coords = self.diagram_tab.canvas.coords(self.canvas_id)
        coords = [value*factor for value in coords]
        self.diagram_tab.canvas.coords(self.canvas_id, coords)
