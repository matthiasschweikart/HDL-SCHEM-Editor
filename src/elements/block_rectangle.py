"""Manages the rectangle around a block text"""


class BlockRectangle:
    """Manages the rectangle around a block text."""

    def __init__(
        self,
        window,  #      : schematic_window.SchematicWindow,
        diagram_tab,  # : notebook_diagram_tab.NotebookDiagramTab,
        coords,
        color,
        block_tag,
        push_design_to_stack,
    ):
        self.window = window
        self.diagram_tab = diagram_tab
        self.block_tag = block_tag
        self.canvas_id = self.diagram_tab.canvas.create_rectangle(
            coords, fill=color, tags=(self.block_tag, "layer4", "schematic-element"), activeoutline="red", activewidth=3
        )
        self.store_item(push_design_to_stack, signal_design_change=False)

    def delete_item(self, push_design_to_stack):
        """Deletes the block rectangle."""
        self.window.design.remove_canvas_item_from_dictionary(self.canvas_id, push_design_to_stack)
        self.diagram_tab.canvas.delete(self.canvas_id)
        del self  # Once the last reference to an object is deleted, the object will be removed by garbage collection.

    def select_item(self):
        """Highlights the block rectangle, which is needed for selection."""
        self.diagram_tab.canvas.itemconfigure(self.canvas_id, outline="red", width=3)  # Will be called by diagram_tab.

    def move_item(self, delta_x, delta_y):
        """Moves the block rectangle by the given delta values."""
        self.diagram_tab.canvas.move(self.canvas_id, delta_x, delta_y)

    def move_corner(self, delta_x, delta_y, touching_point):
        """Moves a corner of the block rectangle by the given delta values."""
        coords = self.diagram_tab.canvas.coords(self.canvas_id)
        # print("coords     =", coords)
        new_coords = list(coords)
        if touching_point == "top_left":
            new_coords[0] = coords[0] + delta_x
            new_coords[1] = coords[1] + delta_y
        elif touching_point == "top_right":
            new_coords[1] = coords[1] + delta_y
            new_coords[2] = coords[2] + delta_x
        elif touching_point == "bottom_left":
            new_coords[0] = coords[0] + delta_x
            new_coords[3] = coords[3] + delta_y
        elif touching_point == "bottom_right":
            new_coords[2] = coords[2] + delta_x
            new_coords[3] = coords[3] + delta_y
        # Guarantee a minimal rectangle size of 2 times gridsize:
        # In order to compensate a not exact calculation use factor 1.999 instead of factor 2:
        if (
            new_coords[2] - new_coords[0] >= 1.999 * self.window.design.get_grid_size()
            and new_coords[3] - new_coords[1] >= 1.999 * self.window.design.get_grid_size()
        ):
            self.diagram_tab.canvas.coords(self.canvas_id, new_coords)
            return True
        return False

    def unselect_item(self):
        """Unhighlights the block rectangle, which is needed for deselection."""
        self.diagram_tab.canvas.itemconfigure(
            self.canvas_id, outline="black", width=1
        )  # Will be called by diagram_tab.

    def store_item(self, push_design_to_stack, signal_design_change):
        """Stores the block rectangle in the canvas dictionary, which is needed for undo/redo and file write."""
        # The rectangle is stored in canvas_dictionary (but not in the project file), because:
        # - at update_diagram_tab_from() in diagram_tab,all canvas elements are first removed by reference.delete_item()
        # - at __zoom() in diagram_tab, all canvas elements are first stored by reference.store_item()
        # - for undo/redo and call of store_item()
        self.window.design.store_block_rectangle_in_canvas_dictionary(self.canvas_id, self, push_design_to_stack)

    def get_canvas_id(self):
        """Returns the canvas id of the block rectangle, which is needed for moving and deleting."""
        return self.canvas_id

    def get_object_tag(self):
        """Returns the object tag of the block rectangle."""
        return self.block_tag

    def add_pasted_tag_to_all_canvas_items(self):
        """Adds a 'pasted' tag to all canvas items of the block rectangle."""
        self.diagram_tab.canvas.addtag_withtag("pasted_tag", self.canvas_id)

    def adapt_coordinates_by_factor(self, factor):
        """Adapts the coordinates of the block rectangle by the given factor."""
        coords = self.diagram_tab.canvas.coords(self.canvas_id)
        coords = [value * factor for value in coords]
        self.diagram_tab.canvas.coords(self.canvas_id, coords)
