"""
    The LinkDictionary shall carry all information which are needed to create hyperlinks from each line in the generated HDL
    to the graphical source of the line.
    The LinkDictionary is created once, when the HDL-SCHEM-Editor is started.
    All accesses to the LinkDictionary are done by using the class variable link_dict_reference.
    The LinkDictionary is filled when the HDL is generated and at some other events.
    At HDL generation only the needed information is gathered and send to the LinkDictionary.
    The LinkDictionary must then build up the dictionary which afterwards will be used by the HDL tab.
    The HDL tab observes the mouse movements and at a left mouse button press at a line a method of the
    LinkDictionary is called, which shows the graphical source of this HLD code line.

    When the LinkDictionary is filled by the HDL generation, a HDL-file-name and a HDL-file-line-number must be handed over.
    These 2 parameters are the keys of the LinkDictionary, so when the user clicks on a line in a HDL file in the HDL-tab,
    line-number and file-name are determined and the corresponding entry of the LinkDictionary can be read.
"""
class LinkDictionary():
    link_dict_reference = None
    def __init__(self, root):
        self.root = root
        LinkDictionary.link_dict_reference = self
        self.link_dict = {}
    def add(self,
            window,           # Window for which the HDL-item is generated
            file_name,        # Filename in which the HDL-item is stored
            file_line_number, # File-line-number in which the HDL-item is stored
            hdl_item_type,    # One of "interface_packages", "interface_generics", ..., "port_connection"
            number_of_lines,  # How many lines does the HDL-item use in the file
            hdl_item_name,    # Name of the HDL-item: "", port-name at port_declar., instance-name at embedded_library_instruct.,signal_name at signal_decl., canvas_id at inst.
            number_of_line    # Carrys the number of the line in a block or a generic-map. When hdl_item_type=="port_connection" then it carries a signal name.
            ):
        #print("add =", file_name, file_line_number, hdl_item_type, number_of_lines , hdl_item_name, number_of_line)
        if file_name not in self.link_dict:
            self.link_dict[file_name] = {}
            self.link_dict[file_name]["window"] = window
            self.link_dict[file_name]["lines" ] = {}
        if hdl_item_type=="entity":
            self.link_dict[file_name]["lines"][file_line_number]     = {"tab_name"         : "Control",
                                                                        "widget_reference" : window.notebook_top.control_tab,
                                                                        "hdl_item_type"    : "",
                                                                        "object_identifier": "",
                                                                        "number_of_line"   : ""}
            file_line_number += 1
        elif hdl_item_type=="interface_packages":
            for text_line_number in range(1, number_of_lines+1):
                self.link_dict[file_name]["lines"][file_line_number] = {"tab_name"         : "Entity Declarations",
                                                                        "widget_reference" : window.notebook_top.interface_tab.interface_packages_text,
                                                                        "hdl_item_type"    : "",
                                                                        "object_identifier": "",
                                                                        "number_of_line"   : text_line_number}
                file_line_number += 1
        elif hdl_item_type=="interface_generics":
            for text_line_number in range(1, number_of_lines+1):
                self.link_dict[file_name]["lines"][file_line_number] = {"tab_name"         : "Entity Declarations",
                                                                        "widget_reference" : window.notebook_top.interface_tab.interface_generics_text,
                                                                        "hdl_item_type"    : "",
                                                                        "object_identifier": "",
                                                                        "number_of_line"   : text_line_number}
                file_line_number += 1
        elif hdl_item_type=="internals_packages":
            for text_line_number in range(1, number_of_lines+1):
                self.link_dict[file_name]["lines"][file_line_number] = {"tab_name"         : "Architecture Declarations",
                                                                        "widget_reference" : window.notebook_top.internals_tab.internals_packages_text,
                                                                        "hdl_item_type"    : "",
                                                                        "object_identifier": "",
                                                                        "number_of_line"   : text_line_number}
                file_line_number += 1
        elif hdl_item_type=="first_declarations":
            if window.design.get_language()=="VHDL":
                tab_name = "Architecture Declarations"
            else:
                tab_name = "Internal Declarations"
            for text_line_number in range(1, number_of_lines+1):
                self.link_dict[file_name]["lines"][file_line_number] = {"tab_name"         : tab_name,
                                                                        "widget_reference" : window.notebook_top.internals_tab.architecture_first_declarations_text,
                                                                        "hdl_item_type"    : "",
                                                                        "object_identifier": "",
                                                                        "number_of_line"   : text_line_number}
                file_line_number += 1
        elif hdl_item_type=="last_declarations":
            for text_line_number in range(1, number_of_lines+1):
                self.link_dict[file_name]["lines"][file_line_number] = {"tab_name"         : "Architecture Declarations",
                                                                        "widget_reference" : window.notebook_top.internals_tab.architecture_last_declarations_text,
                                                                        "hdl_item_type"    : "",
                                                                        "object_identifier": "",
                                                                        "number_of_line"   : text_line_number}
                file_line_number += 1
        elif hdl_item_type=="port_declaration":
            self.link_dict[file_name]["lines"][file_line_number]     = {"tab_name"         : "Diagram",
                                                                        "widget_reference" : window.notebook_top.diagram_tab,
                                                                        "hdl_item_type"    : "port_declaration",
                                                                        "object_identifier": hdl_item_name, # port name
                                                                        "number_of_line"   : ""}
        elif hdl_item_type=="embedded_library_instruction":
            self.link_dict[file_name]["lines"][file_line_number]     = {"tab_name"         : "Diagram",
                                                                        "widget_reference" : window.notebook_top.diagram_tab,
                                                                        "hdl_item_type"    : "embedded_library_instruction",
                                                                        "object_identifier": hdl_item_name, # instance name
                                                                        "number_of_line"   : ""}
        elif hdl_item_type=="signal_declaration":
            self.link_dict[file_name]["lines"][file_line_number]     = {"tab_name"         : "Diagram",
                                                                        "widget_reference" : window.notebook_top.diagram_tab,
                                                                        "hdl_item_type"    : "signal_declaration",
                                                                        "object_identifier": hdl_item_name, # signal name
                                                                        "number_of_line"   : ""}
        elif hdl_item_type=="generate":
            self.link_dict[file_name]["lines"][file_line_number]     = {"tab_name"         : "Diagram",
                                                                        "widget_reference" : window.notebook_top.diagram_tab,
                                                                        "hdl_item_type"    : "generate",
                                                                        "object_identifier": hdl_item_name, # canvas_id of generate-rectangle
                                                                        "number_of_line"   : ""}
        elif hdl_item_type=="block":
            self.link_dict[file_name]["lines"][file_line_number]     = {"tab_name"         : "Diagram",
                                                                        "widget_reference" : window.notebook_top.diagram_tab,
                                                                        "hdl_item_type"    : "block",
                                                                        "object_identifier": hdl_item_name, # canvas_id of block-canvas-item
                                                                        "number_of_line"   : number_of_line}
        elif hdl_item_type=="instance_name":
            self.link_dict[file_name]["lines"][file_line_number]     = {"tab_name"         : "Diagram",
                                                                        "widget_reference" : window.notebook_top.diagram_tab,
                                                                        "hdl_item_type"    : "instance_name",
                                                                        "object_identifier": hdl_item_name, # canvas_id of symbol
                                                                        "number_of_line"   : ""}
        elif hdl_item_type=="generic_mapping":
            self.link_dict[file_name]["lines"][file_line_number]     = {"tab_name"         : "Diagram",
                                                                        "widget_reference" : window.notebook_top.diagram_tab,
                                                                        "hdl_item_type"    : "generic_mapping",
                                                                        "object_identifier": hdl_item_name, # canvas_id of symbol
                                                                        "number_of_line"   : number_of_line}
        elif hdl_item_type=="port_connection":
            self.link_dict[file_name]["lines"][file_line_number]     = {"tab_name"         : "Diagram",
                                                                        "widget_reference" : window.notebook_top.diagram_tab,
                                                                        "hdl_item_type"    : "port_connection",
                                                                        "object_identifier": hdl_item_name,  # canvas_id of symbol
                                                                        "number_of_line"   : number_of_line} # name of the connected signal

    def jump_to_source(self, selected_file, file_line_number): # Used in the "Generated HDL"-Tab and in the "Messages"-Tab.
        window_to_lift    = self.link_dict[selected_file]["window"]
        tab_to_show       = self.link_dict[selected_file]["lines"][file_line_number]["tab_name"]
        widget            = self.link_dict[selected_file]["lines"][file_line_number]["widget_reference"]
        hdl_item_type     = self.link_dict[selected_file]["lines"][file_line_number]["hdl_item_type"]
        object_identifier = self.link_dict[selected_file]["lines"][file_line_number]["object_identifier"]
        number_of_line    = self.link_dict[selected_file]["lines"][file_line_number]["number_of_line"]
        window_to_lift.open_this_window()
        window_to_lift.update_idletasks()
        window_to_lift.notebook_top.show_tab(tab_to_show)
        widget.highlight_item(hdl_item_type, object_identifier, number_of_line)

    def jump_to_hdl(self, selected_file, file_line_number): # Used only in the Messages-Tab.
        window_to_lift    = self.link_dict[selected_file]["window"]
        if window_to_lift.design.get_number_of_files()==2:
            _, file_name_architecture = window_to_lift.design.get_file_names()
            if selected_file==file_name_architecture:
                file_line_number += window_to_lift.notebook_top.hdl_tab.last_line_number_of_file1
        window_to_lift.open_this_window()
        window_to_lift.update_idletasks()
        window_to_lift.notebook_top.show_tab("generated HDL")
        window_to_lift.notebook_top.hdl_tab.hdl_frame_text.highlight_item("", "", file_line_number)

    def clear_link_dict(self, file_name):
        # The link_dict is filled when a module-file is read and a HDL-file was found which is newer than the module-file.
        # The link_dict is filled when the HDL for a module is generated.
        # The link_dict is filled when a different VHDL architecture is selected for a sub-module.
        #print("clear_link_dict from ", file_name)
        if file_name in self.link_dict:
            self.link_dict.pop(file_name)
