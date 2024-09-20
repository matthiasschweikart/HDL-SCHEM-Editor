"""
Update the generics of a instance.
"""

class SymbolUpdateGenerics():
    def __init__(self, root, window, diagram_tab, symbol, symbol_define_ref):
        self.root        = root
        self.window      = window
        self.diagram_tab = diagram_tab
        instance_updated = symbol_define_ref.get_instance()
        if instance_updated is None:
            return
        symbol_definition_upd = self.__create_new_symbol_definition_from_source_file(instance_updated)
        generic_map_new       = self.__get_generic_map_from_new_symbol_definition(symbol_definition_upd)
        # The order of the entries in the dictionary is important, as only the second one calls store_item():
        symbol.update({"library"            : symbol_definition_upd["configuration"]["library"],
                       "entity_name"        : symbol_definition_upd["entity_name"]["name"],
                       "generate_path_value": symbol_definition_upd["generate_path_value"],
                       "generic_definition" : symbol_definition_upd["generic_definition"],
                       "generic_block"      : generic_map_new})

    def __create_new_symbol_definition_from_source_file(self, instance_updated):
        symbol_definition_upd = instance_updated.get_symbol_definition_for_update() # From a symbol which is calculated by symbol_insertion.Instance at x=0, y=0
        return symbol_definition_upd

    def __get_generic_map_from_new_symbol_definition(self, symbol_definition_upd):
        return symbol_definition_upd["generic_block"]["generic_map"]
