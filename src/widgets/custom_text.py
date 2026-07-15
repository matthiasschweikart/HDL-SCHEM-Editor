"""This class expands the tkinter Text-class"""

import concurrent.futures
import contextlib
import os
import re
import tkinter as tk
from typing import Literal

import constants
from actions import edit_ext
from codegen import hdl_generate_through_hierarchy
from data_io import file_read
from hdl_parser import vhdl_parsing

from .code_editor import CodeEditor


# Module-level function – must be a top-level def to be pickleable for ProcessPoolExecutor.
def _run_parser(parser_class, hdl, region):
    parse_ref = parser_class(hdl, region)
    return {text_type: parse_ref.get_positions(text_type + "_positions") for text_type in CustomText.hdl_text_style}


class CustomText(CodeEditor):
    """This class expands the tkinter Text-class."""

    hdl_text_style = {  # The names of the keys are defined by VHDL- and Verilog-Parser.
        "comment": {"color": "blue", "fontweight": ""},
        "keyword": {"color": "green", "fontweight": ""},
        "entity_library_name": {"color": "brown", "fontweight": ""},
        "entity_package_name": {"color": "brown", "fontweight": ""},
        "architecture_library_name": {"color": "brown", "fontweight": ""},
        "architecture_package_name": {"color": "brown", "fontweight": ""},
        "entity_name": {"color": "black", "fontweight": "bold"},
        "architecture_name": {"color": "black", "fontweight": "bold"},
        "entity_name_used_in_architecture": {"color": "black", "fontweight": "bold"},
        "generics_interface_names": {"color": "black", "fontweight": "bold"},
        "generics_interface_init": {"color": "red", "fontweight": ""},
        "port_interface_names": {"color": "black", "fontweight": ""},
        "port_interface_direction": {"color": "green", "fontweight": ""},
        "port_interface_init": {"color": "red", "fontweight": ""},
        "component_port_interface_names": {"color": "black", "fontweight": "bold"},
        "component_port_interface_init": {"color": "red", "fontweight": ""},
        "component_port_interface_direction": {"color": "green", "fontweight": ""},
        "component_generic_interface_names": {"color": "black", "fontweight": "bold"},
        "component_generic_interface_init": {"color": "red", "fontweight": ""},
        "procedure_interface_names": {"color": "black", "fontweight": "bold"},
        "function_interface_names": {"color": "black", "fontweight": "bold"},
        "data_type": {"color": "brown", "fontweight": ""},
        "label": {"color": "red", "fontweight": ""},
        "begin_label": {"color": "red", "fontweight": ""},
    }

    def __init__(
        self,
        *args,
        window,
        # identifier text_name for storing the text in the design_dictionary can have one of these values:
        # "block_edit","generated_hdl","interface_packages","interface_generics",
        # "internals_packages","architecture_first_declarations","architecture_last_declarations","log_text"
        text_name,
        region: dict[Literal["vhdl", "verilog"], str],  # The region of the HDL which is edited by this widget.
        parser: vhdl_parsing.VhdlParser,
        store_in_design_data=True,  # store_in_design_data=False is only used by block_edit.py and notebook_log_tab.py.
        has_line_numbers=False,
        disabled=False,
        **kwargs,
    ):
        self.window = window
        self.text_name = text_name
        self.region = region
        self.parser_class = parser
        self.store_in_design_data = store_in_design_data
        self.has_line_numbers = has_line_numbers
        self.disabled = disabled
        self.text = ""
        self.overwrite = False  # Is used to switch from "insert" mode to "overwrite" mode. Toggle per "Insert" key.
        self.after_identifier = None
        super().__init__(*args, **kwargs)
        if self.disabled:
            self.config(state=tk.DISABLED)
        if self.store_in_design_data:
            # Create an empty entry, so that after write into a file, at read an entry exists for all text objects.
            self.window.design.store_in_text_dictionary(self.text_name, "", signal_design_change=False)
        self.bind("<Control-o>", lambda event: self._open())  # overwrite Control-o of widget (which inserts a new line)
        self.bind("<Control-e>", lambda event: self._edit_in_external_editor(self.window.design))
        self.bind("<Button-1>", lambda event: self.tag_delete("highlight"))  # Needed after using a HDL/message-link.
        if self.store_in_design_data:  # This text-widget allows edit operations and stores changes in design data.
            self.bind("<Key>", self._key_event_after_idle)  # Adds overwrite-mode and store-actions.
            self.bind("<Control-z>", lambda event: self._undo_or_redo_and_store())  # Adds store-actions to Ctrl-z.
            self.bind("<Control-y>", lambda event: self._undo_or_redo_and_store())  # Adds store-actions to Ctrl-y.
            self.bind("<Control-Z>", lambda event: self._edit_redo_and_store())  # Adds store-actions to Linux-Ctrl-Z.
            self.bind("<Insert>", lambda event: self._toggle_overwrite())  # Switch between insert/overwrite mode.
            self.bind("<Control-C>", lambda event: self._toggle_comment())
        elif not self.disabled:  # This text-widget allows edit operations but does not store in design data.
            self.bind("<Key>", self._key_event_after_idle)  # Adds overwrite mode.
            self.bind("<Control-Z>", lambda event: self._edit_redo())  # Adds Linux-Ctrl-Z.
            self.bind("<Insert>", lambda event: self._toggle_overwrite())  # Switch between insert/overwrite mode.
            self.bind("<Control-C>", lambda event: self._toggle_comment())
        self._define_text_tags(kwargs.get("font"))

    def _define_text_tags(self, font):
        self.tag_configure("message_red", foreground="red")
        self.tag_configure("message_green", foreground="green")
        self.tag_configure("highlight", background="orange")
        self.tag_configure("generated_entity_bg", background=self.window.root.generated_entity_bg)
        self.tag_configure("generated_arch_bg", background=self.window.root.generated_arch_bg)
        self._provide_hdl_text_tags_for_this_font(*font)

    def _provide_hdl_text_tags_for_this_font(self, fontname, fontsize):
        """Prepare syntax highlighting format tags for custom_text."""
        for text_type, type_dict in CustomText.hdl_text_style.items():
            self.tag_config(
                text_type,
                foreground=type_dict["color"],
                font=(
                    fontname,
                    fontsize,
                    type_dict["fontweight"],
                ),
            )

    def _open(self):
        file_read.FileRead(self.window)  # Provide the same behaviour for control-o as in all other widgets.
        hdl_generate_through_hierarchy.HdlGenerateHierarchy(
            self.window.root, self.window, force=False, write_to_file=False
        )
        return "break"  # Prevent a second call of File Read by bind_all binding.

    def _key_event_after_idle(self, event):
        self._delete_character_if_overwrite_mode(event)
        # Cancel calling _key_event in order to limit the number of _key_event() calls.
        if self.after_identifier is not None:
            self.after_cancel(self.after_identifier)
        self.after_identifier = self.after(300, self._key_event)  # wait 300 ms
        return  # Tkinter handles all other things to do with the key.

    def _delete_character_if_overwrite_mode(self, event):
        if self.overwrite and event.keysym not in ("BackSpace", "Delete", "Control_L", "Control_R"):
            cursor_index = self.index(tk.INSERT)
            if self.get(cursor_index) != "\n" and self.compare(cursor_index, "<", tk.END):
                self.delete(cursor_index)

    def _key_event(self):
        new_text = self.get("1.0", tk.END + "- 1 chars")
        if new_text not in ["\n", self.text]:
            if self.store_in_design_data:
                self.store_change_in_text_dictionary_and_add_syntax_highlight_tags(signal_design_change=True)
            else:
                self.add_syntax_highlight_tags()

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
        self._key_event()  # Emulates key-event and calls store_change_in_text_dictionary_and_add_syntax_highlight_tags.

    def _undo_or_redo_and_store(self):
        self.after_idle(self.store_change_in_text_dictionary_and_add_syntax_highlight_tags, True)
        # The Tkinter text widget handles Ctrl-z or Ctrl-y by itself.

    def _edit_redo_and_store(self):
        with contextlib.suppress(tk.TclError):  # Exception at redo with empty stack
            self.edit_redo()  # The Tkinter text widget cannot handle Ctrl-Z by itself.
        self.after_idle(self.store_change_in_text_dictionary_and_add_syntax_highlight_tags, True)
        return "break"  # Don't send Ctrl-Z to the text widget, as it will be ignored there anyway.

    def _edit_redo(self):
        with contextlib.suppress(tk.TclError):  # Exception at redo with empty stack
            self.edit_redo()  # The Tkinter text widget cannot handle Ctrl-Z by itself.
        return "break"  # Don't send Ctrl-Z to the text widget, as it will be ignored there anyway.

    def _toggle_overwrite(self):
        self.overwrite = not self.overwrite
        return "break"

    def _toggle_comment(self):
        comment_string = "--" if self.window.design.get_language() == "VHDL" else "//"
        start_line, end_line = self._get_range_of_lines_to_comment_or_uncomment()
        all_lines_are_comments = self._check_if_all_lines_are_already_comments(start_line, end_line, comment_string)
        for line_number in range(start_line, end_line + 1):
            line_content = self.get(f"{line_number}.0", f"{line_number}.end")
            if all_lines_are_comments:  # All lines are commented, so remove the comment string from each line.
                self._remove_comment_from_line(line_number, line_content, comment_string)
            else:  # At least one line is not commented, so add the comment string to all lines.
                self._change_line_into_a_comment(line_number, line_content, comment_string, start_line)
        self.format_after_idle(event=None)
        return "break"

    def _get_range_of_lines_to_comment_or_uncomment(self) -> tuple[int, int]:
        if self.tag_ranges(tk.SEL):
            start_index = self.index(tk.SEL_FIRST)
            start_line = int(start_index.split(".", maxsplit=1)[0])
            end_index = self.index(tk.SEL_LAST)
            if end_index.endswith(".0"):
                end_line = int(end_index.split(".", maxsplit=1)[0]) - 1
            else:
                end_line = int(end_index.split(".", maxsplit=1)[0])
        else:
            start_line = int(self.index(tk.INSERT).split(".", maxsplit=1)[0])
            end_line = start_line
        return start_line, end_line

    def _check_if_all_lines_are_already_comments(self, start_line, end_line, comment_string):
        for line_number in range(start_line, end_line + 1):
            line_content = self.get(f"{line_number}.0", f"{line_number}.end")
            if not line_content.lstrip().startswith(comment_string):
                return False
        return True

    def _change_line_into_a_comment(self, line_number, line_content, comment_string, start_line):
        number_of_leading_blanks = len(re.search(r"^\s*", line_content).group(0))
        self.insert(f"{line_number}.{number_of_leading_blanks}", comment_string + " ")
        if line_number == start_line and self.tag_nextrange(tk.SEL, f"{line_number}.0"):
            self._extend_selection_to_new_line_start(line_number)

    def _extend_selection_to_new_line_start(self, line_number):
        self.tag_add(tk.SEL, f"{line_number}.0", tk.INSERT)

    def _remove_comment_from_line(self, line_number, line_content, comment_string):
        match_object = re.search(r"(^\s*)" + comment_string + r"(.?)", line_content)
        comment_string_start_index = match_object.start() + len(match_object.group(1))
        comment_string_end_index = comment_string_start_index + len(comment_string)
        ends_with_blank = match_object.group(2) == " "
        if ends_with_blank:
            comment_string_end_index += 1
        self.delete(f"{line_number}.{comment_string_start_index}", f"{line_number}.{comment_string_end_index}")

    def store_change_in_text_dictionary_and_add_syntax_highlight_tags(self, signal_design_change):
        """Store change in design_data dictionary."""
        # Changes in custom_text are not pushed into the change_stack,
        # as custom_text has its own Undo/Redo-Stack.
        self.text = self.get("1.0", tk.END + "- 1 chars")  # remove "return"
        if self.store_in_design_data:
            self.window.design.store_in_text_dictionary(
                self.text_name, self.text, signal_design_change=signal_design_change
            )
        self.add_syntax_highlight_tags()

    def insert_text(self, text, state_after_insert, append=False, tags=None):
        """Inserts the given text and sets the state to state_after_insert"""
        self.config(state="normal")
        if not append:
            self.delete("1.0", tk.END)
        self.insert(tk.END, text, tags)
        self.config(state=state_after_insert)
        self.text = text

    def insert_line(self, text, state_after_insert, color=None):
        """Insert 1 line"""
        self.config(state="normal")
        if color is None:
            self.insert(tk.END, text)
        else:
            # "message_"+color is a tag which is added to the inserted text (based on indices)
            self.insert(tk.END, text, ("message_" + color))
        self.see(tk.END)
        self.config(state=state_after_insert)
        self.text += text

    def adapt_to_new_fontsize(self, new_font_size):
        """Adapt the fontsize for this widget"""
        fontkind = self.cget("font")
        fontname, _ = fontkind.split()
        self.configure(font=(fontname, new_font_size))
        self._provide_hdl_text_tags_for_this_font(fontname, new_font_size)

    def change_parser(self, parser):
        """Select parser between VHDL and Verilog"""
        self.parser_class = parser

    def highlight_item(self, _, __, number_of_line, ___):
        """Highlights the line in orange"""
        # The unused parameters are needed for compatibility with NotebookDiagramTab.highlight_item().
        self.tag_add("highlight", str(number_of_line) + ".0", str(number_of_line + 1) + ".0")
        self.see(str(number_of_line) + ".0")
        self.focus_set()

    def format_after_idle(self, event) -> None:  # Used only by code_editor (event is always None)
        """Schedule storing and highlighting after key events."""
        # Bindings work even if the state of custom_text is "disabled" as the message tab, so it is necessary to
        # block the highlighting of the message tab, which could contain a big text (with keywords by accident):
        if self.store_in_design_data:  # Text contains HDL code , so store and highlight.
            self.after_idle(self.store_change_in_text_dictionary_and_add_syntax_highlight_tags, True)
        elif self.disabled == 0:  # Text can be edited, so highlight syntax.
            self.after_idle(self.add_syntax_highlight_tags)

    def add_syntax_highlight_tags(self):  # also called from block_edit.
        """Adds tags for syntax highlighting to the text. The positions of the tags are determined by the parser."""
        # Called by store_change_in_text_dictionary_and_add_syntax_highlight_tags():
        #  - after block edit (for the new edit window)
        #  - after switching language for interface_packages_text
        #  - after update_hdl_tab for hdl_frame_text
        #  - after update_interface_tab for interface_packages_text and interface_generics_text
        #  - after update_internals_tab for internals_packages_text, internals_architecture_first/last_declarations_text
        text = self.get(
            "1.0", tk.END + "- 1 chars"
        )  # when called from block_edit, the new text is not stored yet in self.text.
        hdl = self._replace_line_numbers_with_blanks(text) if self.has_line_numbers else text
        region = self.region["vhdl"] if self.window.design.get_language() == "VHDL" else self.region["verilog"]
        if self.parser_class is not None:  # Check needed, because no parser exists for the message tab.
            if len(hdl) > 10000:  # Avoid freezing the GUI for very long texts.
                executor = concurrent.futures.ProcessPoolExecutor(max_workers=None)
                future = executor.submit(_run_parser, self.parser_class, hdl, region)
                executor.shutdown(wait=False)  # Free any resources after executing, but no waiting here.
                for text_type in CustomText.hdl_text_style:
                    self.tag_remove(text_type, "1.0", tk.END)
                self._poll_parse_result(future)
            else:
                object_positions = _run_parser(self.parser_class, hdl, region)
                for text_type, positions in object_positions.items():
                    self.tag_remove(text_type, "1.0", tk.END)
                    for position in positions:
                        self.tag_add(
                            text_type, "1.0 +" + str(position[0]) + " chars", "1.0 +" + str(position[1]) + " chars"
                        )

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

    def set_background_color(self, hdl_area, color):
        """Set default background colors for generated entity and architecture text."""
        self.tag_configure(hdl_area, background=color)

    def set_default_background_colors(self):
        """Set default background colors for generated entity and architecture text."""
        self.tag_configure("generated_entity_bg", background=constants.PALE_BROWN)  # Pale brown
        self.tag_configure("generated_arch_bg", background=constants.PALE_YELLOW)  # Pale yellow
