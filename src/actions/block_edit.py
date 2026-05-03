"""Stuff for editing the text of a block"""

import os
import re
from tkinter import messagebox

from actions import edit_ext
from hdl_parser import verilog_parsing, vhdl_parsing
from widgets import custom_text


class BlockEdit:
    """This class is used for editing the text of a block."""

    def __init__(
        self,
        parent,
        window,  # : schematic_window.SchematicWindow,
        diagram_tab,  # : notebook_diagram_tab.NotebookDiagramTab,
        canvas_id_text,
        canvas_id_rectangle,
        use_external_editor,
    ):
        self.parent = parent
        self.window = window
        self.diagram_tab = diagram_tab
        self.canvas_id_rectangle = canvas_id_rectangle
        self.canvas_id_text = canvas_id_text
        self.use_external_editor = use_external_editor
        self.old_rectangle_coords = None
        self.window_coords = None
        self.after_identifier = None
        if self.parent.text_is_shortened:
            short_text = diagram_tab.canvas.itemcget(canvas_id_text, "text")
            self.old_text = self.window.design.get_text_of_block(self.canvas_id_text)
            self.diagram_tab.canvas.itemconfigure(self.canvas_id_text, text=self.old_text)
            self.window_coords = list(self.diagram_tab.canvas.bbox(self.canvas_id_text))
            self.diagram_tab.canvas.itemconfigure(self.canvas_id_text, text=short_text)
        else:
            self.old_text = diagram_tab.canvas.itemcget(canvas_id_text, "text")
            self.window_coords = list(self.diagram_tab.canvas.bbox(self.canvas_id_text))
        self.old_text = self.parent.remove_blanks_at_line_ends(self.old_text)
        if self.window.notebook_top.control_tab.language.get() == "VHDL":
            parser = vhdl_parsing.VhdlParser
        else:
            parser = verilog_parsing.VerilogParser
        if self.use_external_editor:
            self._edit_in_external_editor(self.old_text)
        else:
            self.text_edit_widget = custom_text.CustomText(
                diagram_tab.canvas,
                window=self.window,
                parser=parser,
                relief="flat",
                borderwidth=0,
                highlightthickness=0,
                position_tags=parser.position_tags,
                font=("Courier", self.window.design.get_font_size()),
                text_name="block_edit",
                store_in_design=False,
                undo=True,
                maxundo=-1,
            )
            self.canvas_window_for_text_edit_widget = diagram_tab.canvas.create_window(
                self.window_coords[0] - 1,
                self.window_coords[1],
                width=self.window_coords[2] - self.window_coords[0] + 3,
                height=self.window_coords[3] - self.window_coords[1] + 3,
                anchor="nw",
                window=self.text_edit_widget,
            )
            # Needed to prevent <Focus-In> from binding <Control-s> again
            # in menu_bar.create_binding__for_menu_accelerators():
            self.window.design.set_block_edit_is_running(True)
            self.window.unbind_all("<Control-s>")  # <Control-s> is needed for saving the block edit.
            self.text_edit_widget.bind("<Escape>", lambda event: self._close_edit_window_by_escape())
            self.text_edit_widget.bind("<Control-s>", lambda event: self._save())
            self.text_edit_widget.bind("<Key>", lambda event: self._adapt_window_size_and_highlighting_after_idle())
            self.text_edit_widget.insert_text(self.old_text, state_after_insert="normal")
            self.text_edit_widget.add_syntax_highlight_tags()
            self.text_edit_widget.focus_set()
            self.window.design.block_edit_list_append(self)

    def _close_edit_window_by_escape(self):
        new_text = self.text_edit_widget.get("1.0", "end - 1 chars")
        if new_text != self.old_text:
            message = "This block has unsaved changes, do you want to store them?"
            answer = messagebox.askquestion("HDL-Schem-Editor:", message, default="yes")
            if answer == "yes":
                self._save()
        self.close_edit_window()

    def _save(self, new_text=""):
        self.old_rectangle_coords = self.diagram_tab.canvas.coords(self.canvas_id_rectangle)
        text = new_text if self.use_external_editor else self.text_edit_widget.get("1.0", "end - 1 chars")
        text = self.parent.fill_all_lines_with_blanks_to_equal_length(text)
        self.diagram_tab.canvas.itemconfigure(self.canvas_id_text, text=text)
        self.parent.text_is_shortened = False
        self.parent.store_item(push_design_to_stack=True, signal_design_change=True)
        self.old_text = self.parent.remove_blanks_at_line_ends(text)
        if self.use_external_editor:
            self._finish_editing()
        else:
            self.close_edit_window()

    def close_edit_window(self):
        """This is called when the block edit window should be closed, either by pressing Escape or after saving."""
        self.parent.block_edit_ref = None
        self.diagram_tab.canvas.delete(self.canvas_window_for_text_edit_widget)
        self.text_edit_widget.destroy()
        # The next <FocusIn> event will bind <Control-s> to file_write again:
        self.window.design.set_block_edit_is_running(False)
        if self in self.window.design.get_block_edit_list():
            self.window.design.block_edit_list_remove(self)
        self._finish_editing()

    def _finish_editing(self):
        del self  # Once the last reference to an object is deleted, the object will be removed by garbage collection.

    def _adapt_window_size_and_highlighting_after_idle(self):
        if self.after_identifier is not None:
            self.text_edit_widget.after_cancel(self.after_identifier)
        self.after_identifier = self.text_edit_widget.after(
            300, self._adapt_window_size_and_highlighting
        )  # wait 300 ms

    def _adapt_window_size_and_highlighting(self):
        old_width = self.window_coords[2] - self.window_coords[0]
        old_height = self.window_coords[3] - self.window_coords[1]
        new_window_coords = self._determine_the_new_size_of_the_text_item()
        new_width = new_window_coords[2] - new_window_coords[0]
        new_height = new_window_coords[3] - new_window_coords[1]
        if new_width > old_width:
            self.diagram_tab.canvas.itemconfigure(self.canvas_window_for_text_edit_widget, width=new_width)
            self.window_coords[2] = self.window_coords[0] + new_width
        if new_height > old_height:
            self.diagram_tab.canvas.itemconfigure(self.canvas_window_for_text_edit_widget, height=new_height)
            self.window_coords[3] = self.window_coords[1] + new_height
        self.text_edit_widget.add_syntax_highlight_tags()

    def _determine_the_new_size_of_the_text_item(self):
        new_text = self.text_edit_widget.get("1.0", "end - 1 chars")
        coords = self.diagram_tab.canvas.coords(self.canvas_id_text)
        canvas_id_tmp = self.diagram_tab.canvas.create_text(
            *coords, text=new_text, font=("Courier", self.window.design.get_font_size())
        )
        text_coords = self.diagram_tab.canvas.bbox(canvas_id_tmp)
        self.diagram_tab.canvas.delete(canvas_id_tmp)
        # Increase the size a little bit, because sometimes the window is 1 character too small:
        text_coords = [text_coords[0] - 2, text_coords[1] - 2, text_coords[2] + 2, text_coords[3] + 2]
        return text_coords

    def _edit_in_external_editor(self, old_text):
        if self.window.design.get_language() == "VHDL":
            file_name_tmp = "hdl-schem-editor.tmp.vhd"
        else:
            file_name_tmp = "hdl-schem-editor.tmp.v"
        with open(file_name_tmp, "w", encoding="utf-8") as fileobject:
            fileobject.write(old_text)
        edit_ext.EditExt(self.window.design, file_name_tmp)
        with open(file_name_tmp, encoding="utf-8") as fileobject:
            new_text = fileobject.read()
        new_text = self._replace_tabs_by_4_blanks(new_text)
        fileobject.close()
        os.remove(file_name_tmp)
        if new_text != self.old_text:
            self._save(new_text)

    def _replace_tabs_by_4_blanks(self, text):
        return re.sub("\\t", "    ", text)
