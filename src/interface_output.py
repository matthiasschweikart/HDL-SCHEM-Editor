""" Handles all stuff for inserting an output connector into the canvas"""
import interface_insertion

class Output(interface_insertion.InterfaceInsertion):
    # There is a "dummy" entry to keep the number of parameters of Output() identical to the number of parameters of InterfaceInsertion().
    def __init__(self, schematic_window, diagram_tab, dummy, follow_mouse, # push_design_to_stack=True,
                 location=(0,0), orientation=0):
        anchor             = [   0,     0]
        point_corner2      = [   0, +1/30]
        base_corner2       = [+1/6, +1/30]
        lower_left_corner  = [+1/6, +1/6 ]
        lower_right_corner = [+5/6, +1/6 ]
        right_corner       = [+3/3,     0]
        upper_right_corner = [+5/6, -1/6 ]
        upper_left_corner  = [+1/6, -1/6 ]
        base_corner1       = [+1/6, -1/30]
        point_corner1      = [   0, -1/30]
        points = [anchor,    # Must be the first point in the list.
                       point_corner2, base_corner2,
                       lower_left_corner , lower_right_corner,
                       right_corner,
                       upper_right_corner, upper_left_corner ,
                       base_corner1, point_corner1
                       ]
        for point_index, point in enumerate(points):
            for coord_index, _ in enumerate(point):
                points[point_index][coord_index] = points[point_index][coord_index] * schematic_window.design.get_connector_size()
        interface_insertion.InterfaceInsertion.__init__(self, schematic_window, diagram_tab, points, follow_mouse)
        self.type = "output"
        # Dieser Aufruf für das Einsetzen per File-Read, Undo, Paste sollte besser in InterfaceInsertion stehen.
        # Er steht hier, weil beim Einsetzen per Maus nur points aber nicht location und orientation übergeben werden müssen.
        # Dies macht vor allem deshalb Probleme, weil der Constructor hier und der Constructor in InterfaceInsertion die gleichen Parameter haben müssen.
        # Dieses Problem ist bei GenerateFrame besser gelöst, weil dort alle Daten in einem einzigen Dictionary übergeben werden.
        # Dieser Dictionary ist dann je nach Einsetz-Methode mehr oder weniger gefüllt.
        if not follow_mouse:
            self.draw_at_location(location, orientation, points)
