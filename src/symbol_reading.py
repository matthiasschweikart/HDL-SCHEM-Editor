"""
This class asks for the filename and tries to create an instance object.
If the instance could be created, its symbol is placed into the Canvas.

SymbolReading creates Symbol-Define: Symbol-Define creates SymbolInsertion-Object
                                     Symbol-Define fills Symbol-Insertion-Object
Symbol-Reading fetches reference to the Symbol-Insertion-Object.
Symbol-Reading calls draw-method of Symbol-Insertion-Object.
"""
from tkinter.filedialog import askopenfilename
import symbol_define

class SymbolReading():
    def __init__(self, root, window, diagram_tab):
        filename = askopenfilename(filetypes=(
            ("All files"           , "*.*"  ),
            ("VHDL files"          , "*.vhd"),
            ("Verilog files"       , "*.v"  ),
            ("System-Verilog files", "*.sv" ),
            ("HDL-Schematic-Editor", "*.hse"),
            ("HDL-FSM-Editor"      , "*.hfe")
            ))
        if filename!="": # When the user has pressed "abort", the filename is "".
            symbol_define_ref = symbol_define.SymbolDefine(root, window, diagram_tab, filename)
            symbol_insertion_ref = symbol_define_ref.get_symbol_insertion_ref()
            if symbol_insertion_ref is not None:
                symbol_insertion_ref.draw_symbol()
            diagram_tab.canvas.focus_set() # needed to make "Escape" working even before the symbol was ever moved during insertion.
