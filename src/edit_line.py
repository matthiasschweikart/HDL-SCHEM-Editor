"""
This class copies the content of a canvas text item into an tk entry widget,
so that the user can modify the text.
When the user ends editing by pressing return, the new text is stored in the canvas text item.
When the user ends editing by pressing escape, the new text is not stored in the canvas text item.
"""
from tkinter import ttk

class EditLine():
    def __init__(self,
                 design,      # : design_data.DesignData,
                 diagram_tab, # : notebook_diagram_tab.NotebookDiagramTab,
                 canvas_id,
                 parent):
        self.design      = design
        self.diagram_tab = diagram_tab
        text = self.diagram_tab.canvas.itemcget(canvas_id, "text")
        self.text_box = ttk.Entry(self.diagram_tab.canvas, width=len(text), justify="left", font=("Courier", design.get_font_size()))
        self.text_box.insert("end", text)
        self.text_box.focus_set()
        coords = self.diagram_tab.canvas.coords(canvas_id)
        self.diagram_tab.canvas.create_window(coords, window=self.text_box, anchor="w", tags="entry-window")
        self.text_box.bind("<Key>"   , lambda event: self.__increase_length  (len(text)        ))
        self.text_box.bind("<Return>", lambda event: self.__update_text      (canvas_id, parent))
        self.text_box.bind("<Escape>", lambda event: self.delete_entry_window(                 ))
        self.design.edit_line_edit_list_append(self)

    def __increase_length(self, text_length):
        self.diagram_tab.canvas.after_idle(self.__increase_length_after_idle, text_length)

    def __increase_length_after_idle(self, text_length):
        new_length = len(self.text_box.get())
        if new_length>text_length:
            self.text_box.configure(width=new_length)

    def __update_text(self, canvas_id, parent):
        self.diagram_tab.canvas.itemconfigure(canvas_id, text=self.text_box.get())
        self.delete_entry_window()
        parent.store_item(push_design_to_stack=True, signal_design_change=True)

    def delete_entry_window(self):
        self.design.edit_line_edit_list_remove(self)
        self.text_box.destroy()
        self.diagram_tab.canvas.delete("entry-window")
        self.diagram_tab.canvas.focus_set()
