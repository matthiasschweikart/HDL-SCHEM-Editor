"""Dots for wires"""


class Dot:
    """Class for the dots on wires. The dot is a small circle, which is drawn on the canvas."""

    def __init__(self, schematic_window, push_design_to_stack, coords, line_size):
        self.window = schematic_window
        if line_size == 1:
            radius = 0.2 * self.window.design.get_grid_size()
        else:
            radius = 0.4 * self.window.design.get_grid_size()
        self.dot_canvas_id = self.window.notebook_top.diagram_tab.canvas.create_oval(
            coords[0] - radius,
            coords[1] - radius,
            coords[0] + radius,
            coords[1] + radius,
            fill="black",
            tag="schematic-element",
        )
        self.window.design.store_dot_in_canvas_dictionary(self.dot_canvas_id, self, coords, push_design_to_stack)

    def delete_item(self, push_design_to_stack):
        """Deletes the dot."""
        # Because a dot is also deleted, when the wire the dot belongs to is deleted,
        # it must be checked if there is still a dot:
        reference = self.window.design.get_references([self.dot_canvas_id])
        if reference != []:
            self.window.design.remove_canvas_item_from_dictionary(self.dot_canvas_id, push_design_to_stack)
            self.window.notebook_top.diagram_tab.canvas.delete(self.dot_canvas_id)

    def select_item(self):
        """Highlights the dot, which is needed for selection."""
        self.window.notebook_top.diagram_tab.canvas.itemconfigure(self.dot_canvas_id, fill="red")

    def unselect_item(self):
        """Unhighlights the dot, which is needed for deselection."""
        self.window.notebook_top.diagram_tab.canvas.itemconfigure(self.dot_canvas_id, fill="black")

    def store_item(self, push_design_to_stack, signal_design_change):
        """Stores the dot in the canvas dictionary, which is needed for undo/redo and file write."""
        coords = self.window.notebook_top.diagram_tab.canvas.coords(self.dot_canvas_id)
        coords[0] = (coords[2] + coords[0]) / 2
        coords[1] = (coords[3] + coords[1]) / 2
        self.window.design.store_dot_in_canvas_dictionary(
            self.dot_canvas_id, self, [coords[0], coords[1]], push_design_to_stack
        )

    def get_object_tag(self):
        """Returns the object tag of the dot."""
        return self.dot_canvas_id  # allowed, because a dot consists only from 1 canvas item.
