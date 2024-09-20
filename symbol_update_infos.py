"""
Update the generics of a instance.
"""

class SymbolUpdateInfos():
    def __init__(self, root, window, diagram_tab, symbol, symbol_define_ref, update_generics, update_by_reading_from_other_file):
        self.root        = root
        self.window      = window
        self.diagram_tab = diagram_tab
        instance_updated = symbol_define_ref.get_symbol_insertion_ref()
        if instance_updated is None:
            return
        symbol_definition_upd = self.__create_new_symbol_definition_from_source_file(instance_updated)
        generic_map_new       = self.__get_generic_map_from_new_symbol_definition(symbol_definition_upd)
        # When update_by_reading_from_other_file is True, then SymbolUpdateInfos starts a second call of symbol.update,
        # while the first call of symbol.update has not finished.
        # This second call shall not store the design, instead the first call shall store at its end.
        if update_generics:
            symbol.update({"entity_name"        : symbol_definition_upd["entity_name"]["name"],
                           "architecture_name"  : symbol_definition_upd["architecture_name"],
                           "architecture_list"  : symbol_definition_upd["architecture_list"],
                           "generate_path_value": symbol_definition_upd["generate_path_value"],
                           "generic_definition" : symbol_definition_upd["generic_definition"],
                           "generic_block"      : generic_map_new,
                           "additional_files"   : symbol_definition_upd["additional_files"],
                           "library"            : symbol_definition_upd["configuration"]["library"]
                           }, store_in_design_and_stack= not update_by_reading_from_other_file)
        else:
            symbol.update({"entity_name"        : symbol_definition_upd["entity_name"]["name"],
                           "architecture_name"  : symbol_definition_upd["architecture_name"],
                           "architecture_list"  : symbol_definition_upd["architecture_list"],
                           "generate_path_value": symbol_definition_upd["generate_path_value"],
                           "additional_files"   : symbol_definition_upd["additional_files"],
                           "library"            : symbol_definition_upd["configuration"]["library"]
                           }, store_in_design_and_stack= not update_by_reading_from_other_file)

    def __create_new_symbol_definition_from_source_file(self, instance_updated):
        symbol_definition_upd = instance_updated.get_symbol_definition_for_update() # From a symbol which is calculated by symbol_insertion.Instance at x=0, y=0
        return symbol_definition_upd

    def __get_generic_map_from_new_symbol_definition(self, symbol_definition_upd):
        return symbol_definition_upd["generic_block"]["generic_map"]
