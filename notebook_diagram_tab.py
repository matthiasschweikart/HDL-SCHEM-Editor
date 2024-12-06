""" This class creates a notebook page for drawing the schematic. """
import tkinter as tk
from   tkinter import ttk
from   tkinter import messagebox
import re
import wire_insertion
import schematic_window
import wire_highlight
import hdl_generate_functions
import symbol_properties
import edit_line
import edit_text
import grid_drawing
import listbox_animated
import color_changer
import constants

class NotebookDiagramTab():
    selected_canvas_ids_for_copy = []
    clipboard_window             = None
    grid_size_copied_from        = 0
    def __init__(self, root, window,
                 notebook : ttk.Notebook,
                 design, #: design_data.DesignData,
                 wire_class, signal_name_class, input_class, output_class, inout_class,
                 block_class, symbol_reading_class, symbol_insertion_class, symbol_instance_class, generate_frame_class
                 ):
        self.design                  = design
        self.architecture_name       = self.design.get_architecture_name()
        self.architecture_list       = ["struct"]
        self.wire_class              = wire_class
        self.signal_name_class       = signal_name_class
        self.input_class             = input_class
        self.output_class            = output_class
        self.inout_class             = inout_class
        self.block_class             = block_class
        self.symbol_reading_class    = symbol_reading_class
        self.symbol_insertion_class  = symbol_insertion_class
        self.symbol_instance_class   = symbol_instance_class
        self.generate_frame_class    = generate_frame_class
        self.root                    = root
        self.window                  = window
        self.event_x                 = 0
        self.event_y                 = 0
        self.func_id_1               = None
        self.func_id_2               = None
        self.func_id_3               = None
        self.func_id_4               = None
        self.func_id_6               = None
        self.func_id_7               = None
        self.funcid_motion           = None
        self.funcid_button1_start_move_of_selection = None
        self.funcid_button1_release  = None
        self.funcid_button3_release  = None
        self.last_factor             = 1
        self.zoom_area_shift_x       = 0
        self.zoom_area_shift_y       = 0
        self.polygon_move_funcids_button1 = {}
        self.polygon_move_funcids_motion  = None
        self.polygon_move_funcids_release = None
        self.polygon_move_list            = []
        self.coords_select_rectangle      = []
        self.canvas_menue_entries_list_with_hide = r"""Change\ background\ color
                                                       Hide\ grid"""
        self.canvas_menue_entries_list_with_show = r"""Change\ background\ color
                                                       Show\ grid"""

        # Prepare for the Canvas:
        canvas_width  = 1300 # The width must be bigger than the layout-manager calculates for all the buttons.
        canvas_height = 400  # Otherwise the canvas width would be bigger than the scroll_region, which would be a mistake.
        self.canvas_visible_area = [0, 0, canvas_width, canvas_height]

        # Implement the diagram_frame:
        self.diagram_frame = ttk.Frame(notebook, borderwidth=0, relief='flat')
        self.diagram_frame.grid()
        self.left_buttons_frame   = ttk.Frame      (self.diagram_frame, borderwidth=0)
        self.paned_window         = ttk.PanedWindow(self.diagram_frame, orient=tk.HORIZONTAL, takefocus=True)
        self.left_buttons_frame.grid    (row=0, column=0, sticky=(tk.N,tk.W,tk.E,tk.S))
        self.paned_window.grid          (row=0, column=1, sticky=(tk.N,tk.W,tk.E,tk.S))
        self.diagram_frame.rowconfigure   (0, weight=1)
        self.diagram_frame.columnconfigure(0, weight=0)
        self.diagram_frame.columnconfigure(1, weight=1)

        # Implement the canvas_frame:
        self.canvas_frame         = ttk.Frame    (self.paned_window, borderwidth=0)
        self.canvas_frame.grid()
        self.canvas_scrollbar_hor = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, cursor='arrow', style='Horizontal.TScrollbar')
        self.canvas_scrollbar_ver = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL  , cursor='arrow')
        self.canvas               = tk.Canvas    (self.canvas_frame, relief='sunken', borderwidth=1, height=canvas_height, width=canvas_width,
                                                  scrollregion=self.canvas_visible_area, bg=self.root.schematic_background_color,
                                                  xscrollcommand=self.canvas_scrollbar_hor.set, yscrollcommand=self.canvas_scrollbar_ver.set)
        self.canvas_frame.rowconfigure   (0, weight=1)
        self.canvas_frame.rowconfigure   (1, weight=0)
        self.canvas_frame.columnconfigure(0, weight=1)
        self.canvas_frame.columnconfigure(1, weight=0)
        self.canvas.grid              (row=0, column=0, sticky=(tk.N,tk.W,tk.E,tk.S))
        self.canvas_scrollbar_ver.grid(row=0, column=1, sticky=(tk.N,tk.S))     # The sticky argument extends the scrollbar, so that a "shift" is possible.
        self.canvas_scrollbar_hor.grid(row=1, column=0, sticky=(tk.W,tk.E))     # The sticky argument extends the scrollbar, so that a "shift" is possible.
        self.canvas_scrollbar_ver['command'] = self.canvas.yview # self.yview_extended
        self.canvas_scrollbar_hor['command'] = self.canvas.xview # self.xview_extended
        self.canvas_scrollbar_ver.bind("<ButtonRelease-1>", lambda event : self.__store_visible_center_point())
        self.canvas_scrollbar_hor.bind("<ButtonRelease-1>", lambda event : self.__store_visible_center_point())
        self.paned_window.add(self.canvas_frame, weight=10)

        # Implement the treeview_frame:
        self.treeview_frame         = ttk.Frame(self.paned_window, borderwidth=0)
        self.treeview_scrollbar_hor = ttk.Scrollbar(self.treeview_frame, orient=tk.HORIZONTAL, cursor='arrow', style='Horizontal.TScrollbar')
        self.treeview_scrollbar_ver = ttk.Scrollbar(self.treeview_frame, orient=tk.VERTICAL  , cursor='arrow')
        self.treeview               = ttk.Treeview (self.treeview_frame,
                                                    columns=self.window.hierarchytree.column_names[1:], # Define additional columns beside the icon column.
                                                    displaycolumns=(0,1), # Beside the icon column display the columns 0 and 1.
                                                    xscrollcommand=self.treeview_scrollbar_hor.set,
                                                    yscrollcommand=self.treeview_scrollbar_ver.set)
        for column_name in self.window.hierarchytree.column_names:
            if column_name=="#0":
                text = self.window.hierarchytree.column_name_of_column0
            else:
                text = column_name
            self.treeview.heading(column_name, text=text)
            self.treeview.column (column_name, stretch=False, width=100)
        self.treeview_frame.rowconfigure   (0, weight=1)
        self.treeview_frame.rowconfigure   (1, weight=0)
        self.treeview_frame.columnconfigure(0, weight=1)
        self.treeview_frame.columnconfigure(1, weight=0)
        self.treeview.grid              (row=0, column=0, sticky=(tk.N,tk.W,tk.E,tk.S))
        self.treeview_scrollbar_ver.grid(row=0, column=1, sticky=(tk.N,tk.S))     # The sticky argument extends the scrollbar, so that a "shift" is possible.
        self.treeview_scrollbar_hor.grid(row=1, column=0, sticky=(tk.W,tk.E))     # The sticky argument extends the scrollbar, so that a "shift" is possible.
        self.treeview_scrollbar_ver['command'] = self.treeview.yview
        self.treeview_scrollbar_hor['command'] = self.treeview.xview
        #self.treeview.tag_bind("tree_view_entry", "<Double-Button-1>", lambda event: self.window.hierarchytree.open_design_in_new_window(event, self.treeview))
        self.treeview.bind("<Double-Button-1>", lambda event: self.window.hierarchytree.open_design_in_new_window(event, self.treeview))

        notebook.add(self.diagram_frame, sticky=tk.N+tk.E+tk.W+tk.S, text="Diagram") # As schematic_window.notebook_top.notebook does not yet exist, when the constructor is called,
                                                                                     # because it is actually under construction, reference "notebook" has to be used
        # Layout of the left_buttons_frame:
        self.architecture_frame = ttk.Frame (self.left_buttons_frame, borderwidth=0)
        self.new_buttons_frame  = ttk.Frame (self.left_buttons_frame, borderwidth=0)
        self.copy_paste_frame   = ttk.Frame (self.left_buttons_frame, borderwidth=0)
        self.undo_redo_frame    = ttk.Frame (self.left_buttons_frame, borderwidth=0)
        self.view_buttons_frame = ttk.Frame (self.left_buttons_frame, borderwidth=0)
        self.architecture_frame.grid(row=0, column=0, sticky=(tk.W,tk.E,tk.N))
        self.new_buttons_frame .grid(row=1, column=0, sticky=(tk.W,tk.E))
        self.copy_paste_frame  .grid(row=2, column=0, sticky=(tk.W,tk.E))
        self.undo_redo_frame   .grid(row=3, column=0, sticky=(tk.W,tk.E))
        self.view_buttons_frame.grid(row=4, column=0, sticky=(tk.W,tk.E,tk.S))
        self.left_buttons_frame.rowconfigure(0, weight=1)
        self.left_buttons_frame.rowconfigure(1, weight=1)
        self.left_buttons_frame.rowconfigure(2, weight=1)
        self.left_buttons_frame.rowconfigure(3, weight=1)
        self.left_buttons_frame.rowconfigure(4, weight=1)

        # Implement the buttons for the architecture_frame
        self.architecture_label         = ttk.Label   (self.architecture_frame, takefocus=False, text="Architecture:", justify=tk.CENTER)
        self.architecture_combobox      = ttk.Combobox(self.architecture_frame, takefocus=False, state="readonly",
                                                                                values=self.architecture_list, justify=tk.CENTER)
        self.rename_architecture_button = ttk.Button  (self.architecture_frame, takefocus=False, text="rename Architecture", style="NewState.TButton")
        self.new_architecture_button    = ttk.Button  (self.architecture_frame, takefocus=False, text="new Architecture", style="NewState.TButton")
        self.delete_architecture_button = ttk.Button  (self.architecture_frame, takefocus=False, text="delete Architecture", style="NewState.TButton", state="disabled")
        self.architecture_label        .grid(row=0, column=0)
        self.architecture_combobox     .grid(row=1, column=0, sticky=(tk.W,tk.E))
        self.rename_architecture_button.grid(row=2, column=0, sticky=(tk.W,tk.E))
        self.new_architecture_button   .grid(row=3, column=0, sticky=(tk.W,tk.E))
        self.delete_architecture_button.grid(row=4, column=0, sticky=(tk.W,tk.E))
        self.architecture_frame.columnconfigure(0, weight=1)
        self.architecture_combobox.set(self.architecture_list[0])

        # Implement the buttons of the new_buttons_frame:
        self.new_input_button    = ttk.Button(self.new_buttons_frame, takefocus=False, text="new Input"       , style="NewState.TButton")
        self.new_output_button   = ttk.Button(self.new_buttons_frame, takefocus=False, text="new Output"      , style="NewTransition.TButton")
        self.new_inout_button    = ttk.Button(self.new_buttons_frame, takefocus=False, text="new Inout"       , style="NewConnector.TButton")
        self.new_wire_button     = ttk.Button(self.new_buttons_frame, takefocus=False, text="new Wire"        , style="ResetEntry.TButton")
        self.new_bus_button      = ttk.Button(self.new_buttons_frame, takefocus=False, text="new Bus"         , style="ResetEntry.TButton")
        self.new_block_button    = ttk.Button(self.new_buttons_frame, takefocus=False, text="new Block"       , style="DefaultStateActions.TButton")
        self.new_instance_button = ttk.Button(self.new_buttons_frame, takefocus=False, text="new Instance"    , style="DefaultStateActions.TButton")
        self.new_generate_button = ttk.Button(self.new_buttons_frame, takefocus=False, text="new Generate"    , style="DefaultStateActions.TButton")
        self.new_input_button   .grid(row=0, column=0, sticky=(tk.W,tk.E))
        self.new_output_button  .grid(row=1, column=0, sticky=(tk.W,tk.E))
        self.new_inout_button   .grid(row=2, column=0, sticky=(tk.W,tk.E))
        self.new_wire_button    .grid(row=3, column=0, sticky=(tk.W,tk.E))
        self.new_bus_button     .grid(row=4, column=0, sticky=(tk.W,tk.E))
        self.new_block_button   .grid(row=5, column=0, sticky=(tk.W,tk.E))
        self.new_instance_button.grid(row=6, column=0, sticky=(tk.W,tk.E))
        self.new_generate_button.grid(row=7, column=0, sticky=(tk.W,tk.E))
        self.new_buttons_frame.columnconfigure(0, weight=1)

        # Implement the buttons of the copy_paste_frame:
        self.copy_button      = ttk.Button(self.copy_paste_frame, text="Copy Selection (Ctrl-c)" , state="disabled", command=self.copy )
        self.paste_button     = ttk.Button(self.copy_paste_frame, text="Paste (Ctrl-v)"          , state="disabled", command=self.paste_from_button)
        self.copy_button .grid(row=0, column=0, sticky=(tk.W,tk.E))
        self.paste_button.grid(row=1, column=0, sticky=(tk.W,tk.E))
        self.copy_paste_frame.columnconfigure(0, weight=1)

        # Implement the buttons of the undo_redo_frame:
        self.undo_button     = ttk.Button(self.undo_redo_frame, text="Undo (Ctrl-z)"  ,  command=self.undo, state="disabled")
        self.redo_button     = ttk.Button(self.undo_redo_frame, text="Redo (Ctrl-y/Z)",  command=self.redo, state="disabled")
        self.undo_button.grid(row=0, column=0, sticky=(tk.W,tk.E))
        self.redo_button.grid(row=1, column=0, sticky=(tk.W,tk.E))
        self.undo_redo_frame.columnconfigure(0, weight=1)

        # Implement the buttons of the view_buttons_frame:
        self.view_all_button         = ttk.Button  (self.view_buttons_frame, takefocus=False, text="view all"        , style="View.TButton")
        self.view_area_button        = ttk.Button  (self.view_buttons_frame, takefocus=False, text="view area"       , style="View.TButton")
        self.view_last_button        = ttk.Button  (self.view_buttons_frame, takefocus=False, text="view last"       , style="View.TButton")
        self.plus_button             = ttk.Button  (self.view_buttons_frame, takefocus=False, text='+'               , style="View.TButton")
        self.minus_button            = ttk.Button  (self.view_buttons_frame, takefocus=False, text='-'               , style="View.TButton")
        self.view_all_button .grid(row=0, column=0, sticky=(tk.W,tk.E))
        self.view_area_button.grid(row=1, column=0, sticky=(tk.W,tk.E))
        self.view_last_button.grid(row=2, column=0, sticky=(tk.W,tk.E))
        self.plus_button     .grid(row=3, column=0, sticky=(tk.W,tk.E))
        self.minus_button    .grid(row=4, column=0, sticky=(tk.W,tk.E))
        self.view_buttons_frame.columnconfigure(0, weight=1)

        # Bindings of the drawing area:
        dummy = None
        self.architecture_combobox     .bind("<<ComboboxSelected>>", lambda event: self.__switch_to_other_architecture())
        self.new_architecture_button   .bind ('<Button-1>'         , lambda event: self.__create_new_architecture_name())
        self.delete_architecture_button.bind ('<Button-1>'         , lambda event: self.__delete_architecture())
        self.rename_architecture_button.bind ('<Button-1>'         , lambda event: self.__rename_architecture())
        self.new_input_button          .bind ('<Button-1>'         , lambda event: self.input_class   (window, self, dummy, follow_mouse=True))
        self.new_output_button         .bind ('<Button-1>'         , lambda event: self.output_class  (window, self, dummy, follow_mouse=True))
        self.new_inout_button          .bind ('<Button-1>'         , lambda event: self.inout_class   (window, self, dummy, follow_mouse=True))
        self.new_wire_button           .bind ('<Button-1>'         , lambda event: self.wire_class    (root, window, self, width=1)) #push_design_to_stack=True))
        self.new_bus_button            .bind ('<Button-1>'         , lambda event: self.wire_class    (root, window, self, width=3)) #push_design_to_stack=True))
        self.new_block_button          .bind ('<Button-1>'         , lambda event: self.block_class   (window, self)) #, push_design_to_stack=True))
        self.new_instance_button       .bind ('<Button-1>'         , lambda event: self.__open_symbol_reading())
        self.new_generate_button       .bind ('<Button-1>'         , lambda event: self.__open_generate_frame())
        self.view_all_button           .bind ('<Button-1>'         , lambda event: self.__view_all())
        self.view_area_button          .bind ('<Button-1>'         , lambda event: self.__view_area())
        self.view_last_button          .bind ('<Button-1>'         , lambda event: self.__view_last())
        self.plus_button               .bind ('<Button-1>'         , lambda event: self.__zoom(factor=1.1  , command="plus" , event=None))
        self.minus_button              .bind ('<Button-1>'         , lambda event: self.__zoom(factor=1/1.1, command="minus", event=None))
        self.create_canvas_bindings()
        self.canvas.bind('<Control-Button-1>'       , self.__scroll_start)
        self.canvas.bind('<Control-B1-Motion>'      , self.__scroll_move )
        self.canvas.bind("<MouseWheel>"             , self.__scroll_wheel) # MouseWheel used at Windows.
        self.canvas.bind("<Button-4>"               , self.__scroll_wheel) # MouseWheel-Scroll-Up used at Linux.
        self.canvas.bind("<Button-5>"               , self.__scroll_wheel) # MouseWheel-Scroll-Down used at Linux.
        self.canvas.bind("<Control-ButtonRelease-1>", self.__scroll_end  )
        self.canvas.bind("<Control-MouseWheel>"     , self.__zoom_wheel  ) # MouseWheel used at Windows.
        self.canvas.bind("<Control-Button-4>"       , self.__zoom_wheel  ) # MouseWheel-Scroll-Up used at Linux.
        self.canvas.bind("<Control-Button-5>"       , self.__zoom_wheel  ) # MouseWheel-Scroll-Down used at Linux.
        #self.window.bind("<Motion>", self.__coord_info)
        self.grid_drawer = grid_drawing.GridDraw(self.root, self, self.design, self.canvas)
        # Needed for Entry-Widget for new architecture name:
        self.architecture_name_stringvar = tk.StringVar()

    def create_canvas_bindings(self):
        self.func_id_3 = self.canvas.bind("<Button-1>", self.__start_drawing_selection_rectangle)
        self.func_id_4 = self.canvas.bind("<Button-3>", self.__start_drawing_zoom_rectangle)

    def remove_canvas_bindings(self):
        if self.func_id_3 is not None:
            self.canvas.unbind("<Button-1>", self.func_id_3)
            self.func_id_3 = None
        if self.func_id_4 is not None:
            self.canvas.unbind("<Button-3>", self.func_id_4)
            self.func_id_4 = None

    def diagram_tab_is_shown(self):
        self.__adjust_scroll_region()
        self.grid_drawer.draw_grid()
        self.window.hierarchytree.show_hierarchy_button()

    def diagram_tab_is_hidden(self):
        self.window.hierarchytree.hide_hierarchy_button()

    # def __show_scroll_region(self):
    #     self.canvas.delete("scroll_region_points")
    #     size = self.design.get_grid_size()/2
    #     self.canvas.create_oval(self.canvas_visible_area[0]-size,
    #                             self.canvas_visible_area[1]-size,
    #                             self.canvas_visible_area[0]+size,
    #                             self.canvas_visible_area[1]+size,
    #                             fill="blue", tag="scroll_region_points")
    #     self.canvas.create_oval(self.canvas_visible_area[2]-size,
    #                             self.canvas_visible_area[1]-size,
    #                             self.canvas_visible_area[2]+size,
    #                             self.canvas_visible_area[1]+size,
    #                             fill="blue", tag="scroll_region_points")
    #     self.canvas.create_oval(self.canvas_visible_area[0]-size,
    #                             self.canvas_visible_area[3]-size,
    #                             self.canvas_visible_area[0]+size,
    #                             self.canvas_visible_area[3]+size,
    #                             fill="blue", tag="scroll_region_points")
    #     self.canvas.create_oval(self.canvas_visible_area[2]-size,
    #                             self.canvas_visible_area[3]-size,
    #                             self.canvas_visible_area[2]+size,
    #                             self.canvas_visible_area[3]+size,
    #                             fill="blue", tag="scroll_region_points")

    # def __get_canvas_coords(self):
    #     canvas_coords = [self.canvas.canvasx(0                         ),#, gridspacing=grid_size),
    #                      self.canvas.canvasy(0                         ),# gridspacing=grid_size),
    #                      self.canvas.canvasx(self.canvas.winfo_width() ),# gridspacing=grid_size),
    #                      self.canvas.canvasy(self.canvas.winfo_height())]#, gridspacing=grid_size)]
    #     return canvas_coords

    def sort_layers(self):
        layers = ["layer1", "layer2", "layer3", "layer4", "layer5"]
        for layer in layers:
            self.canvas.lower(layer)

    # def __coord_info(self, event):
    #     # print("self.window.winfo_pointerxy() =", self.window.winfo_pointerxy())
    #     # print("self.canvas.winfo_pointerxy() =", self.canvas.winfo_pointerxy())
    #     # print("self.canvas.winfo_rootxy()    =", self.canvas.winfo_rootx(),self.canvas.winfo_rooty())
    #     # print("event_x , event_y  =", event.x,event.y)
    #     print("canvas_x, canvas_y =", self.canvas.canvasx(event.x),self.canvas.canvasy(event.y))
    #     # print("scroll_region =", self.canvas.cget("scrollregion"))
    #     # print(self.canvas.canvasx(0), self.canvas.canvasy(0), self.canvas.canvasx(self.canvas.winfo_width()), self.canvas.canvasy(self.canvas.winfo_height()))

    def get_enclosed_elements(self, coords):
        element_canvas_ids =[]
        enclosed_element_list = self.canvas.find_enclosed(*coords)
        for canvas_id in enclosed_element_list:
            if canvas_id in self.design.get_canvas_ids_of_elements():
                if self.design.get_schematic_element_type_of(canvas_id) in ["block", "instance", "generate_frame"]:
                    element_canvas_ids.append(canvas_id)
        element_canvas_ids = self.__add_overlapping_block_text_elements(enclosed_element_list, element_canvas_ids)
        return element_canvas_ids

    def __add_overlapping_block_text_elements(self, enclosed_element_list, element_canvas_ids):
        for canvas_id in enclosed_element_list:
            if self.canvas.type(canvas_id)=="rectangle" and self.design.get_schematic_element_type_of(canvas_id)=="block-rectangle":
                ref = self.design.get_references([canvas_id])[0]
                object_tag = ref.get_object_tag()
                list_of_canvas_ids_of_object = self.canvas.find_withtag(object_tag)
                for single_canvas_id_of_object in list_of_canvas_ids_of_object:
                    if single_canvas_id_of_object!=canvas_id:
                        if single_canvas_id_of_object not in element_canvas_ids:
                            element_canvas_ids.append(single_canvas_id_of_object)
        return element_canvas_ids

    def copy(self):
        if NotebookDiagramTab.clipboard_window is not None:
            NotebookDiagramTab.clipboard_window.close_this_window()
            NotebookDiagramTab.clipboard_window = None
        references = self.design.get_references(self.canvas.find_withtag("selected"))
        if references:
            selected_canvas_ids_for_copy = self.__get_canvas_ids_of_all_items_of_the_selected(references)
        else:
            messagebox.showerror("Error in HDL-SCHEM-Editor", "Nothing selected. Select by dragging a rectangle with the mouse pointer.")
        self.__unselect_elements()
        if references:
            self.__copy_selected_to_clipboard(selected_canvas_ids_for_copy)
            for window in schematic_window.SchematicWindow.open_window_dict:
                window.notebook_top.diagram_tab.paste_button.configure(state="active")
        self.canvas.focus_set() # When copy was called by the Copy-button, focus changed to the button, which will not react to a Control-v which might be the next user action.

    def __get_canvas_ids_of_all_items_of_the_selected(self, references):
        all_object_tags         = []
        signal_name_object_tags = []
        for reference in references:
            object_tag = reference.get_object_tag()
            if (isinstance(object_tag, int) or # Detect the integer object_tags of interface-connectors so that they are not checked by ".endswith" in the next line.
                not object_tag.endswith("_signal_name")): # Do not add signal-name-object-tags to this list, otherwise signal_names without wires could be copied.
                all_object_tags.append(object_tag)
            else: # Only signal_names remain here.
                signal_name_object_tags.append(object_tag) # This list is needed for later adding to the "selected"-tag, so that __undo selection() can work.
        for object_tag in all_object_tags:
            self.canvas.addtag_withtag("selected", object_tag)
        selected_canvas_ids_for_copy = self.canvas.find_withtag("selected")
        for object_tag in signal_name_object_tags: # These canvas items shall not be included in NotebookDiagramTab.selected_canvas_ids_for_copy.
            self.canvas.addtag_withtag("selected", object_tag) # prepare for __undo selection()
        return selected_canvas_ids_for_copy

    def __copy_selected_to_clipboard(self, selected_canvas_ids_for_copy):
        NotebookDiagramTab.grid_size_copied_from = self.design.get_grid_size()
        NotebookDiagramTab.clipboard_window = schematic_window.SchematicWindow.open_clipboard_window(self.root)
        NotebookDiagramTab.clipboard_window.design.set_grid_size     (self.design.get_grid_size     ())
        NotebookDiagramTab.clipboard_window.design.set_font_size     (self.design.get_font_size     ())
        NotebookDiagramTab.clipboard_window.design.set_connector_size(self.design.get_connector_size())
        NotebookDiagramTab.clipboard_window.design.set_language      (self.design.get_language      ())
        references_of_copies = NotebookDiagramTab.clipboard_window.design.insert_copies_from(self.window, selected_canvas_ids_for_copy, move_copies_under_the_cursor=False)
        if references_of_copies:
            NotebookDiagramTab.selected_canvas_ids_for_copy = NotebookDiagramTab.clipboard_window.notebook_top.diagram_tab.canvas.find_all()
        else:
            NotebookDiagramTab.selected_canvas_ids_for_copy = []

    def paste_from_button(self):
        self.canvas.focus_set()
        self.canvas.event_generate("<Control-v>", when="now") # event coordinates are not defined.
        # The event "<Control-v>" calls paste() and paste() draws the new elements and calls at last _move_selection_start().
        # But as the mouse pointer is still located at the button "Paste", the "<Motion>" event must be deactivated for
        # the time, when the user moves the mouse pointer from the button to the selected objects.
        # When the user clicks at the selected objects, in order to move them, _move_selection_start() is called a second time and "Motion" is bound again:
        self.canvas.unbind("<Motion>", self.funcid_motion)
        self.funcid_motion = None
        # The binding of ButtonRelease-1 must also be removed, because when the user clicks at the pasted objects in order to move them,
        # __move_selection-start is called and decides by self.funcid_button1_release if Motion must be bound again:
        self.canvas.unbind("<ButtonRelease-1>", self.funcid_button1_release)
        self.funcid_button1_release = None

    def paste(self, event): # event was key "control-v".
        self.window.event_generate("<FocusIn>", when="now") # get the focus back from the clipboard and bind the accellerators to this window.
        if event.send_event: # Event control-v was created by keyboard
            move_copies_under_the_cursor = True
        else:                # Event control-v was created by the paste-button
            move_copies_under_the_cursor = False
        if NotebookDiagramTab.clipboard_window is not None:
            references_of_copies = self.window.design.insert_copies_from(NotebookDiagramTab.clipboard_window,
                                                                         NotebookDiagramTab.selected_canvas_ids_for_copy, move_copies_under_the_cursor)
            if references_of_copies:
                all_object_tags = []
                for reference in references_of_copies:
                    reference.select_item() # Highlights all items and deactivates all bindings at the items
                    all_object_tags.append(reference.get_object_tag())
                for object_tag in all_object_tags:
                    self.canvas.addtag_withtag("selected", object_tag)
                # A copy of a symbol is not yet stored in the design_data.canvas_dictionary, so the references must be taken from here.
                # When Control-v was pressed then the copy shall react to mouse-movements and shall not need a pick up by Button-1:
                self.__move_selection_start(event, references=references_of_copies)
                # When the paste button was pressed, then the moving of the selection has to start by the left mouse button:
                self.funcid_button1_start_move_of_selection = self.canvas.tag_bind("selected", "<Button-1>",
                                                                lambda event: self.__move_selection_start(event, references_of_copies))
            self.copy_button.configure(state="disabled")

    def __store_visible_center_point(self):
        # Here canvasx and canvasy are used. They translate coordinates.
        # The upper left  edge of the canvas widget has always the window coordinates [0, 0].
        # The lower right edge of the canvas widget has always the window coordinates [canvas.winfo_width(), canvas.winfo_height()].
        visible_center_point = [(self.canvas.canvasx(0) + self.canvas.canvasx(self.canvas.winfo_width ()))/2,
                                (self.canvas.canvasy(0) + self.canvas.canvasy(self.canvas.winfo_height()))/2]
        self.window.design.store_visible_center_point(visible_center_point, True, False)

    def __open_symbol_reading(self):
        # The filedialog must not be started, before the button had time to show first "pressed" and then "released":
        # This did work under windows but is probably wrong, as the button is not part of canvas.
        #self.canvas.after_idle(self.symbol_reading_class, self.root, self.window, self)
        # This let the button enter "released" under Linux:
        self.window.after(300, self.symbol_reading_class, self.root, self.window, self)

    def __open_generate_frame(self):
        # Probably not needed to show the button first "pressed" and then "released":
        self.canvas.after_idle(self.generate_frame_class, self.root, self.window, self, {})

    def __scroll_start(self, event):
        self.canvas.scan_mark(event.x,event.y)

    def __scroll_move(self, event):
        self.canvas.scan_dragto(event.x,event.y,gain=1)

    def __scroll_end(self,event):
        self.__store_visible_center_point()

    def __scroll_wheel(self,event):
        self.canvas.scan_mark(event.x,event.y)
        # event.delta: attribute of the mouse wheel under Windows and MacOs.
        # One "felt step" at the mouse wheel gives this value:
        # Windows: delta=+/-120 ; MacOS: delta=+/-1 ; Linux: delta=0
        # num: attribute of the the mouse wheel under Linux  ("scroll-up=5" and "scroll-down=4").
        if   event.num == 5 or event.delta<0:  # scroll down
            delta_y = -100
        elif event.num == 4 or event.delta>=0:  # scroll up
            delta_y = +100
        self.canvas.scan_dragto(event.x,event.y + delta_y,gain=1)
        self.__store_visible_center_point()

    def __zoom_wheel(self,event):
        # event.delta: attribute of the mouse wheel under Windows and MacOs.
        # One "felt step" at the mouse wheel gives this value:
        # Windows: delta=+/-120 ; MacOS: delta=+/-1 ; Linux: delta=0
        # event.num: attribute of the the mouse wheel under Linux ("scroll-up=5" and "scroll-down=4").
        if   event.num == 5 or event.delta<0:  # scroll down
            self.__zoom(1/1.1, "minus", event)
        elif event.num == 4 or event.delta>=0: # scroll up
            self.__zoom(1.1  , "plus" , event)

    # def xview_extended(self,*args):
    #     self.canvas.xview(*args)

    # def yview_extended(self,*args):
    #     self.canvas.yview(*args)

    def __view_all(self):
        self.grid_drawer.remove_grid() # Remove grid, so that it is not found by "bbox".
        complete_rectangle = self.canvas.bbox("all")
        if complete_rectangle is not None: # Is None, when Canvas is empty.
            self.__zoom_area(complete_rectangle, "view_all")

    def __view_area(self):
        self.window.config(cursor="cross")
        self.remove_canvas_bindings()
        self.func_id_7 = self.canvas.bind("<Button-1>", self.__start_drawing_zoom_rectangle_by_button)

    def __start_drawing_zoom_rectangle_by_button(self, event):
        event_x, event_y  = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        zoom_rectangle_id = self.canvas.create_rectangle(event_x, event_y, event_x, event_y, dash=(3,5))
        self.funcid_motion          = self.canvas.bind("<Motion>"         , lambda event: self.__expand_rectangle(event, zoom_rectangle_id))
        self.funcid_button1_release = self.canvas.bind("<ButtonRelease-1>", lambda event: self.__close_zoom_rectangle_by_button(zoom_rectangle_id))

    def __close_zoom_rectangle_by_button(self, zoom_rectangle_id):
        self.canvas.unbind("<Button-1>"       , self.func_id_7)
        self.canvas.unbind("<Motion>"         , self.funcid_motion)
        self.canvas.unbind("<ButtonRelease-1>", self.funcid_button1_release)
        self.func_id_7              = None
        self.funcid_motion          = None
        self.funcid_button1_release = None
        zoom_coords = self.canvas.coords(zoom_rectangle_id)
        self.canvas.delete(zoom_rectangle_id)
        self.__zoom_area(zoom_coords, "zoom_rectangle")
        self.window.config(cursor="arrow")
        self.create_canvas_bindings()

    def __start_drawing_zoom_rectangle(self, event):
        event_x, event_y  = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        zoom_rectangle_id = self.canvas.create_rectangle(event_x, event_y, event_x, event_y, dash=(3,5))
        self.funcid_motion          = self.canvas.bind("<Motion>"         , lambda event: self.__expand_rectangle(event, zoom_rectangle_id))
        self.funcid_button3_release = self.canvas.bind("<ButtonRelease-3>", lambda event: self.__close_zoom_rectangle(zoom_rectangle_id))

    def __expand_rectangle(self, event, rectangle_id):
        event_x, event_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        coords = self.canvas.coords(rectangle_id)
        self.canvas.coords(rectangle_id, coords[0], coords[1], event_x, event_y)

    def __close_zoom_rectangle(self, zoom_rectangle_id):
        self.canvas.unbind("<Motion>"         , self.funcid_motion)
        self.canvas.unbind("<ButtonRelease-3>", self.funcid_button3_release)
        self.funcid_motion          = None
        self.funcid_button3_release = None
        zoom_coords = self.canvas.coords(zoom_rectangle_id)
        self.canvas.delete(zoom_rectangle_id)
        self.__zoom_area(zoom_coords, "zoom_rectangle")

    def __zoom_area(self, zoom_coords, command):
        if zoom_coords[0]!=zoom_coords[2] and zoom_coords[1]!=zoom_coords[3] and self.canvas.bbox("all") is not None:
            zoom_center = [(zoom_coords[0]+zoom_coords[2])/2, (zoom_coords[1]+zoom_coords[3])/2]
            window_coords = [self.canvas.canvasx(0), self.canvas.canvasy(0), self.canvas.canvasx(self.canvas.winfo_width()), self.canvas.canvasy(self.canvas.winfo_height())]
            window_center = [(window_coords[0]+window_coords[2])/2, (window_coords[1]+window_coords[3])/2]
            self.canvas.configure(confine=False)  # scan_dragto does now not depend on the scroll_region anymore.
            self.canvas.scan_mark  (int(zoom_center  [0]), int(zoom_center  [1]))
            self.canvas.scan_dragto(int(window_center[0]), int(window_center[1]), gain=1)
            self.zoom_area_shift_x = - int(zoom_center[0]) + int(window_center[0])
            self.zoom_area_shift_y = - int(zoom_center[1]) + int(window_center[1])
            factor_x = self.canvas.winfo_width() /(zoom_coords[2]-zoom_coords[0])
            factor_y = self.canvas.winfo_height()/(zoom_coords[3]-zoom_coords[1])
            self.__zoom(min(factor_x, factor_y), command, event=None)
        else:
            # No rectangle was drawn, but the right mouse button was clicked and released at the same place.
            overlapping_canvas_ids = self.canvas.find_overlapping(zoom_coords[0]-5, zoom_coords[1]-5, zoom_coords[0]+5, zoom_coords[1]+5)
            for canvas_id in overlapping_canvas_ids:
                tags = self.canvas.gettags(canvas_id)
                if "grid_line" not in tags:
                    return # An item was found which is not a grid-line
            self.__show_menu(zoom_coords)

    def __show_menu(self, zoom_coords):
        menu_entry_list = tk.StringVar()
        if self.root.show_grid is True:
            menu_entry_list.set(self.canvas_menue_entries_list_with_hide)
        else:
            menu_entry_list.set(self.canvas_menue_entries_list_with_show)
        menu = listbox_animated.ListboxAnimated(self.canvas, listvariable=menu_entry_list, height=2,
                                                bg='grey', width=25, activestyle='dotbox', relief="raised")
        menue_window = self.canvas.create_window(zoom_coords[0],zoom_coords[1],window=menu)
        menu.bind("<Button-1>", lambda event: self.__evaluate_menu_after_idle(menue_window, menu))
        menu.bind("<Leave>"   , lambda event: self.__close_menu(menue_window, menu))

    def __evaluate_menu_after_idle(self, menue_window, menu):
        self.canvas.after_idle(self.__evaluate_menu, menue_window, menu)

    def __evaluate_menu(self, menue_window, menu):
        selected_entry = menu.get(menu.curselection()[0])
        if 'Change background color' in selected_entry:
            new_color = color_changer.ColorChanger("white", self.window).get_new_color()
            if new_color is not None:
                self.root.schematic_background_color = new_color
                for open_window in self.window.__class__.open_window_dict:
                    open_window.notebook_top.diagram_tab.canvas.configure(bg=new_color)
        elif 'Hide grid' in selected_entry:
            self.root.show_grid = False
            for open_window in self.window.__class__.open_window_dict:
                open_window.notebook_top.diagram_tab.grid_drawer.remove_grid()
        elif 'Show grid' in selected_entry:
            self.root.show_grid = True
            for open_window in self.window.__class__.open_window_dict:
                open_window.notebook_top.diagram_tab.grid_drawer.draw_grid()
        self.__close_menu(menue_window, menu)

    def __close_menu(self, menue_window, menu):
        menu.destroy()
        self.canvas.delete(menue_window)

    def __zoom(self, factor, command, event):
        new_font_size = self.__get_new_font_size(factor, command)
        if new_font_size==0: # This happens at very big schematics
            new_font_size = 1
        self.canvas.itemconfigure("instance-text", font=("Courier", new_font_size))
        self.canvas.itemconfigure("signal-name"  , font=("Courier", new_font_size))
        self.canvas.itemconfigure("block-text"   , font=("Courier", new_font_size))
        factor_adapted = new_font_size/self.design.get_font_size()
        if event is None:
            old_center_x = (self.canvas.canvasx(0) + self.canvas.canvasx(self.canvas.winfo_width ()))/2
            old_center_y = (self.canvas.canvasy(0) + self.canvas.canvasy(self.canvas.winfo_height()))/2
        else:
            canvas_upper_left_x_measured_from_upper_left_corner_of_screen = self.canvas.winfo_rootx()
            canvas_upper_left_y_measured_from_upper_left_corner_of_screen = self.canvas.winfo_rooty()
            mouse_pointer_x_measured_from_upper_left_corner_of_screen     = self.canvas.winfo_pointerx()
            mouse_pointer_y_measured_from_upper_left_corner_of_screen     = self.canvas.winfo_pointery()
            delta_x = mouse_pointer_x_measured_from_upper_left_corner_of_screen - canvas_upper_left_x_measured_from_upper_left_corner_of_screen
            delta_y = mouse_pointer_y_measured_from_upper_left_corner_of_screen - canvas_upper_left_y_measured_from_upper_left_corner_of_screen
            old_center_x = self.canvas.canvasx(delta_x)
            old_center_y = self.canvas.canvasy(delta_y)
        new_center_x = factor_adapted * old_center_x
        new_center_y = factor_adapted * old_center_y
        self.canvas.configure(confine=False) # scan_dragto does now not depend on the scroll_region anymore.
        self.canvas.scale("all", 0, 0, factor_adapted, factor_adapted)
        self.canvas.scan_mark  (int(new_center_x), int(new_center_y))
        self.canvas.scan_dragto(int(old_center_x), int(old_center_y), gain=1)
        for block_edit in self.design.get_block_edit_list():
            block_edit.text_edit_widget.configure(font=("Courier", new_font_size))
            block_edit.text_edit_widget.prepare_for_syntax_highlighting() # Adapts the fontsize which is defined for the tags which are used for syntax highlighting
        self.last_factor = factor_adapted
        self.design.set_font_size(new_font_size)
        self.design.set_grid_size(self.design.get_grid_size()*factor_adapted)
        self.design.set_connector_size(self.design.get_connector_size()*factor_adapted)
        all_references = self.design.get_references()
        for reference in all_references: # Store the new places of all canvas items.
            reference.store_item(push_design_to_stack=False, signal_design_change=False)
        self.__store_visible_center_point()
        self.adjust_scroll_region_at_zoom(factor_adapted) # new grid size must be visible.
        self.grid_drawer.draw_grid()
        self.canvas.configure(confine=True)
        self.canvas.focus_set() # When zoom is started by a button, then the focus is on the button and not at canvas anymore.

    def __view_last(self):
        if self.last_factor!=0:
            self.__zoom(1/self.last_factor, "view_last", event=None)
            self.last_factor = 0
            self.canvas.configure(confine=False) # scan_dragto does now not depend on the scroll_region anymore.
            self.canvas.scan_mark  (0, 0)
            self.canvas.scan_dragto(-self.zoom_area_shift_x, -self.zoom_area_shift_y, gain=1)
            self.__adjust_scroll_region()
            self.grid_drawer.draw_grid()
            self.canvas.configure(confine=True)

    def __adjust_scroll_region(self):
        window = [self.canvas.canvasx(0), self.canvas.canvasy(0), self.canvas.canvasx(self.canvas.winfo_width ()), self.canvas.canvasy(self.canvas.winfo_height())]
        bbox   = self.canvas.bbox("all")
        if bbox is not None:
            if window[0]<bbox[0]:
                self.canvas_visible_area[0] = window[0]
            else:
                self.canvas_visible_area[0] = bbox[0]
            if window[1]<bbox[1]:
                self.canvas_visible_area[1] = window[1]
            else:
                self.canvas_visible_area[1] = bbox[1]
            if window[2]>bbox[2]:
                self.canvas_visible_area[2] = window[2]
            else:
                self.canvas_visible_area[2] = bbox[2]
            if window[3]>bbox[3]:
                self.canvas_visible_area[3] = window[3]
            else:
                self.canvas_visible_area[3] = bbox[3]
            self.canvas.configure(scrollregion=self.canvas_visible_area)
        else:
            self.canvas_visible_area = window

    def adjust_scroll_region_at_zoom(self, factor_adapted):
        # scroll_region_old = self.canvas.configure("scrollregion")[4].split()
        # scroll_region_old = [float(x) for x in scroll_region_old]
        # canvas_visible_are_new = [x*factor_adapted for x in scroll_region_old]
        canvas_visible_are_new = [x*factor_adapted for x in self.canvas_visible_area]
        window = [self.canvas.canvasx(0), self.canvas.canvasy(0), self.canvas.canvasx(self.canvas.winfo_width ()), self.canvas.canvasy(self.canvas.winfo_height())]
        if factor_adapted>1:
            self.canvas_visible_area = canvas_visible_are_new
        else:
            if window[0]<canvas_visible_are_new[0]:
                self.canvas_visible_area[0] = window[0]
            else:
                self.canvas_visible_area[0] = canvas_visible_are_new[0]
            if window[1]<canvas_visible_are_new[1]:
                self.canvas_visible_area[1] = window[1]
            else:
                self.canvas_visible_area[1] = canvas_visible_are_new[1]
            if window[2]>canvas_visible_are_new[2]:
                self.canvas_visible_area[2] = window[2]
            else:
                self.canvas_visible_area[2] = canvas_visible_are_new[2]
            if window[3]>canvas_visible_are_new[3]:
                self.canvas_visible_area[3] = window[3]
            else:
                self.canvas_visible_area[3] = canvas_visible_are_new[3]
        self.canvas.configure(scrollregion=self.canvas_visible_area)

    def __get_new_font_size(self, factor, command):
        new_font_size = factor * self.design.get_font_size()
        new_font_size_int = int(new_font_size)
        if (new_font_size_int==self.design.get_font_size() and  # The casting into "int" reduced the factor to 1,
            factor>1 and                                  # but the picture shall increase (factor>1) and it is not a "view all",
            command!="view_all"):                         # then the font size can be increased (to determine the real zoom-factor).
            new_font_size_int += 1                        # At "view all" the graphic could get bigger than the window,
            #print("aus Faktor 1 wurde Faktor 2 gemacht")
        return new_font_size_int                          # if the font size would be increased.

    def update_diagram_tab_from(self, new_design, push_design_to_stack): # push_design_to_stack is true at file-read, is false at Undo/Redo.
        self.__init_architecture_buttons_at_file_read(new_design["architecture_name"], new_design["architecture_list"])
        self.update_diagram_tab(new_design, push_design_to_stack) # push_design_to_stack is true at file-read, is false at Undo/Redo.

    def update_diagram_tab(self, new_design, push_design_to_stack): # Update without init_architecture_buttons_at_file_read() for design_data_selector
        references = self.__get_references_without_signalnames("all")
        for reference in references:
            reference.delete_item(push_design_to_stack=False) # The changes by delete shall not be tracked step by step.
        if "generate_frame_id" not in new_design: # Old versions of HDL-SCHEM-Editor do not support generate_frames
            new_design["generate_frame_id"] = 0
        self.architecture_name = new_design["architecture_name"]
        self.design.store_new_architecture_name(new_design["architecture_name"   ], signal_design_change=False)
        self.design.store_block_id             (new_design["block_id"            ])
        self.design.store_generate_frame_id    (new_design["generate_frame_id"   ])
        self.design.store_instance_id          (new_design["instance_id"         ])
        self.design.store_wire_id              (new_design["wire_id"             ])
        self.design.store_signal_name_font     (new_design["signal_name_font"    ], signal_design_change=False)
        self.design.store_font_size            (new_design["font_size"           ], signal_design_change=False)
        self.design.store_grid_size            (new_design["grid_size"           ], signal_design_change=False)
        self.design.store_connector_size       (new_design["connector_size"      ], signal_design_change=False)
        self.design.store_visible_center_point (new_design["visible_center_point"], signal_design_change=False, push_design_to_stack=False)
        wire_ref = None
        dummy    = None
        for canvas_id in new_design["canvas_dictionary"]:
            if   new_design["canvas_dictionary"][canvas_id][1]=="input":
                self.input_class          (self.window, self, dummy, follow_mouse=False, #push_design_to_stack=False,
                                  location      = new_design["canvas_dictionary"][canvas_id][2],
                                  orientation   = new_design["canvas_dictionary"][canvas_id][3])
            elif new_design["canvas_dictionary"][canvas_id][1]=="output":
                self.output_class         (self.window, self, dummy, follow_mouse=False, #push_design_to_stack=False,
                                  location      = new_design["canvas_dictionary"][canvas_id][2],
                                  orientation   = new_design["canvas_dictionary"][canvas_id][3])
            elif new_design["canvas_dictionary"][canvas_id][1]=="inout":
                self.inout_class          (self.window, self, dummy, follow_mouse=False, #push_design_to_stack=False,
                                  location      = new_design["canvas_dictionary"][canvas_id][2],
                                  orientation   = new_design["canvas_dictionary"][canvas_id][3])
            elif new_design["canvas_dictionary"][canvas_id][1]=="wire":
                wire_ref = self.wire_class(self.root, self.window, self, # push_design_to_stack=False,
                                  coords        = new_design["canvas_dictionary"][canvas_id][2],
                                  tags          = new_design["canvas_dictionary"][canvas_id][3],
                                  arrow         = new_design["canvas_dictionary"][canvas_id][4],
                                  width         = new_design["canvas_dictionary"][canvas_id][5])
            elif new_design["canvas_dictionary"][canvas_id][1]=="signal-name":
                self.signal_name_class    (self.design, self, #push_design_to_stack=False,
                                  coords        = new_design["canvas_dictionary"][canvas_id][2],
                                  angle         = new_design["canvas_dictionary"][canvas_id][3],
                                  declaration   = new_design["canvas_dictionary"][canvas_id][4],
                                  wire_tag      = new_design["canvas_dictionary"][canvas_id][5])
            elif new_design["canvas_dictionary"][canvas_id][1]=="block": # block-rectangle is also content of canvas_dictionary, but will be created by block_class object.
                if len(new_design["canvas_dictionary"][canvas_id])==7:
                    rect_color = new_design["canvas_dictionary"][canvas_id][6]
                else:
                    rect_color = constants.BLOCK_DEFAULT_COLOR
                self.block_class          (self.window, self, # push_design_to_stack=False,
                                  rect_coords   = new_design["canvas_dictionary"][canvas_id][2],
                                  rect_color    = rect_color,
                                  text_coords   = new_design["canvas_dictionary"][canvas_id][3],
                                  text          = new_design["canvas_dictionary"][canvas_id][4],
                                  block_tag     = new_design["canvas_dictionary"][canvas_id][5])
            elif new_design["canvas_dictionary"][canvas_id][1]=="instance":
                if "architecture_filename" not in new_design["canvas_dictionary"][canvas_id][2]:
                    new_design["canvas_dictionary"][canvas_id][2]["architecture_filename"] = "" # Designs created with old versions of HDL-SCHEM-Editor may not have this key.
                self.symbol_instance_class(self.root, self.window, self, # push_design_to_stack=False,
                                  symbol_definition=new_design["canvas_dictionary"][canvas_id][2])
            elif new_design["canvas_dictionary"][canvas_id][1]=="generate_frame":
                self.generate_frame_class(self.root, self.window, self, # push_design_to_stack=False,
                                  generate_definition=new_design["canvas_dictionary"][canvas_id][2])
        if wire_ref is not None: # Check is needed for schematics without any wires.
            wire_ref.add_dots_new_for_all_wires()
        self.canvas.update_idletasks() # This is needed to prevent winfo_width/height from being 1 in the following lines (only at the first read from file).
        new_center = [(self.canvas.canvasx(0) + self.canvas.canvasx(self.canvas.winfo_width ()))/2,
                      (self.canvas.canvasy(0) + self.canvas.canvasy(self.canvas.winfo_height()))/2]
        self.canvas.configure(confine=False) # scan_dragto does now not depend on the scroll_region anymore.
        self.canvas.scan_mark(*self.design.get_visible_center_point())
        self.canvas.scan_dragto(int(new_center[0]), int(new_center[1]), gain=1)
        if self.window.state!="withdrawn":
            self.__adjust_scroll_region()
            self.grid_drawer.draw_grid()
        self.canvas.configure(confine=True)
        self.design.add_change_to_stack(push_design_to_stack) # push_design_to_stack is only true, when data is read from a file.
        if wire_highlight.WireHighlight.highlight_object is not None:
            if self.window.winfo_viewable()==1:
                wire_highlight.WireHighlight.highlight_object.highlight_at_window_opening(self.window)
        self.window.notebook_top.show_tab("Diagram")
        self.window.update_idletasks()
        self.__view_all()

    def __start_drawing_selection_rectangle(self, event):
        self.canvas.focus_set() # needed to catch Ctrl-z
        event_x, event_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.canvas.tag_unbind("selected", "<Button-1>", self.funcid_button1_start_move_of_selection)
        self.funcid_button1_start_move_of_selection = None
        self.__unselect_elements()
        # Only if no item is near the Button-1 event, a new selection shall be created:
        canvas_ids_overlapping = self.canvas.find_overlapping(event_x-self.design.get_grid_size()/10, event_y-self.design.get_grid_size()/10,
                                                              event_x+self.design.get_grid_size()/10, event_y+self.design.get_grid_size()/10)
        found_item = 0
        for canvas_id_overlapping in canvas_ids_overlapping:
            if not "grid_line" in self.canvas.gettags(canvas_id_overlapping):
                found_item += 1
        if found_item==0:
            select_rectangle = self.canvas.create_rectangle(event_x, event_y,event_x, event_y, dash=(3,5))
            self.funcid_motion          = self.canvas.bind("<Motion>"           , lambda event: self.__expand_rectangle(event, select_rectangle))
            self.funcid_button1_release = self.canvas.bind("<ButtonRelease-1>"  , lambda event: self.__select_items_in_selection_rectangle (select_rectangle))

    def __unselect_elements(self, references=()):
        if self.funcid_button1_start_move_of_selection is not None: # Remove the binding of _move_selection_start from all selected elements.
            self.canvas.tag_unbind("selected", "<Button-1>", self.funcid_button1_start_move_of_selection)
            self.funcid_button1_start_move_of_selection = None
        selected_canvas_ids = self.canvas.find_withtag("selected")
        if not references:
            references = self.design.get_references(selected_canvas_ids)
        if references:
            for ref in references:
                ref.unselect_item()
        else:
            for selected_canvas_id in selected_canvas_ids:
                if self.canvas.type(selected_canvas_id)=="polygon":
                    tags_of_polygon = self.canvas.gettags(selected_canvas_id)
                    for tag in tags_of_polygon:
                        if tag.startswith("instance"):
                            object_tag = tag
                            break
                    canvas_ids = self.canvas.find_withtag(object_tag)
                    for canvas_id in canvas_ids:
                        if self.canvas.type(canvas_id)=="rectangle":
                            canvas_id_rectangle = canvas_id
                            break
                    references_to_instance = self.design.get_references([canvas_id_rectangle])[0]
                    if "symbol_color" in references_to_instance.symbol_definition["rectangle"]:
                        symbol_color = references_to_instance.symbol_definition["rectangle"]["symbol_color"]
                    else:
                        symbol_color = constants.SYMBOL_DEFAULT_COLOR
                    self.canvas.itemconfigure(selected_canvas_id, fill=symbol_color)
        self.canvas.dtag("selected", "selected")
        self.polygon_move_list = []
        self.copy_button.configure(state="disabled")

    def __get_references_without_signalnames(self, tag):
        references_to_selected = []
        selected_canvas_ids = self.canvas.find_withtag(tag)
        for selected_canvas_id in selected_canvas_ids:
            ref = self.design.get_references([selected_canvas_id])
            if ref != []: # There are Canvas items, which do not have a reference, for example the polygons of an instance.
                tags = self.canvas.gettags(selected_canvas_id)
                if "signal-name" not in tags: # signal-names are handled by the wire to which the signal-name belongs.
                    references_to_selected.append(ref[0])
            else: # A canvas item is found by the tag, which has no entry in the canvas dictionary, but belongs to a bigger canvas object.
                pass
        return references_to_selected

    def delete_selection(self):
        references_to_selected = self.__get_references_without_signalnames("selected")
        for reference in references_to_selected:
            reference.delete_item(push_design_to_stack=False) # removes from Canvas-dictionary and from Canvas.
        self.design.add_change_to_stack(push_design_to_stack=True)

    def __select_items_in_selection_rectangle(self, select_rectangle):
        # The selection is used for "delete" and "move" and "copy".
        # The selection is build from canvas IDs.
        # But some objects at the canvas are build from more than one canvas items and
        # it is not allowed, that not all canvas IDs from such an object are in the selection.
        # But the selection rectangle may not include all these needed canvas IDs.
        # So it must be checked that the selection is complete.
        # This can only be done by getting the reference for each selected Canvas ID from the design dictionary.
        # Then for each reference all its canvas IDs must be determined.
        # But when the design was built by reading from a file, the order in which the canvas items (which together
        # build an object) are created, is not predictable. Perhaps a signal name is created before the signal line.
        # Then by the signal name reference it is not possible to get the Canvas ID of the signal line.
        # So for each Canvas object which is built not only from one Canvas item, there must exist a common tag,
        # which is stored at each Canvas item which belongs to this object.
        self.canvas.unbind("<Motion>"         , self.funcid_motion)
        self.canvas.unbind("<ButtonRelease-1>", self.funcid_button1_release)
        self.funcid_motion          = None
        self.funcid_button1_release = None
        self.coords_select_rectangle = self.canvas.coords(select_rectangle)
        self.canvas.addtag_enclosed("selected", *self.canvas.coords(select_rectangle))
        self.canvas.delete(select_rectangle)
         # Remove dots from "selected": Dots shall not be moved as they are new placed after a movement.
        for canvas_item in self.canvas.find_withtag("selected"):
            if self.canvas.type(canvas_item)=="oval":
                self.canvas.dtag(canvas_item, "selected")
        self.polygon_move_list = []
        references = self.design.get_references(self.canvas.find_withtag("selected"))
        if references:
            self.canvas.dtag("selected", "selected") # Remove the selection in order to expand it to not selected parts of the selected elements.
            all_object_tags = []
            for reference in references:
                all_object_tags.append(reference.get_object_tag())
            for object_tag in all_object_tags:
                self.canvas.addtag_withtag("selected", object_tag)
            for reference in references:
                reference.select_item() # Highlights all items and deactivates all bindings at the items
            self.funcid_button1_start_move_of_selection = self.canvas.tag_bind("selected", "<Button-1>",
                                                                               lambda event: self.__move_selection_start(event, references))
            self.copy_button.configure(state="active")
        else: # If no object with a reference was "enclosed", then move the "enclosed" polygons
            canvas_ids_selected = self.canvas.find_withtag("selected")
            if canvas_ids_selected: # At least one canvas item is enclosed in the selection rectangle.
                self.__create_polygon_move_list_and_mark_with_red(canvas_ids_selected)
                # The "selected" tag must not be removed here, as it is needed in the case when the polygon selection
                # is not used and the red color must be removed from the selection.
                # When the polygon selection is used, then the red color and the "selected" tag are removed by PolygonMove.

    def __create_polygon_move_list_and_mark_with_red(self, canvas_ids_selected):
        for canvas_id_selected in canvas_ids_selected:
            if self.canvas.type(canvas_id_selected)=="polygon":
                self.canvas.itemconfigure(canvas_id_selected, fill="red")
                object_tag = self.canvas.gettags(canvas_id_selected)[0]
                symbol_canvas_ids = self.canvas.find_withtag(object_tag)
                for symbol_canvas_id in symbol_canvas_ids:
                    if self.canvas.type(symbol_canvas_id)=="rectangle":
                        symbol_reference = self.design.get_references([symbol_canvas_id])[0]
                self.polygon_move_list.append([symbol_reference, canvas_id_selected])

    def get_polygon_move_list(self): # Used by symbol_polygon_move.
        return_list = list(self.polygon_move_list)
        self.polygon_move_list = []
        return return_list

    def __move_selection_start(self, event, references):
        self.remove_canvas_bindings() # Because the mouse click after paste (to end the moving of the new elements) shall not start a new selection.
        self.event_x = self.canvas.canvasx(event.x)
        self.event_y = self.canvas.canvasy(event.y)
        if self.funcid_button1_release is None: # Check is needed, because __move_selection-start may be called twice.
            # The references must be moved to the grid in a last move action.
            # At move begin, the references are located at the grid.
            # To determine the distance from the grid after the last moving an anchor object is created here, which can be identified by the tag "move_anchor".
            # This anchor object is placed at the grid before movement by using 2 coordinates of one of the canvas widgets, which have to be moved.
            # After moving the delta_x/y to the grid can easily be determined by looking at the anchor object.
            object_tag_of_one_object = references[0].get_object_tag()
            canvas_id_of_one_object  = self.canvas.find_withtag(object_tag_of_one_object)[0]
            coords_of_anchor_object  = self.canvas.coords(canvas_id_of_one_object)[0:2]
            # For the move_anchor an object is used, which is not used for any other purpose, because the checks for finding overlapping items
            # do not search or check for an "arc":
            self.canvas.create_arc(coords_of_anchor_object[0],coords_of_anchor_object[1],
                                   coords_of_anchor_object[0],coords_of_anchor_object[1], tags=("move_anchor", "selected"), width=0)
            self.funcid_motion          = self.canvas.bind("<Motion>"         , self.__move_selection_to)
            self.funcid_button1_release = self.canvas.bind("<ButtonRelease-1>", lambda event: self.__move_selection_end(event, references, coords_of_anchor_object))

    def __move_selection_to(self, event):
        new_event_x = self.canvas.canvasx(event.x)
        new_event_y = self.canvas.canvasy(event.y)
        self.canvas.move("selected", new_event_x-self.event_x, new_event_y-self.event_y)
        self.event_x = new_event_x
        self.event_y = new_event_y

    def __move_selection_end(self, event, references, coords_of_anchor_object):
        # The selection is not removed here, because the user might want to move the selection again.
        self.canvas.unbind("<Motion>"         , self.funcid_motion)
        self.canvas.unbind("<ButtonRelease-1>", self.funcid_button1_release)
        self.funcid_motion          = None
        self.funcid_button1_release = None
        self.__move_selection_to_grid("selected", event, coords_of_anchor_object)
        if references!=[]:
            self.__store_moved_elements(references)
        self.create_canvas_bindings()

    def __store_moved_elements(self, references):
        wire_reference = None
        for reference in references:
            reference.store_item(push_design_to_stack=False, signal_design_change=False)
            if isinstance(reference, wire_insertion.Wire):
                wire_reference = reference
        if wire_reference:
            wire_reference.add_dots_new_for_all_wires()
        references[0].store_item(push_design_to_stack=True, signal_design_change=True) # Store again, in order to create 1 stack entry

    def __move_selection_to_grid(self, tag_or_id, event, coords_of_anchor_object):
        # Determine the distance of the anchor point to the grid:
        anchor_x, anchor_y = self.canvas.coords("move_anchor")[0:2]
        remainder_x = (anchor_x - coords_of_anchor_object[0]) % self.design.get_grid_size()
        remainder_y = (anchor_y - coords_of_anchor_object[1]) % self.design.get_grid_size()
        # Move the symbol to the grid:
        delta_x = - remainder_x
        delta_y = - remainder_y
        if remainder_x>self.design.get_grid_size()/2:
            delta_x += self.design.get_grid_size()
        if remainder_y>self.design.get_grid_size()/2:
            delta_y += self.design.get_grid_size()
        self.canvas.move(tag_or_id, delta_x, delta_y)
        #print("anchor coords at grid: ", self.canvas.coords("move_anchor")[0:2] )
        self.canvas.delete("move_anchor")

    def undo(self):
        new_design = self.design.get_previous_design_dictionary()
        if new_design is not None:
            self.update_diagram_tab(new_design, push_design_to_stack=False)
            self.design.update_hierarchy() # Needed because at update_diagram_tab (see line before) the push_design_to_stack has the value False.
    def redo(self):
        new_design = self.design.get_later_design_dictionary()
        if new_design is not None:
            self.update_diagram_tab(new_design, push_design_to_stack=False)
            self.design.update_hierarchy() # Needed because at update_diagram_tab (see line before) the push_design_to_stack has the value False.

    def find_string(self, search_string, replace, new_string):
        number_of_hits = 0
        all_canvas_ids = self.canvas.find_all()
        for canvas_id in all_canvas_ids:
            if self.canvas.type(canvas_id)=="text": # block, signal_name (not the declaration), instance_name, generic_map, generate-condition
                if replace:
                    all_tags = self.canvas.gettags(canvas_id)
                    # No replacement in entity-name or symbol-port-names:
                    if ("block-text"     in all_tags or
                        "signal-name"    in all_tags or
                        "instance-name"  in all_tags or
                        "generate-frame" in all_tags or
                        "generic-map"    in all_tags):
                        number_of_hits += self.__search_in_canvas_text(canvas_id, search_string, replace, new_string)
                else:
                    hits = self.__search_in_canvas_text(canvas_id, search_string, replace, new_string)
                    if hits==-1:
                        return -1
                    number_of_hits += hits
        return number_of_hits

    def __search_in_canvas_text(self, canvas_id, search_string, replace, new_string):
        number_of_hits = 0
        tags_of_canvas_text = self.canvas.gettags(canvas_id)
        if "signal-name" in tags_of_canvas_text:
            reference = self.design.get_references([canvas_id])[0]
            text = reference.get_declaration()
        else:
            text = self.canvas.itemcget(canvas_id, "text")
        if replace:
            number_of_hits = len(re.findall(search_string, text, flags=re.IGNORECASE))
            if number_of_hits!=0: # Important to check, because no new entry at the stack shall be created, if nothing has changed.
                new_text = re.sub(search_string, new_string, text, flags=re.IGNORECASE)
                self.canvas.itemconfigure(canvas_id, text=new_text)
                all_tags = self.canvas.gettags(canvas_id)
                if "block-text" in all_tags:
                    reference = self.design.get_references([canvas_id])[0]
                    reference.store_item(push_design_to_stack=True, signal_design_change=True)
                elif "generate-frame" in all_tags:
                    for tag in all_tags:
                        if tag.startswith("generate_frame_"):
                            object_tag = tag
                    hit_list = self.canvas.find_withtag(object_tag)
                    for canvas_id in hit_list:
                        if self.canvas.type(canvas_id)=="rectangle":
                            reference = self.design.get_references([canvas_id])[0]
                            reference.store_item(push_design_to_stack=True, signal_design_change=True)
                elif "signal-name" in all_tags:
                    reference.change_declaration(new_text) # includes also a store_item() call.
                else: # "instance-name" in all_tags, or "generic-map" in all_tags
                    for tag in all_tags:
                        if tag.startswith("instance_"):
                            object_tag_of_instance = tag
                    all_canvas_ids_of_instance = self.canvas.find_withtag(object_tag_of_instance)
                    for single_canvas_id in all_canvas_ids_of_instance:
                        if self.canvas.type(single_canvas_id)=="rectangle":
                            reference = self.design.get_references([single_canvas_id])[0]
                    reference.store_item(push_design_to_stack=True, signal_design_change=True)
            return number_of_hits
        start_index = 0
        while True:
            hit_begin = text.lower().find(search_string, start_index, len(text))
            if hit_begin!=-1:
                number_of_hits += 1
                self.window.notebook_top.show_tab("Diagram")
                self.canvas.select_from(canvas_id, hit_begin)
                self.canvas.select_to  (canvas_id, hit_begin + len(search_string) - 1)
                object_coords = self.canvas.bbox(canvas_id)
                self.__zoom_area(object_coords, "not view_all")
                continue_search = messagebox.askyesno("Continue ...", "Find next?")
                self.canvas.select_clear()
                if not continue_search:
                    number_of_hits = -1
                    break
                start_index = hit_begin + len(search_string)
            else:
                break
        return number_of_hits

    # Called by architecture select combobox:
    def __switch_to_other_architecture(self):
        new_architecture_name = self.architecture_list[self.architecture_combobox.current()]
        self.architecture_combobox.selection_clear()
        self.design.open_existing_schematic(self.architecture_name, new_architecture_name)

    # Called by "new Architecture" button:
    def __create_new_architecture_name(self):
        ask_architecture_window, create_button, cancel_button, architecture_entry = self.__open_entry_window()
        create_button.bind("<Button-1>", lambda event: self.__store_new_architecture_name(ask_architecture_window))
        cancel_button.bind("<Button-1>", lambda event: ask_architecture_window.destroy())
        architecture_entry.bind("<Return>", lambda event: self.__store_new_architecture_name(ask_architecture_window))
    def __store_new_architecture_name(self, ask_architecture_window):
        ask_architecture_window.destroy()
        new_architecture_name = self.architecture_name_stringvar.get()
        if new_architecture_name not in self.architecture_list:
            self.architecture_list.append(new_architecture_name)
            self.architecture_combobox.configure(values=self.architecture_list)
            self.delete_architecture_button.configure(state="enabled")
            self.design.create_new_and_empty_schematic(self.architecture_name) # Design-Data of self.architecture_name is stored first.
            self.design.store_new_architecture_name(new_architecture_name, signal_design_change=True)
            self.architecture_name = new_architecture_name
        else:
            self.design.open_existing_schematic(self.architecture_name, new_architecture_name)
        self.architecture_combobox.set(new_architecture_name)

    # Called by "delete Architecture" button:
    def __delete_architecture(self):
        # Because a messagebox is opened next, first the "released" state of the button must be waited for.
        self.window.after_idle(self.__delete_architecture_after_idle)
    def __delete_architecture_after_idle(self):
        if len(self.architecture_list)>1:
            delete_architecture = messagebox.askyesno("Delete architecture", "Are you sure you want to delete the architecture " +
                                                    self.architecture_name + "? All data will be removed from the database.")
            if delete_architecture:
                self.architecture_list.remove(self.architecture_name)
                if len(self.architecture_list)==1:
                    self.delete_architecture_button.configure(state="disabled")
                self.architecture_combobox.configure(values=self.architecture_list)
                new_architecture = self.architecture_list[0]
                self.architecture_combobox.set(new_architecture)
                self.design.delete_schematic(self.architecture_name, new_architecture)
        else:
            messagebox.showerror("delete architecture", "last architecture cannot be deleted")

    # Called by "rename Architecture" button:
    def __rename_architecture(self):
        ask_architecture_window, create_button, cancel_button, architecture_entry = self.__open_entry_window()
        create_button.bind("<Button-1>", lambda event: self.__change_architecture_name(ask_architecture_window))
        cancel_button.bind("<Button-1>", lambda event: ask_architecture_window.destroy())
        architecture_entry.bind("<Return>", lambda event: self.__change_architecture_name(ask_architecture_window))
    def __change_architecture_name(self, ask_architecture_window):
        ask_architecture_window.destroy()
        new_architecture_name = self.architecture_name_stringvar.get()
        if new_architecture_name not in self.architecture_list:
            self.architecture_list.remove(self.architecture_name)
            self.architecture_list.append(new_architecture_name)
            self.architecture_combobox.configure(values=self.architecture_list)
            self.architecture_combobox.set(new_architecture_name)
            self.design.schematic_was_renamed(self.architecture_name)
            self.design.store_new_architecture_name(new_architecture_name, signal_design_change=True)
            self.architecture_name = new_architecture_name
        else:
            messagebox.showerror("Renaming-Error","New architecture name " + new_architecture_name + " already exists.")

    def __init_architecture_buttons_at_file_read(self, architecture, architecture_list):
        # unnötig: self.architecture_name = architecture
        self.architecture_list = architecture_list
        self.architecture_combobox.set(architecture)
        self.architecture_combobox.configure(values=self.architecture_list)
        if len(self.architecture_list)!=1:
            self.delete_architecture_button.configure(state="enabled")

    def clear_canvas_for_new_schematic(self):
        all_canvas_ids = self.canvas.find_all()
        for canvas_id in all_canvas_ids:
            self.canvas.delete(canvas_id)
            self.grid_drawer.draw_grid()

    def __open_entry_window(self):
        self.architecture_name_stringvar.set("")
        ask_architecture_window = tk.Toplevel(padx=10, pady=10)
        enter_label        = ttk.Label (ask_architecture_window, takefocus=False, text="New architecture name:")
        architecture_entry = ttk.Entry (ask_architecture_window, width=80, justify="left", textvariable=self.architecture_name_stringvar)
        button_frame       = ttk.Frame (ask_architecture_window, borderwidth=0, relief='flat')
        create_button      = ttk.Button(button_frame, takefocus=False, text="Enter", style="NewState.TButton")
        cancel_button      = ttk.Button(button_frame, takefocus=False, text="Cancel", style="NewState.TButton")
        enter_label       .grid(row=0, column=0, sticky=(tk.W, tk.E))
        architecture_entry.grid(row=1, column=0)
        button_frame      .grid(row=2, column=0, sticky=tk.W)
        create_button     .grid(row=0, column=0)
        cancel_button     .grid(row=0, column=1)
        return [ask_architecture_window, create_button, cancel_button, architecture_entry]

    def highlight_item(self, hdl_item_type, object_identifier, number_of_line):
        if hdl_item_type in ["port_declaration", "signal_declaration"]: # The port_declaration does not contain "in", "out", "inout" anymore.
            signal_name_canvas_id = self.__get_canvas_id_of_signal_name(object_identifier)
            wire_canvas_id        = self.__get_canvas_id_of_wire       (signal_name_canvas_id)
            if wire_highlight.WireHighlight.highlight_object is not None:
                wire_highlight.WireHighlight.highlight_object.unhighlight_all_and_delete_object()
            if wire_highlight.WireHighlight.highlight_object is None:
                wire_highlight.WireHighlight(self.root)
            wire_highlight.WireHighlight.highlight_object.add_to_highlight(self.window, wire_canvas_id, "flat")
            self.__view_all()
        elif hdl_item_type=="embedded_library_instruction":
            all_instance_name_canvas_ids = self.canvas.find_withtag("instance-name")
            for instance_name_canvas_id in all_instance_name_canvas_ids:
                instance_name = self.canvas.itemcget(instance_name_canvas_id, "text")
                if instance_name.startswith(object_identifier): # instance_name may have a attached VHDL comment
                    all_tags_of_instance_name_text = self.canvas.gettags(instance_name_canvas_id)
                    for tag in all_tags_of_instance_name_text:
                        if tag.startswith("instance_"):
                            symbol_object_tag = tag
                            break
                    break
            canvas_ids_of_symbol_parts = self.canvas.find_withtag(symbol_object_tag)
            for canvas_id in canvas_ids_of_symbol_parts:
                if self.canvas.type(canvas_id)=="rectangle":
                    symbol_ref = self.design.get_references([canvas_id])[0]
                    symbol_properties.SymbolProperties(symbol_ref)
        elif hdl_item_type=="generate":
            tags = self.canvas.gettags(object_identifier)
            for tag in tags:
                if tag.startswith("generate_frame_"):
                    object_tag = tag
            canvas_items_with_object_tag = self.canvas.find_withtag(object_tag)
            for canvas_id in canvas_items_with_object_tag:
                if self.canvas.type(canvas_id)=="text":
                    canvas_id_of_generate_text = canvas_id
            bbox = list(self.canvas.bbox(canvas_id_of_generate_text))
            bbox = self.__increase_bbox(bbox)
            self.__zoom_area(bbox, "zoom_rectangle")
            generate_ref = self.design.get_references([object_identifier])[0]
            generate_ref.edit()
        elif hdl_item_type=="block":
            bbox = list(self.canvas.bbox(object_identifier)) # object_identifier = canvas-id of text
            bbox = self.__increase_bbox(bbox)
            self.__zoom_area(bbox, "zoom_rectangle")
            text = self.canvas.itemcget(object_identifier, "text")
            text_list = text.split("\n")
            if self.design.get_language()=="VHDL":
                match_obj = re.match(r"^\s*--\s*[0-9]+\s*$", text_list[0])
            else:
                match_obj = re.match(r"^\s*//\s*[0-9]+\s*$", text_list[0])
            if match_obj is not None: # The block starts with a priority comment which is not visible in HDL.
                number_of_line += 1
            block_reference = self.design.get_references([object_identifier])[0]
            custom_text_ref = block_reference.edit_block()
            if custom_text_ref is not None:
                custom_text_ref.highlight_item("", "", number_of_line)
        elif hdl_item_type=="instance_name":
            symbol_reference = self.design.get_references([object_identifier])[0]
            canvas_id_of_instance_name = symbol_reference.symbol_definition["instance_name"]["canvas_id"]
            bbox = list(self.canvas.bbox(canvas_id_of_instance_name))
            bbox = self.__increase_bbox(bbox)
            self.__zoom_area(bbox, "zoom_rectangle")
            edit_line.EditLine(self.design, self, canvas_id_of_instance_name, symbol_reference)
        elif hdl_item_type=="generic_mapping":
            symbol_reference = self.design.get_references([object_identifier])[0]
            canvas_id_of_generic_map = symbol_reference.symbol_definition["generic_block"]["canvas_id"]
            bbox = list(self.canvas.bbox(canvas_id_of_generic_map))
            bbox = self.__increase_bbox(bbox)
            self.__zoom_area(bbox, "zoom_rectangle")
            edit_text.EditText("generic_block", self.window, self, symbol_reference.symbol_definition["generic_block"]["canvas_id"], symbol_reference, number_of_line)
        elif hdl_item_type=="port_connection":
            symbol_reference = self.design.get_references([object_identifier])[0]
            name_of_connected_signal = number_of_line # number_of_line contains the name of the connected signal
            canvas_id_of_symbol_rectangle = symbol_reference.symbol_definition["rectangle"]["canvas_id"]
            bbox = list(self.canvas.bbox(canvas_id_of_symbol_rectangle))
            bbox = self.__increase_bbox(bbox)
            self.__zoom_area(bbox, "zoom_rectangle")
            signal_name_canvas_id = self.__get_canvas_id_of_signal_name(name_of_connected_signal)
            wire_canvas_id        = self.__get_canvas_id_of_wire       (signal_name_canvas_id)
            if wire_highlight.WireHighlight.highlight_object is not None:
                wire_highlight.WireHighlight.highlight_object.unhighlight_all_and_delete_object()
            if wire_highlight.WireHighlight.highlight_object is None:
                wire_highlight.WireHighlight(self.root)
            wire_highlight.WireHighlight.highlight_object.add_to_highlight(self.window, wire_canvas_id, "flat")

    def __get_canvas_id_of_signal_name(self, object_identifier):
        all_signal_name_canvas_ids = self.canvas.find_withtag("signal-name")
        language = self.design.get_language()
        for signal_name_canvas_id in all_signal_name_canvas_ids:
            ref = self.design.get_references([signal_name_canvas_id])[0]
            signal_name_declaration = ref.declaration
            signal_name, _, _, _, _ = hdl_generate_functions.HdlGenerateFunctions.split_declaration(signal_name_declaration, language)
            if language=="VHDL":
                if signal_name==object_identifier:
                    return signal_name_canvas_id
            else:
                signal_name_without_range = re.sub(r"\[.*", "", signal_name) # Verilog-signals may have a range at the end.
                if signal_name_without_range==object_identifier:
                    return signal_name_canvas_id

    def __get_canvas_id_of_wire(self, signal_name_canvas_id):
        all_tags = self.canvas.gettags(signal_name_canvas_id)
        for tag in all_tags:
            if tag.startswith("wire") and not tag.endswith("_signal_name"):
                list_of_canvas_ids = self.canvas.find_withtag(tag)
                for canvas_id in list_of_canvas_ids:
                    if self.canvas.type(canvas_id)=="line" and "grid_line" not in self.canvas.gettags(canvas_id):
                        return canvas_id

    def __increase_bbox(self, bbox):
        half_bbox_width = (bbox[2] - bbox[0])/2
        bbox[0] = bbox[0] - half_bbox_width
        bbox[2] = bbox[2] + half_bbox_width
        half_bbox_height = (bbox[3] - bbox[1])/2
        bbox[1] = bbox[1] - half_bbox_height
        bbox[3] = bbox[3] + half_bbox_height
        return bbox

    def hide_hierarchy_window(self):
        self.paned_window.forget(self.treeview_frame)
        self.grid_drawer.draw_grid()

    def show_hierarchy_window(self):
        self.paned_window.add(self.treeview_frame, weight=1)
