"""
"""
from tkinter import messagebox
import file_write
import schematic_window

class FindReplace:
    search_is_running = False
    def __init__(self, window, search_string, replace_string, search_replace_hier, replace=False):
        if FindReplace.search_is_running:
            return
        FindReplace.search_is_running = True
        number_of_all_hits = 0
        if search_replace_hier:
            window_list = schematic_window.SchematicWindow.open_window_dict
        else:
            window_list = [window]
        for open_window in window_list:
            number_of_hits = self._search_and_replace(window, search_string, replace_string, replace)
            if number_of_hits == -1:
                FindReplace.search_is_running = False
                return
            if replace and search_replace_hier and number_of_hits!=0:
                file_write.FileWrite(open_window, open_window.design, "save")
            number_of_all_hits += number_of_hits
        if replace:
            action = "replacements"
        else:
            action = "hits"
        messagebox.showinfo("HDL_SCHEM-Editor", "Number of " + action + " = " + str(number_of_all_hits))
        FindReplace.search_is_running = False

    def _search_and_replace(self, window, search_string, replace_string, replace) -> int:
        # The 4 find_string methods use:
        # diagram_tab.find_string   : "find" uses <string>.find(), "replace" uses re.findall()/re.sub()
        # interface_tab.find_string : "find" uses textwidget.search(), "replace" uses textwidget.search()
        # internals_tab.find_string : "find" uses textwidget.search(), "replace" uses textwidget.search()
        # hdl_tab.find_string       : "find" uses textwidget.search()
        # So only in diagram_tab at "replace" regular expressions would work.
        # In order to handle the search_string and the new_string identical in all find_string methods,
        # both strings are "escaped" in diagram_tab "replace".
        number_of_local_hits = 0
        if search_string!="":
            # number_of_hits==-1 then a search was aborted; number_of_hits==0 means no hits at search or replace, number of hits>0 means number of replacements.
            number_of_hits = window.notebook_top.diagram_tab.find_string(search_string, replace, replace_string)
            if number_of_hits==-1:
                return -1
            number_of_local_hits += number_of_hits
            number_of_hits = window.notebook_top.interface_tab.find_string(search_string, replace, replace_string)
            if number_of_hits==-1:
                return -1
            number_of_local_hits += number_of_hits
            number_of_hits = window.notebook_top.internals_tab.find_string(search_string, replace, replace_string)
            if number_of_hits==-1:
                return -1
            number_of_local_hits += number_of_hits
            number_of_hits = window.notebook_top.control_tab.find_string(search_string, replace, replace_string)
            if number_of_hits==-1:
                return -1
            number_of_local_hits += number_of_hits
            if not replace:
                number_of_hits = window.notebook_top.hdl_tab.find_string(search_string)
                if number_of_hits==-1:
                    return -1
                number_of_local_hits += number_of_hits
        return number_of_local_hits
