"""
"""
from tkinter import messagebox

class FindReplace:
    search_is_running = False
    def __init__(self, window, search_string_var, replace_string_var, replace=False):
        if FindReplace.search_is_running:
            return
        FindReplace.search_is_running = True
        number_of_matches = 0
        search_string = search_string_var.get().lower()
        replace_string = replace_string_var.get()
        # The 4 find_string methods use:
        # diagram_tab.find_string   : "find" uses <string>.find(), "replace" uses re.findall()/re.sub()
        # interface_tab.find_string : "find" uses textwidget.search(), "replace" uses textwidget.search()
        # internals_tab.find_string : "find" uses textwidget.search(), "replace" uses textwidget.search()
        # hdl_tab.find_string       : "find" uses textwidget.search()
        # So only in diagram_tab at "replace" regular expressions would work.
        # In order to handle the search_string and the new_string identical in all find_string methods,
        # both strings are "escaped" in diagram_tab "replace".
        if search_string!="":
            # number_of_hits==-1 then a search was aborted; number_of_hits==0 means no hits at search or replace, number of hits>0 means number of replacements.
            number_of_hits = window.notebook_top.diagram_tab.find_string(search_string, replace, replace_string)
            if number_of_hits!=-1:
                number_of_matches += number_of_hits
                number_of_hits = window.notebook_top.interface_tab.find_string(search_string, replace, replace_string)
                if number_of_hits!=-1:
                    number_of_matches += number_of_hits
                    number_of_hits = window.notebook_top.internals_tab.find_string(search_string, replace, replace_string)
                    if number_of_hits!=-1:
                        number_of_matches += number_of_hits
                        if not replace:
                            number_of_hits = window.notebook_top.hdl_tab.find_string(search_string)
                            if number_of_hits!=-1:
                                number_of_matches += number_of_hits
        FindReplace.search_is_running = False
        if number_of_hits!=-1:
            if replace:
                messagebox.showinfo("HDL_SCHEM-Editor", "Number of replacements = " + str(number_of_matches))
            else:
                messagebox.showinfo("HDL_SCHEM-Editor", "Number of hits = " + str(number_of_matches))
