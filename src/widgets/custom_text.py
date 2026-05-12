"""This class expands the tkinter Text-class"""

import concurrent.futures
import contextlib
import os
import re
import tkinter as tk

from actions import edit_ext
from codegen import hdl_generate_through_hierarchy
from data_io import file_read
from hdl_parser import vhdl_parsing

from .code_editor import CodeEditor


# Module-level function – must be a top-level def to be pickleable for ProcessPoolExecutor.
def _run_parser(parser_class, hdl, region, position_tags):
    parse_ref = parser_class(hdl, region)
    return {tag: parse_ref.get_positions(tag) for tag in position_tags}


class CustomText(CodeEditor):
    """This class expands the tkinter Text-class."""

    def __init__(
        self,
        *args,
        window,
        # identifier text_name for storing the text in the design_dictionary can have one of these values::
        # "block_edit","generated_hdl","interface_packages","interface_generics",
        # "internals_packages","architecture_first_declarations","architecture_last_declarations","log_text"
        text_name,
        parser: vhdl_parsing.VhdlParser,
        position_tags,
        store_in_design=True,  # store_in_design=False is only used by block_edit.py.
        has_line_numbers=False,
        **kwargs,
    ):
        self.window = window
        self.text_name = text_name
        self.text = ""
        self.store_in_design = store_in_design
        self.has_line_numbers = has_line_numbers
        self.parser_class = parser
        self.position_tags = position_tags
        self.after_identifier = None
        self.format_after_id = None
        super().__init__(*args, **kwargs)
        self.format_after_id = self.after(100, lambda: None)  # Dummy id for first key press
        self.tag_config("message_red", foreground="red")
        self.tag_config("message_green", foreground="green")
        if self.store_in_design:
            # Create an empty entry, so that after write into a file, at read an entry exists for all text objects.
            self.window.design.store_in_text_dictionary(self.text_name, "", signal_design_change=False)
        self.bind("<Control-e>", lambda event: self._edit_in_external_editor(self.window.design))
        # overwrite Control-o of Text-widget (which inserts a new line):
        self.bind("<Control-o>", lambda event: self._open())
        self.bind("<Button-1>", lambda event: self.tag_delete("highlight"))
        if self.text_name in [
            "interface_packages",
            "interface_generics",
            "internals_packages",
            "architecture_first_declarations",
            "architecture_last_declarations",
        ]:
            # These objects allow edit operations and need undo/redo with changes in design.text_dictionary.
            self.bind("<Key>", lambda event: self._key_event_after_idle())
            self.bind("<Control-z>", lambda event: self.undo())  # overwrite the built-in Control-z.
            self.bind("<Control-y>", lambda event: self.redo())  # overwrite the built-in Control-y.
            self.bind("<Control-Z>", lambda event: self.redo())  # add the linux-style redo
        elif text_name == "block_edit":
            # This objects allows edit operations and has undo/redo by Control-x/y, but does not
            # change design.text_dictionary.
            # Bind the built-in edit_redo also to the linux-style redo-shortcut:
            self.bind("<Control-Z>", lambda event: self._edit_redo())
        self.prepare_for_syntax_highlighting()

    def _edit_redo(self):
        # try:
        #     self.edit_redo()
        # except tk.TclError:
        #     pass
        contextlib.suppress(tk.TclError)  # Exception at redo with empty stack

    def _open(self):
        file_read.FileRead(self.window)  # Provide the same behaviour for control-o as in all other widgets.
        hdl_generate_through_hierarchy.HdlGenerateHierarchy(
            self.window.root, self.window, force=False, write_to_file=False
        )
        return "break"  # Prevent a second call of File Read by bind_all binding.

    def prepare_for_syntax_highlighting(self):
        """Prepare tags for syntax highlighting."""
        # self.position_tags is a reference to vhdl_parsing.VhdlParser.position_tags (can be
        # switched to a Verilog tag_list by self.set_taglist())
        # For each tag of tag_list a format (color, font-appearance) is defined here.
        # The keys of tag_format must be the same as the tag-names in vhdl_parsing.VhdlParser.position_tags:
        fontkind = self.cget("font")
        fontname, fontsize = fontkind.split()
        tag_format = {}
        tag_format["comment_positions"] = ("blue", fontname, fontsize, "")
        tag_format["keyword_positions"] = ("green", fontname, fontsize, "")
        tag_format["entity_library_name_positions"] = ("brown", fontname, fontsize, "")
        tag_format["entity_package_name_positions"] = ("brown", fontname, fontsize, "")
        tag_format["architecture_library_name_positions"] = ("brown", fontname, fontsize, "")
        tag_format["architecture_package_name_positions"] = ("brown", fontname, fontsize, "")
        tag_format["entity_name_positions"] = ("black", fontname, fontsize, "bold")
        tag_format["architecture_name_positions"] = ("black", fontname, fontsize, "bold")
        tag_format["entity_name_used_in_architecture_positions"] = ("black", fontname, fontsize, "bold")
        tag_format["generics_interface_names_positions"] = ("black", fontname, fontsize, "bold")
        tag_format["generics_interface_init_positions"] = ("red", fontname, fontsize, "")
        tag_format["port_interface_names_positions"] = ("black", fontname, fontsize, "bold")
        tag_format["port_interface_direction_positions"] = ("green", fontname, fontsize, "")
        tag_format["port_interface_init_positions"] = ("red", fontname, fontsize, "")
        tag_format["component_port_interface_names_positions"] = ("black", fontname, fontsize, "bold")
        tag_format["component_port_interface_init_positions"] = ("red", fontname, fontsize, "")
        tag_format["component_port_interface_direction_positions"] = ("green", fontname, fontsize, "")
        tag_format["component_generic_interface_names_positions"] = ("black", fontname, fontsize, "bold")
        tag_format["component_generic_interface_init_positions"] = ("red", fontname, fontsize, "")
        tag_format["procedure_interface_names_positions"] = ("black", fontname, fontsize, "bold")
        tag_format["function_interface_names_positions"] = ("black", fontname, fontsize, "bold")
        tag_format["data_type_positions"] = ("brown", fontname, fontsize, "")
        tag_format["label_positions"] = ("red", fontname, fontsize, "")
        tag_format["begin_label_positions"] = ("red", fontname, fontsize, "")
        # For each tag of tag_list a tag with its own format will be created now.
        # Characters will be added to the tags by self.add_syntax_highlight_tags:
        if self.position_tags is not None:
            for tag in self.position_tags:
                self.tag_config(
                    tag,
                    foreground=tag_format[tag][0],
                    font=(tag_format[tag][1], tag_format[tag][2], tag_format[tag][3]),
                )

    def store_change_in_text_dictionary(self, signal_design_change):
        """Store change in design_data dictionary."""
        # Changes in custom_text are not pushed into the change_stack,
        # as custom_text has its own Undo/Redo-Stack.
        self.text = self.get("1.0", tk.END + "- 1 chars")  # remove "return"
        if self.store_in_design:
            self.window.design.store_in_text_dictionary(
                self.text_name, self.text, signal_design_change=signal_design_change
            )
        self.add_syntax_highlight_tags()

    def add_syntax_highlight_tags(self):  # also called from block_edit.
        """Adds tags for syntax highlighting to the text. The positions of the tags are determined by the parser."""
        # Called by store_change_in_text_dictionary():
        #  - after block edit (for the new edit window)
        #  - after switching language for interface_packages_text
        #  - after update_hdl_tab for hdl_frame_text
        #  - after update_interface_tab for interface_packages_text and interface_generics_text
        #  - after update_internals_tab for internals_packages_text, internals_architecture_first/last_declarations_text
        text = self.get(
            "1.0", tk.END + "- 1 chars"
        )  # when called from block_edit, the new text is not stored yet in self.text.
        hdl = self._replace_line_numbers_with_blanks(text) if self.has_line_numbers else text
        if self.window.design.get_language() == "VHDL":
            if self.text_name == "interface_generics":
                region = "generics"
            elif self.text_name in ["architecture_first_declarations", "architecture_last_declarations"]:
                region = "architecture_declarative_region"
            elif self.text_name == "block_edit":
                region = "architecture_body"
            else:
                region = "entity_context"
        else:  # language is "Verilog" or "SystemVerilog"
            if self.text_name == "interface_generics":
                region = "parameter_region"
            elif self.text_name in ("architecture_first_declarations", "block_edit"):
                region = "declaration_region"
            else:
                region = "module"
        if self.parser_class is not None:  # Check needed, because no parser exists for the message tab.
            if len(hdl) > 10000:  # Avoid freezing the GUI for very long texts.
                executor = concurrent.futures.ProcessPoolExecutor(max_workers=None)
                future = executor.submit(_run_parser, self.parser_class, hdl, region, list(self.position_tags))
                executor.shutdown(wait=False)  # Free any resources after executing, but no waiting here.
                for tag in self.position_tags:
                    self.tag_remove(tag, "1.0", tk.END)
                self._poll_parse_result(future)
            else:
                object_positions = _run_parser(self.parser_class, hdl, region, list(self.position_tags))
                for tag, positions in object_positions.items():
                    self.tag_remove(tag, "1.0", tk.END)
                    for position in positions:
                        self.tag_add(tag, "1.0 +" + str(position[0]) + " chars", "1.0 +" + str(position[1]) + " chars")

    def _poll_parse_result(self, future):
        if not future.done():
            self.after(50, self._poll_parse_result, future)
        else:
            try:
                all_positions = future.result()
            except Exception:  # pylint: disable=broad-except
                return
            self._apply_tags_chunked(list(all_positions.items()), 0, 0, future)

    def _apply_tags_chunked(self, tag_items, tag_index, position_index, future):
        positions_to_tag = 100
        positions_tagged = 0
        while tag_index < len(tag_items) and positions_tagged < positions_to_tag:
            tag, positions = tag_items[tag_index]
            positions_remaining = positions[position_index:]
            batch = positions_remaining[: positions_to_tag - positions_tagged]
            if batch:
                args = [idx for pos in batch for idx in (f"1.0 +{pos[0]}c", f"1.0 +{pos[1]}c")]
                self.tk.call(self._w, "tag", "add", tag, *args)
            positions_tagged += len(batch)
            position_index += len(batch)
            if position_index == len(positions):
                tag_index += 1
                position_index = 0
        if tag_index < len(tag_items):
            self.after(50, self._apply_tags_chunked, tag_items, tag_index, position_index, future)

    def _replace_line_numbers_with_blanks(self, hdl):
        return re.sub("^[0-9]+:", self._replace_with_blanks, hdl, flags=re.MULTILINE)

    def _replace_with_blanks(self, matchobj):
        number_of_found_characters = matchobj.end() - matchobj.start()
        return " " * number_of_found_characters

    def _key_event_after_idle(self):
        self._key_event()
        # if self.after_identifier is not None:
        #     self.after_cancel(self.after_identifier)
        # self.after_identifier = self.after(300, self._key_event)  # wait 300 ms

    def _key_event(self):
        new_text = self.get("1.0", tk.END + "- 1 chars")
        if new_text not in ["\n", self.text]:
            self.store_change_in_text_dictionary(signal_design_change=True)

    def _edit_in_external_editor(self, design):
        file_name_tmp = "hdl-schem-editor.tmp.vhd" if design.get_language() == "VHDL" else "hdl-schem-editor.tmp.v"
        with open(file_name_tmp, "w", encoding="utf-8") as fileobject:
            fileobject.write(self.get("1.0", tk.END + "- 1 chars"))
        edit_ext.EditExt(design, file_name_tmp, number_of_line=1)
        with open(file_name_tmp, encoding="utf-8") as fileobject:
            new_text = fileobject.read()
        new_text = re.sub("\t", "    ", new_text)
        os.remove(file_name_tmp)
        if self.cget("state") != tk.DISABLED:
            self.delete("1.0", "end")
            self.insert("1.0", new_text)
        self._key_event()  # Emulate a key event, so that store_change_in_text_dictionary is called.

    def redo(self):
        """Store change and redo"""
        # try:
        #     self.edit_redo()
        # except tk.TclError:  # Exception at redo with empty stack
        #     pass
        contextlib.suppress(tk.TclError)  # Exception at redo with empty stack
        self.after_idle(self.store_change_in_text_dictionary, True)

    def undo(self):
        """Store change"""
        self.after_idle(self.store_change_in_text_dictionary, True)

    def set_parser(self, parser):
        """Select parser between VHDL and Verilog"""
        self.parser_class = parser

    def set_taglist(self, position_tags):
        """Set the tag list for syntax highlighting and prepare tags."""
        self.tag_delete("all")
        self.position_tags = position_tags
        self.prepare_for_syntax_highlighting()

    def insert_text(self, text, state_after_insert):
        """Inserts the given text and sets the state to state_after_insert"""
        self.config(state="normal")
        self.delete("1.0", "end")
        self.insert("1.0", text)
        # self.see(tk.END) wegkommentiert, damit im "generated HDL" beim Laden immer der Dateianfang sichtbar ist
        self.config(state=state_after_insert)
        self.text = text

    def insert_line(self, text, state_after_insert, color=None):
        """Insert 1 line"""
        self.config(state="normal")
        if color is None:
            self.insert(tk.END, text)
        else:
            self.insert(
                tk.END, text, ("message_" + color)
            )  # "message_"+color is a tag which is added to the inserted text (based on indices)
        self.see(tk.END)
        self.config(state=state_after_insert)
        self.text += text

    def highlight_item(self, _, __, number_of_line, ___):
        """Highlights the line in orange"""
        # The unused parameters are needed for compatibility with NotebookDiagramTab.highlight_item().
        self.tag_add("highlight", str(number_of_line) + ".0", str(number_of_line + 1) + ".0")
        self.tag_config("highlight", background="orange")
        self.see(str(number_of_line) + ".0")
        self.focus_set()

    def format_after_idle(self, event) -> None:
        """Schedule format() after 200 ms idle (except for log text)."""
        if event is not None and event.keysym in ("Control_L", "Control_R"):  # code_editor.py uses event=None
            return  # No formatting as long as Ctrl is pressed alone.
        # Prevent the formatting of the message tab, which can be very long and may contain keywords by accident (which
        # shall not be highlighted) and can not be changed by key-presses:
        if self.parser_class is not None:  # No parser exists for the message tab
            self.after_cancel(self.format_after_id)
            self.format_after_id = self.after(100, self.format, event)

    def format(self, event) -> None:
        """Update highlighting."""
        self.add_syntax_highlight_tags()
