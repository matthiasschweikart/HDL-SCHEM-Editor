"""
This class converts a VHDL file into a HDL-SCHEM-Editor design.
Any already entered information will be removed by the conversion.
"Entity Declarations" will be filled ("Packages" and "Generics").
"Architecture Declarations" will be filled ("Packages" and "Architecture First declarations").
Ports will be created as wires with connector.
The complete architecture body will be copied into a block.
"""
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename
from tkinter import messagebox
import re

import vhdl_parsing
import file_write

class ConvertVhdl():
    def __init__(self, window):
        hdl_file_name = askopenfilename(filetypes=(("VHDL files","*.vhd"),("all files","*.*")),
                                        title="Select HDL file to convert:")
        if hdl_file_name!="":
            hdl_file_content = self.__read_hdl_file(hdl_file_name)
            if hdl_file_content!="":
                hdl_parsed        = vhdl_parsing.VhdlParser(hdl_file_content, "entity_context")
                design_dictionary = self.__create_design_dictionary(window, hdl_parsed)
                filename          = self.__provide_empty_project_file(design_dictionary["module_name"])
                self.__fill_project_file(window, filename, design_dictionary)

    def __read_hdl_file(self, hdl_file_name):
        try:
            fileobject = open(hdl_file_name, 'r', encoding="utf-8")
            hdl_file_content = fileobject.read()
            fileobject.close()
        except Exception:
            hdl_file_content = ""
            messagebox.showerror("Error in HDL-SCHEM-Editor Convert", "File " + hdl_file_name + " could not be opened.")
        return hdl_file_content

    def __create_design_dictionary(self, window, hdl_parsed):
        design_dictionary = self.__initialize_design_dictionary(window)
        self.__fill_dictionary_with_module_and_architecture_name(design_dictionary, hdl_parsed)
        self.__fill_dictionary_with_entity_packages             (design_dictionary, hdl_parsed)
        self.__fill_dictionary_with_entity_generics             (design_dictionary, hdl_parsed)
        self.__fill_dictionary_with_architecture_declarations   (design_dictionary, hdl_parsed)
        self.__fill_dictionary_with_schematic_elements          (design_dictionary, hdl_parsed)
        return design_dictionary

    def __provide_empty_project_file(self, module_name): # Its time-stamp is used to prevent update_schematic_window_from from copying HDL into HDL-tab.
        filename = asksaveasfilename(defaultextension=".hse",
                                     initialfile = module_name,
                                     filetypes=(("HDL-Schem-Editor files","*.hse"),("all files","*.*")),
                                     title="Where shall the new project file be stored?")
        try:
            fileobject = open(filename, 'w', encoding="utf-8")
            fileobject.write("")
            fileobject.close()
            return filename
        except Exception:
            messagebox.showerror("Error in HDL-SCHEM-Editor Convert", "File " + filename + " could not be opened.")
            return ""

    def __fill_project_file(self, window, filename, design_dictionary):
        if filename!="":
            window.design.set_path_name(filename)
            window.design.clear_stack()
            window.update_schematic_window_from(design_dictionary, fill_link_dictionary=False) # By empty project file it is decided that no HDL must be copied into HDL tab.
            window.notebook_top.diagram_tab.canvas.focus()
            window.__class__.open_window_dict[window] = filename
            file_write.FileWrite(window, window.design, "save")

    def __initialize_design_dictionary(self, window):
        design_dictionary = {}
        design_dictionary["architecture_list"    ] = []
        design_dictionary["port_declarations"    ] = ""
        design_dictionary["generate_path_value"  ] = ""
        design_dictionary["language"             ] = "VHDL"
        design_dictionary["number_of_files"      ] = 1
        design_dictionary["edit_cmd"             ] = window.notebook_top.control_tab.edit_cmd.get()
        design_dictionary["hfe_cmd"              ] = window.notebook_top.control_tab.hfe_cmd.get()
        design_dictionary["module_library"       ] = ""
        design_dictionary["additional_sources"   ] = []
        design_dictionary["working_directory"    ] = ""
        design_dictionary["compile_cmd"          ] = window.notebook_top.control_tab.vhdl_compile_cmd1
        design_dictionary["compile_hierarchy_cmd"] = window.notebook_top.control_tab.vhdl_compile_hierarchy
        design_dictionary["signal_name_font"     ] = "Courier"
        design_dictionary["font_size"            ] = 10
        design_dictionary["grid_size"            ] = 2 * design_dictionary["font_size"]
        design_dictionary["connector_size"       ] = 3 * design_dictionary["font_size"]
        design_dictionary["visible_center_point" ] = [0, 0]
        design_dictionary["block_id"             ] = 0
        design_dictionary["generate_frame_id"    ] = 0
        design_dictionary["instance_id"          ] = 0
        design_dictionary["text_dictionary"      ] = {"interface_packages"             : "",
                                                        "interface_generics"             : "",
                                                        "internals_packages"             : "",
                                                        "architecture_first_declarations": "",
                                                        "architecture_last_declarations" : ""}
        return design_dictionary

    def __fill_dictionary_with_module_and_architecture_name(self, design_dictionary, hdl_parsed):
        module_name       = hdl_parsed.get("entity_name")
        architecture_name = hdl_parsed.get("architecture_name")
        design_dictionary["module_name"      ] = module_name
        design_dictionary["architecture_name"] = architecture_name

    def __fill_dictionary_with_entity_packages(self, design_dictionary, hdl_parsed):
        entity_library_names       = hdl_parsed.get("entity_library_name")
        entity_package_names       = hdl_parsed.get("entity_package_name")
        for entity_library_name in entity_library_names:
            design_dictionary["text_dictionary"]["interface_packages"] += "library " + entity_library_name + ";\n"
        for entity_package_name in entity_package_names:
            design_dictionary["text_dictionary"]["interface_packages"] += "use " + entity_package_name + ".all;\n"

    def __fill_dictionary_with_entity_generics(self, design_dictionary, hdl_parsed):
        generics_interface_names       = hdl_parsed.get("generics_interface_names")
        generics_interface_types       = hdl_parsed.get("generics_interface_types")
        generics_interface_ranges      = hdl_parsed.get("generics_interface_ranges")
        generics_interface_init        = hdl_parsed.get("generics_interface_init")
        generics_interface_init_range  = hdl_parsed.get("generics_interface_init_range")
        if generics_interface_init!="":
            init_assign = " := "
        else:
            init_assign = ""
        index = 0 # Default-value for a design without any ports
        for index, generic_interface_name in enumerate(generics_interface_names):
            design_dictionary["text_dictionary"]["interface_generics"] += (generic_interface_name.strip() + " : "       +
                                                                           generics_interface_types     [index].strip() +
                                                                           generics_interface_ranges    [index].strip() + init_assign +
                                                                           generics_interface_init      [index].strip() +
                                                                           generics_interface_init_range[index].strip() + ";\n")
        return

    def __fill_dictionary_with_architecture_declarations(self, design_dictionary, hdl_parsed):
        architecture_library_names = hdl_parsed.get("architecture_library_name")
        architecture_package_names = hdl_parsed.get("architecture_package_name")
        for architecture_library_name in architecture_library_names:
            design_dictionary["text_dictionary"]["internals_packages"] += "library " + architecture_library_name + ";\n"
        for architecture_package_name in architecture_package_names:
            design_dictionary["text_dictionary"]["internals_packages"] += "use " + architecture_package_name + ".all;\n"
        architecture_declarations  = hdl_parsed.get_architecture_declarations()
        design_dictionary["text_dictionary"]["architecture_first_declarations"] = architecture_declarations

    def __fill_dictionary_with_schematic_elements(self, design_dictionary, hdl_parsed):
        design_dictionary["canvas_dictionary"] = {}
        canvas_dict_key, index = self.__fill_canvas_dictionary_with_ports(design_dictionary, hdl_parsed)
        self.__fill_canvas_dictionary_with_block(design_dictionary, hdl_parsed, canvas_dict_key, index)
        return design_dictionary

    def __fill_canvas_dictionary_with_ports(self, design_dictionary, hdl_parsed):
        port_interface_names       = hdl_parsed.get("port_interface_names")
        port_interface_direction   = hdl_parsed.get("port_interface_direction")
        port_interface_types       = hdl_parsed.get("port_interface_types")
        port_interface_ranges      = hdl_parsed.get("port_interface_ranges")
        port_interface_init        = hdl_parsed.get("port_interface_init")
        port_interface_init_range  = hdl_parsed.get("port_interface_init_range")
        # print(port_interface_names)
        # print(port_interface_direction   )
        # print(port_interface_types       )
        # print(port_interface_ranges      )
        # print(port_interface_init        )
        # print(port_interface_init_range  )
        canvas_dict_key   = 0
        index = 0 # Default-value for a design without any ports
        for index, port_interface_name in enumerate(port_interface_names):
            wire_length = 20*design_dictionary["grid_size"]
            if port_interface_direction[index]=="in":
                connector_type = "input"
                connector_x_coord = 0
            elif port_interface_direction[index]=="out":
                connector_type = "output"
                connector_x_coord = wire_length
            else:
                connector_type = "inout"
                connector_x_coord = wire_length
            port_interface_ranges    [index] = re.sub(r"\n" , " ", port_interface_ranges    [index]) # range may be separated into several lines.
            port_interface_ranges    [index] = re.sub(r"\s+", " ", port_interface_ranges    [index]) # Convert multiple blanks into one blank.
            port_interface_init      [index] = re.sub(r"\n" , " ", port_interface_init      [index]) # init may be separated into several lines.
            port_interface_init      [index] = re.sub(r"\s+", " ", port_interface_init      [index]) # Convert multiple blanks into one blank.
            port_interface_init_range[index] = re.sub(r"\n" , " ", port_interface_init_range[index]) # range may be separated into several lines.
            port_interface_init_range[index] = re.sub(r"\s+", " ", port_interface_init_range[index]) # Convert multiple blanks into one blank.
            if port_interface_ranges[index]!="":
                size = "3.0"
            else:
                size = "1.0"
            design_dictionary["canvas_dictionary"][canvas_dict_key] = ["empty", connector_type, [connector_x_coord, index*design_dictionary["grid_size"]], 0]
            canvas_dict_key += 1
            design_dictionary["canvas_dictionary"][canvas_dict_key] = ["empty", "signal-name" , [0, index*design_dictionary["grid_size"]], 0,
                                                                       port_interface_name + " : "      +
                                                                       port_interface_types     [index] + " " +
                                                                       port_interface_ranges    [index] +
                                                                       port_interface_init      [index] +
                                                                       port_interface_init_range[index],
                                                                       "wire_" + str(index)]
            canvas_dict_key += 1
            design_dictionary["canvas_dictionary"][canvas_dict_key] = ["empty", "wire" , [0,index*design_dictionary["grid_size"],wire_length,index*design_dictionary["grid_size"]],
                                                                       ["wire_" + str(index), "layer2", "schematic-element"], "none", size]
            canvas_dict_key += 1
        index += 1 # Increment in order to place the next schematic element at an empty place.
        design_dictionary["wire_id"] = len(port_interface_names)
        return canvas_dict_key, index

    def __fill_canvas_dictionary_with_block(self, design_dictionary, hdl_parsed, canvas_dict_key, index):
        architecture_body = hdl_parsed.get_architecture_body()
        number_of_lines = architecture_body.count("\n")
        design_dictionary["canvas_dictionary"][canvas_dict_key] = ["empty", "block", [0, index*design_dictionary["grid_size"],
                                                                                      1000, (number_of_lines+index)*design_dictionary["grid_size"]],
                                                                        [10, index*design_dictionary["grid_size"] + 10],
                                                                        architecture_body, "block_0", "lemon chiffon"]
        design_dictionary["block_id"] = 1
