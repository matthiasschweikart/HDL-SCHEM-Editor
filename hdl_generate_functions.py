"""
Support class
"""
from tkinter import messagebox
import re
import os
import symbol_instance


class HdlGenerateFunctions():

    @classmethod
    def indent_identically(cls, character, old_list):
        old_list = [re.sub("[ ]*" + character, character, decl, count=1) for decl in old_list] # Blanks for the character will be adapted und must first be removed here.
        max_index = 0
        new_list = []
        for port_declaration in old_list:
            index = port_declaration.find(character)
            if index>max_index:
                max_index = index
        for port_declaration in old_list:
            index = port_declaration.find(character)
            fill = " "*(max_index-index+1) + character
            new_list.append(re.sub(character, fill, port_declaration, count=1))
        return new_list

    @classmethod
    def split_declaration(cls, signal_declaration, language):
        if language=="VHDL":
            # Examples of VHDL signal declarations at a wire:
            # signal-name                : std_logic_vector(7 downto 0) := X"77" -- complete range is used
            # signal-name(7 downto 4)    : std_logic_vector(7 downto 0) := X"77" -- only range 7:4 is used at the wire
            # signal-name(1 downto 0)    : t_std_logic_8_array(3 downto 0) := (X"77", X"66", X"55", X"44") -- comment
            # signal-name(3)(1 downto 0) : t_std_logic_8_array(3 downto 0) := (X"77", X"66", X"55", X"44") -- comment
            # signal-name(3)(0)          : t_std_logic_8_array(3 downto 0) := (X"77", X"66", X"55", X"44") -- comment
            comment = re.sub(r".*--", "--", signal_declaration)
            if comment==signal_declaration:
                comment = ""
            else:
                signal_declaration = re.sub(r"\s*--.*", "", signal_declaration)
            initialization = re.sub(r".*:=", ":=", signal_declaration)
            if initialization==signal_declaration:
                initialization = ""
            signal_declaration = re.sub(r"\s*:=.*", "", signal_declaration) # Remove initialization
            signal_type        = re.sub(r".*:\s*" , "", signal_declaration) # Contains also the range of the type.
            signal_name        = re.sub(r"\s*:.*" , "", signal_declaration) # Remove type
            signal_name        = re.sub(r"\..*"   , "", signal_name       ) # Remove record slice (if present)
            if '(' in signal_name: # Then the declaration has a sub range
                bracket_open     = signal_name.find ('(')
                bracket_close    = signal_name.rfind(')') # The range could be a multidimensional range.
                signal_sub_range = signal_name[bracket_open:bracket_close+1]
                signal_sub_range = re.sub(r"\s+", " ", signal_sub_range)
                signal_name      = signal_name[:bracket_open]
            else:
                signal_sub_range = ""
            if '.' in signal_declaration: # Then the signal is a slice of a record
                signal_record_slice = re.sub(r".*\."   , ".", signal_declaration)  # remove all characters until the '.' is reached.
                signal_record_slice = re.sub(r"\s*:.*" , "" , signal_record_slice) # remove all characters after the slice.
            else:
                signal_record_slice = ""
            signal_name = signal_name.strip()
        else:
            # Examples of Verilog signal declarations at a wire:
            # reg/wire/logic [7:0] signal-name                 // The complete range is used at the wire (visible at the wire: signal-name[7:0]).
            # reg/wire/logic       signal-name[7:0]            // This is an array (visible at the wire: signal-name[7:0]).
            # reg/wire/logic [7:0] signal-name : [7:4]         // The wire uses only subrange 7:4 of the complete range 7:0 (visible at the wire: signal-name[7:4]).
            # reg/wire/logic [7:0] signal-name[3:0]            // This is an array with 4 values, where each value has 8 bits (visible at the wire: signal-name[3:0]).
            # reg/wire/logic [7:0] signal-name[3:0] : [1:0]    // Only the values 1:0 of the 4 values of 8 bits are used at the wire (visible at the wire: signal-name[1:0]).
            # reg/wire/logic [7:0] signal-name[3:0] : [3][1:0] // Only the values 1:0 of the 4 values of 8 bits are used (visible at the wire: signal-name[3][1:0]).
            # reg/wire/logic [7:0] signal-name[3:0] : [3][7]   // Only the values 1:0 of the 4 values of 8 bits are used (visible at the wire: signal-name[3][7]).
            # reg/wire/logic [7:0] signal-name[3:0] : [3][7:0] // Only the values 1:0 of the 4 values of 8 bits are used (visible at the wire: signal-name[3][7:0]).
            # reg/wire/logic signed   [7:0] signal-name[3:0] : [3][7:0]
            # reg/wire/logic unsigned [7:0] signal-name[3:0] : [3][7:0]
            signal_declaration = signal_declaration.strip() # remove trailing whitespace
            comment = re.sub(r".*//", "//", signal_declaration)
            if comment==signal_declaration:
                comment = ""
            else:
                signal_declaration = re.sub(r"\s*//.*", "", signal_declaration) # Remove comment from signal_declaration.
            initialization = "" # Verilog does not support initialization at declaration (only in initial blocks).
            signal_declaration = re.sub(r"\s*:\s*"        , ':'     , signal_declaration) # Remove blanks from ranges and from index-separator at the end of line.
            signal_declaration = re.sub(r"\[\s*"          , r"["    , signal_declaration) # Remove blanks from range-start.
            signal_declaration = re.sub(r"\s*\]"          , r"]"    , signal_declaration) # Remove blanks from range-end.
            signal_declaration = re.sub(r"\["             , r" ["   , signal_declaration) # Add blank at range begin.
            signal_declaration = re.sub(r"\]"             , r"] "   , signal_declaration) # Add blank at range end.
            signal_declaration = re.sub(r"(\[.*?):(.*?\])", r"\1|\2", signal_declaration) # Substitute ':' in all range descriptions to be able to search for another ':'
            if ':' in signal_declaration: # Then a subrange exists (this construct is not valid Verilog, but a extension here).
                signal_sub_range   = re.sub(r".*:"   , "" , signal_declaration) # Remove all but signal_sub_range.
                signal_sub_range   = re.sub(r"\|"    , ":", signal_sub_range  ) # Undo the replacement of ':' in signal_sub_range.
                signal_sub_range   = re.sub(r" "     , "" , signal_sub_range  ) # Remove blanks from signal_sub_range.
                signal_declaration = re.sub(r"\s*:.*", "" , signal_declaration) # Remove sub_range from signal_declaration.
            else:
                signal_sub_range = ""
            signal_declaration = re.sub(r"\|"   , ":", signal_declaration) # Undo the replacement of ':' in signal_declaration.
            signal_declaration_list = signal_declaration.split()
            signal_name = ""
            signal_type = ""
            in_signal_name = True
            for element in reversed(signal_declaration_list):
                if in_signal_name:
                    signal_name = element + signal_name
                    if not element.startswith('['):
                        in_signal_name = False
                else:
                    signal_type = element + ' ' + signal_type
            signal_record_slice = "" # Verilog has no record
        signal_type = signal_type.strip()
        signal_name = signal_name.strip()
        return signal_name, signal_sub_range, signal_type, comment, initialization, signal_record_slice

    @classmethod
    def extract_data_from_symbols(cls, symbol_definition_list):
        all_pins_definition_list    = [] # List of {"type": "entity-call", "coords": [x1, y1, ...], "instance_name": <string>, "port_declaration": <string>}
        component_declarations_dict = {}
        generic_mapping_dict        = {}
        embedded_configurations     = []
        libraries_from_instance_configuration = []
        for symbol_definition in symbol_definition_list:
            symbol_language        = symbol_instance.Symbol.get_language              (symbol_definition)
            entity_name            = symbol_instance.Symbol.get_entity_name           (symbol_definition) # Only needed for symbols with empty pin_definition_list.
            instance_name          = symbol_instance.Symbol.get_instance_name         (symbol_definition) # Only needed for symbols with empty pin_definition_list.
            insert_component       = True                                                                 # Only needed for symbols with empty pin_definition_list.
            generic_definition     = symbol_instance.Symbol.get_generic_definition    (symbol_definition)
            embedded_configuration = symbol_instance.Symbol.get_embedded_configuration(symbol_definition)
            embedded_configurations.append(embedded_configuration)
            generic_map            = symbol_instance.Symbol.get_generic_map           (symbol_definition)
            pin_definition_list    = symbol_instance.Symbol.get_pin_list              (symbol_definition)
            library_from_instance_configuration = symbol_instance.Symbol.get_library_from_instance_configuration(symbol_definition)
            if library_from_instance_configuration is not None:
                libraries_from_instance_configuration.append(library_from_instance_configuration)
            all_pins_definition_list += pin_definition_list
            # entry of pin_definition_list = {"type": <entity-call>, "instance_name": <instance-name>, "coords": [x1, y1], "port_declaration": <port-declaration}
            component_port_declarations = []
            for pin_definition in pin_definition_list:
                entity_name   = pin_definition["type"]          # This is a strange key name for an entity. But this name is needed, because
                instance_name = pin_definition["instance_name"] # pin_definition_list is combined with a second dictionary, which already has this key.
                if entity_name.startswith("entity "):
                    insert_component = False # No component declaration will be inserted into the architecture declaration region.
                else:
                    insert_component = True
                # In a VHDL declaration make "in" and "out" to have the same width of 3 characters:
                pin_definition["port_declaration"] = re.sub(" in ", " in  ", pin_definition["port_declaration"])
                component_port_declarations.append(pin_definition["port_declaration"])
            # Hier kann component_port_declarations sortiert werden:
            inputs  = []
            outputs = []
            inouts  = []
            for declaration in component_port_declarations:
                if symbol_language=="VHDL":
                    if   " in "  in declaration:
                        inputs.append(declaration)
                    elif " out " in declaration:
                        outputs.append(declaration)
                    else:
                        inouts.append(declaration)
                else: # Verilog
                    if   declaration.startswith("input "):
                        inputs.append(declaration)
                    elif declaration.startswith("output "):
                        outputs.append(declaration)
                    else:
                        inouts.append(declaration)
            if symbol_language=="VHDL":
                inputs  = sorted(inputs )
                outputs = sorted(outputs)
                inouts  = sorted(inouts )
            else:
                inputs  = sorted(inputs , key=lambda s: re.findall(r"\w+$", s)[0])
                outputs = sorted(outputs, key=lambda s: re.findall(r"\w+$", s)[0])
                inouts  = sorted(inouts , key=lambda s: re.findall(r"\w+$", s)[0])
            component_port_declarations_sorted = []
            component_port_declarations_sorted.extend(inputs)
            component_port_declarations_sorted.extend(outputs)
            component_port_declarations_sorted.extend(inouts)
            # The component_declarations_dict contains the component_port_declarations in the native language of the symbol:
            component_declarations_dict[entity_name] = [component_port_declarations_sorted, generic_definition, insert_component, symbol_language]
            generic_mapping_dict[instance_name] = {"entity_name": entity_name, "generic_map": generic_map, "canvas_id": symbol_instance.Symbol.get_canvas_id(symbol_definition)}
        embedded_configurations = HdlGenerateFunctions.indent_identically(':', embedded_configurations)
        return all_pins_definition_list, component_declarations_dict, embedded_configurations, generic_mapping_dict, libraries_from_instance_configuration

    @classmethod
    def hdl_must_be_generated(cls, path_name, hdlfilename, hdlfilename_architecture, show_message):
        if not os.path.isfile(path_name):
            _, name_of_file = os.path.split(path_name)
            if name_of_file.endswith(".hse"):
                messagebox.showerror("Error in HDL-SCHEM-Editor", "The HDL-SCHEM-Editor project file " + path_name + " is missing.")
            else:
                messagebox.showerror("Error in HDL-SCHEM-Editor", "The HDL-FSM-Editor project file "   + path_name + " is missing.")
            return True
        if not os.path.isfile(hdlfilename):
            if show_message:
                messagebox.showerror("Error in HDL-SCHEM-Editor", "The file "   + hdlfilename + " is missing.")
            return True
        if os.path.getmtime(hdlfilename)<os.path.getmtime(path_name):
            if show_message:
                messagebox.showerror("Error in HDL-SCHEM-Editor", "The file\n" + hdlfilename + "\nis older than\n" + path_name + "\nPlease generate HDL again.")
            return True
        if hdlfilename_architecture is not None:
            if not os.path.isfile(hdlfilename_architecture):
                if show_message:
                    messagebox.showerror("Error in HDL-SCHEM-Editor", "The architecture file "   + hdlfilename_architecture + " is missing.")
                return True
            if os.path.getmtime(hdlfilename_architecture)<os.path.getmtime(path_name):
                if show_message:
                    messagebox.showerror("Error in HDL-SCHEM-Editor", "The file\n" + hdlfilename_architecture + "\nis older than\n" + path_name + "\nPlease generate HDL again.")
                return True
        return False
