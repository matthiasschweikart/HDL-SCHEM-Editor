"""
This class lets the user configure a color.
"""
from tkinter import colorchooser

class ColorChanger():
    def __init__(self, default_color, window):
        self.new_color = colorchooser.askcolor(default_color, parent=window)[1]
    def get_new_color(self):
        return self.new_color
    # def __del__(self):
    #     print("ColorChooser Object deleted.")
