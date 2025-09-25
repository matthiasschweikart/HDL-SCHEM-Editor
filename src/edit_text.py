"""
This class copies the content of a canvas text item into an tk text widget,
so that the user can modify the text.
When the user ends editing by pressing return, the new text is stored in the canvas text item.
When the user ends editing by pressing escape, the new text is not stored in the canvas text item.
"""
import tkinter as tk

class EditText():
    def __init__(self,
                 text_type,   # "generic_block"
                 window,
                 diagram_tab, # : notebook_diagram_tab.NotebookDiagramTab,
                 canvas_id,   # Canvas-ID of the text widget, which has to be changed (needed for content and coordinates)
                 parent,
                 highlight_line=None):
        self.text_type   = text_type
        self.diagram_tab = diagram_tab
        self.window      = window
        text = diagram_tab.canvas.itemcget(canvas_id, "text")
        self.height, self.width = self. __determine_height_and_width(text)
        self.text_box = tk.Text(self.diagram_tab.canvas, height=self.height, width=self.width, font=("Courier", self.window.design.get_font_size()),
                                undo=True, maxundo=-1)
        self.text_box.insert("end", text)
        self.text_box.focus_set()
        if highlight_line is not None:
            self.text_box.tag_add("highlight", str(highlight_line) + ".0", str(highlight_line+1) + ".0" )
            self.text_box.tag_config("highlight", background="orange") # "#e9e9e9")
        coords = diagram_tab.canvas.coords(canvas_id)
        diagram_tab.canvas.create_window(coords, window=self.text_box, anchor="sw", tags="entry-window")
        self.window.design.set_block_edit_is_running(True) # Needed to prevent <Focus-In> from binding <Control-s> again in menu_bar.create_binding__for_menu_accelerators().
        self.window.unbind_all("<Control-s>") # <Control-s> is needed for saving the block edit.
        self.text_box.bind("<Control-s>", lambda event: self.__update_text      (parent))
        self.text_box.bind("<Key>"      , lambda event: self.__adapt_window_size(      ))
        self.text_box.bind("<Escape>"   , lambda event: self.delete_entry_window(      ))
        self.text_box.bind("<Control-Z>", lambda event: self.text_box.edit_redo (      ))
        self.text_box.bind("<Button-1>" , lambda event: self.text_box.tag_delete("highlight"))
        self.window.design.edit_text_edit_list_append(self)

    def __determine_height_and_width(self, text):
        number_of_lines = text.count("\n") + 1
        line_list = text.split("\n")
        max_line_length = 0
        for line in line_list:
            if len(line)>max_line_length:
                max_line_length = len(line)
        return number_of_lines, max_line_length

    def __adapt_window_size(self):
        self.diagram_tab.canvas.after_idle(self.__adapt_window_size_after_idle)

    def __adapt_window_size_after_idle(self):
        text = self.text_box.get("1.0", "end - 1 chars")
        height, width = self.__determine_height_and_width(text)
        if height>self.height or width>self.width:
            self.text_box.configure(height=height, width=width)

    def __update_text(self, parent):
        parent.update({self.text_type: self.text_box.get("1.0", "end - 1 chars")}, store_in_design_and_stack=True)
        self.delete_entry_window()
        self.window.design.set_block_edit_is_running(False) # The next <FocusIn> event will bind <Control-s> to file_write again.

    def delete_entry_window(self):
        self.window.design.edit_text_edit_list_remove(self)
        self.text_box.destroy()
        self.diagram_tab.canvas.delete("entry-window")
        self.diagram_tab.canvas.focus_set()
