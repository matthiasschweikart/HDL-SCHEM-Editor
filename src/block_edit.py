""" Stuff for editing the text of a block """
from tkinter import messagebox
import subprocess
import os
import re
import shlex

import custom_text
import block_rectangle
import vhdl_parsing
import verilog_parsing
import edit_ext

class BlockEdit():
    def __init__(self,
                 parent,
                 window,      # : schematic_window.SchematicWindow,
                 diagram_tab, # : notebook_diagram_tab.NotebookDiagramTab,
                 rectangle   : block_rectangle.BlockRectangle,
                 canvas_id_text,
                 canvas_id_rectangle,
                 use_external_editor):
        self.parent               = parent
        self.window               = window
        self.diagram_tab          = diagram_tab
        self.canvas_id_rectangle  = canvas_id_rectangle
        self.canvas_id_text       = canvas_id_text
        self.use_external_editor  = use_external_editor
        self.old_rectangle_coords = None
        self.window_coords        = None
        self.after_identifier     = None
        self.old_text = diagram_tab.canvas.itemcget(canvas_id_text, "text")
        self.old_text = self.parent.remove_blanks_at_line_ends(self.old_text)
        if self.window.notebook_top.control_tab.language.get()=="VHDL":
            parser = vhdl_parsing.VhdlParser
        else:
            parser = verilog_parsing.VerilogParser
        if self.use_external_editor:
            self.__edit_in_external_editor(self.old_text)
        else:
            self.text_edit_widget = custom_text.CustomText(self.window, window=self.window, parser=parser, relief="flat", borderwidth=0,highlightthickness=0,
                                                                tag_position_list=parser.tag_position_list, font=("Courier", self.window.design.get_font_size()),
                                                                text_name="block_edit", store_in_design=False, undo=True, maxundo=-1)
            self.window_coords = list(self.diagram_tab.canvas.bbox(self.canvas_id_text))
            self.canvas_window_for_text_edit_widget = diagram_tab.canvas.create_window(self.window_coords[0]-1, self.window_coords[1],
                                                                    width =self.window_coords[2]-self.window_coords[0]+3,
                                                                    height=self.window_coords[3]-self.window_coords[1]+3,
                                                                    anchor="nw", window=self.text_edit_widget)
            self.window.design.set_block_edit_is_running(True) # Needed to prevent <Focus-In> from binding <Control-s> again in menu_bar.create_binding__for_menu_accelerators().
            self.window.unbind_all("<Control-s>") # <Control-s> is needed for saving the block edit.
            self.text_edit_widget.bind("<Escape>"   , lambda event: self.__close_edit_window_by_escape())
            self.text_edit_widget.bind("<Control-s>", lambda event: self.__save())
            self.text_edit_widget.bind("<Key>"      , lambda event: self._adapt_window_size_and_highlighting_after_idle())
            self.text_edit_widget.insert_text(self.old_text, state_after_insert="normal")
            self.text_edit_widget.focus_set()
            self.window.design.block_edit_list_append(self)

    def __close_edit_window_by_escape(self):
        new_text = self.text_edit_widget.get("1.0", "end - 1 chars")
        if new_text!=self.old_text:
            message  = "This block has unsaved changes, do you want to store them?"
            answer = messagebox.askquestion("HDL-Schem-Editor:", message, default="yes")
            if answer=="yes":
                self.__save()
        self.close_edit_window()

    def __save(self, new_text=""):
        self.old_rectangle_coords = self.diagram_tab.canvas.coords(self.canvas_id_rectangle)
        if self.use_external_editor:
            text = new_text
        else:
            text = self.text_edit_widget.get("1.0", "end - 1 chars")
        text = self.parent.fill_all_lines_with_blanks_to_equal_length(text)
        self.diagram_tab.canvas.itemconfigure(self.canvas_id_text, text=text)
        # When a new text of a block is saved, then the rectangle of the block must get a new shape adapted to the new text.
        # As the new text is created here, also the shape is modified here.
        # After the shape has got a new size, it is also moved back to the grid, by calling move_to_the_grid() of the BlockInsertion class.
        # At block movements the references to all connected wires are handed over to this method.
        # But at block edits there is no common move delta for all the wires which are connected to top, bottom, left, right of the block.
        # So the handed over wire reference list is kept empty and the fix of the wire connections is handled here after
        # the block has got its new size and position by self.__adapt_end_points_of_connected_wires.
        # This feature was removed, because it did not work correct in all cases and in the meantime manually resizing of blocks is possible:
        # references_to_connected_wires = []
        # new_rectangle_coords = self.__adapt_rectangle_to_new_text(references_to_connected_wires)
        # self.__adapt_end_points_of_connected_wires(new_rectangle_coords)
        self.parent.store_item(push_design_to_stack=True, signal_design_change=True)
        self.old_text = self.parent.remove_blanks_at_line_ends(text)
        if self.use_external_editor:
            self.__finish_editing()
        else:
            self.close_edit_window()

    def close_edit_window(self):
        self.parent.block_edit_ref = None
        self.diagram_tab.canvas.delete(self.canvas_window_for_text_edit_widget)
        self.text_edit_widget.destroy()
        self.window.design.set_block_edit_is_running(False) # The next <FocusIn> event will bind <Control-s> to file_write again.
        if self in self.window.design.get_block_edit_list():
            self.window.design.block_edit_list_remove(self)
        self.__finish_editing()

    def __finish_editing(self):
        del self # Once the last reference to an object is deleted, the object will be removed by garbage collection.

    def _adapt_window_size_and_highlighting_after_idle(self):
        if self.after_identifier is not None:
            self.text_edit_widget.after_cancel(self.after_identifier)
        self.after_identifier = self.text_edit_widget.after(300, self.__adapt_window_size_and_highlighting) # wait 300 ms

    def __adapt_window_size_and_highlighting(self):
        old_width  = self.window_coords[2] - self.window_coords[0]
        old_height = self.window_coords[3] - self.window_coords[1]
        new_window_coords = self.__determine_the_new_size_of_the_text_item()
        new_width  = new_window_coords[2] - new_window_coords[0]
        new_height = new_window_coords[3] - new_window_coords[1]
        if new_width>old_width:
            self.diagram_tab.canvas.itemconfigure(self.canvas_window_for_text_edit_widget, width =new_width)
            self.window_coords[2] = self.window_coords[0] + new_width
        if new_height>old_height:
            self.diagram_tab.canvas.itemconfigure(self.canvas_window_for_text_edit_widget, height=new_height)
            self.window_coords[3] = self.window_coords[1] + new_height
        self.text_edit_widget.add_syntax_highlight_tags()

    def __determine_the_new_size_of_the_text_item(self):
        new_text = self.text_edit_widget.get("1.0", "end - 1 chars")
        coords = self.diagram_tab.canvas.coords(self.canvas_id_text)
        canvas_id_tmp = self.diagram_tab.canvas.create_text(*coords, text=new_text, font=("Courier", self.window.design.get_font_size()))
        text_coords = self.diagram_tab.canvas.bbox(canvas_id_tmp)
        self.diagram_tab.canvas.delete(canvas_id_tmp)
        # Increase the size a little bit, because sometimes the window is 1 character too small:
        text_coords = [text_coords[0]-2, text_coords[1]-2,
                                  text_coords[2]+2, text_coords[3]+2]
        return text_coords

    def __edit_in_external_editor(self, old_text):
        if self.window.design.get_language()=="VHDL":
            file_name_tmp = "hdl-schem-editor.tmp.vhd"
        else:
            file_name_tmp = "hdl-schem-editor.tmp.v"
        fileobject = open(file_name_tmp, 'w', encoding="utf-8")
        fileobject.write(old_text)
        fileobject.close()
        edit_ext.EditExt(self.window.design, file_name_tmp)
        fileobject = open(file_name_tmp, 'r', encoding="utf-8")
        new_text = fileobject.read()
        new_text = self.__replace_tabs_by_4_blanks(new_text)
        fileobject.close()
        os.remove(file_name_tmp)
        if new_text!=self.old_text:
            self.__save(new_text)

    def __replace_tabs_by_4_blanks(self, text):
        return re.sub("\\t", "    ", text)
