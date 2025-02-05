"""
This class draws a grid into the canvas.
"""

class GridDraw():
    def __init__(self, root, diagram_tab, design, canvas):
        self.root        = root
        self.diagram_tab = diagram_tab
        self.design      = design
        self.canvas      = canvas

    def draw_grid(self):
        if self.root.show_grid is True:
            self.remove_grid()
            grid_size = self.design.get_grid_size()
            if grid_size>10:
                self.__draw_horizontal_grid(grid_size)
                self.__draw_vertical_grid  (grid_size)
            #self.canvas.create_oval(-2,-2,+2,+2, fill="red", tags="grid_line")

    def remove_grid(self):
        self.canvas.delete("grid_line")

    def __draw_horizontal_grid(self, grid_size):
        x_min = self.diagram_tab.canvas_visible_area[0] - self.diagram_tab.canvas_visible_area[0] % grid_size
        x_max = self.diagram_tab.canvas_visible_area[2] + self.diagram_tab.canvas_visible_area[2] % grid_size
        y     = self.diagram_tab.canvas_visible_area[1] - self.diagram_tab.canvas_visible_area[1] % grid_size
        y_max = self.diagram_tab.canvas_visible_area[3] + self.diagram_tab.canvas_visible_area[3] % grid_size
        while y<y_max:
            canvas_id_of_line = self.canvas.create_line(x_min, y, x_max, y, dash=(1,1), fill="gray85", tags=("grid_line", "layer5"))
            self.canvas.tag_raise("schematic-element", canvas_id_of_line)
            y += grid_size

    def __draw_vertical_grid(self, grid_size):
        x     = self.diagram_tab.canvas_visible_area[0] - self.diagram_tab.canvas_visible_area[0] % grid_size
        x_max = self.diagram_tab.canvas_visible_area[2] + self.diagram_tab.canvas_visible_area[2] % grid_size
        y_min = self.diagram_tab.canvas_visible_area[1] - self.diagram_tab.canvas_visible_area[1] % grid_size
        y_max = self.diagram_tab.canvas_visible_area[3] + self.diagram_tab.canvas_visible_area[3] % grid_size
        while x<x_max:
            canvas_id_of_line = self.canvas.create_line(x, y_min, x, y_max, dash=(1,1), fill="gray85", tags=("grid_line", "layer5"))
            self.canvas.tag_raise("schematic-element", canvas_id_of_line)
            x += grid_size
