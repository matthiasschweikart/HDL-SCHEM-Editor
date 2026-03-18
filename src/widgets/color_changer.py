"""
This class lets the user configure a color.
"""

from tkinter import colorchooser


class ColorChanger:
    """This class is used for changing the color of an element. It opens a color chooser dialog."""

    def __init__(self, default_color, window):
        self.new_color = colorchooser.askcolor(default_color, parent=window)[1]

    def get_new_color(self):
        """Returns the new color. If the user has pressed "abort", the new color is None."""
        return self.new_color

    # def __del__(self):
    #     print("ColorChooser Object deleted.")
