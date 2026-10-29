"""
This class draws a grid into the canvas.
"""

import constants


class GridDraw:
    """This class is used for drawing a grid into the canvas."""

    def __init__(self, root, diagram_tab, design, canvas):
        self.root = root
        self.diagram_tab = diagram_tab
        self.design = design
        self.canvas = canvas
        self.color = constants.GRID_COLOR_NORMAL_MODE

    def remove_grid(self):
        """Removes the grid from the canvas."""
        self.canvas.delete("grid_line")

    def draw_grid(self):
        """Draws a grid into the canvas."""
        if self.root.show_grid:
            self.remove_grid()
            grid_size = self.design.get_grid_size()
            if grid_size > 8:
                self._draw_horizontal_grid(grid_size, self.diagram_tab.canvas_visible_area)
                self._draw_vertical_grid(grid_size, self.diagram_tab.canvas_visible_area)
            self.canvas.tag_lower("grid_line")

    def _draw_horizontal_grid(self, grid_size, canvas_visible_area):
        # An extra margin of 3*grid_size is used because otherwise there are sometimes too few grid-lines:
        x_min = canvas_visible_area[0] - canvas_visible_area[0] % grid_size - 3 * grid_size
        x_max = canvas_visible_area[2] + canvas_visible_area[2] % grid_size + 3 * grid_size
        y = canvas_visible_area[1] - canvas_visible_area[1] % grid_size - 3 * grid_size
        y_max = canvas_visible_area[3] + canvas_visible_area[3] % grid_size + 3 * grid_size
        while y < y_max:
            self.canvas.create_line(x_min, y, x_max, y, dash=(1, 1), fill=self.color, tags=("grid_line", "layer5"))
            y += grid_size

    def _draw_vertical_grid(self, grid_size, canvas_visible_area):
        x = canvas_visible_area[0] - canvas_visible_area[0] % grid_size - 3 * grid_size
        x_max = canvas_visible_area[2] + canvas_visible_area[2] % grid_size + 3 * grid_size
        y_min = canvas_visible_area[1] - canvas_visible_area[1] % grid_size - 3 * grid_size
        y_max = canvas_visible_area[3] + canvas_visible_area[3] % grid_size + 3 * grid_size
        while x < x_max:
            self.canvas.create_line(x, y_min, x, y_max, dash=(1, 1), fill=self.color, tags=("grid_line", "layer5"))
            x += grid_size
