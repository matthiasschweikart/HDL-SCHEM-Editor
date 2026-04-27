"""
This module contains methods used at HDL generation.
"""

import re

BLOCK_COMMENT_RE = re.compile(r"\/\*.*?\*\/", flags=re.DOTALL)


def remove_comments_and_returns(hdl_text, language) -> str:
    """Strip block and line comments, normalize to space-separated string for keyword search."""
    hdl_text = remove_comments(hdl_text, language)
    return hdl_text.replace("\n", " ")


def remove_comments(hdl_text, language) -> str:
    """Strip block and line comments, normalize to space-separated string for keyword search."""
    hdl_text = _remove_vhdl_block_comments(hdl_text) if language == "VHDL" else _remove_verilog_block_comments(hdl_text)
    lines_without_return = hdl_text.split("\n")
    text = ""
    for line in lines_without_return:
        line_without_comment = re.sub("--.*$", "", line) if language == "VHDL" else re.sub("//.*$", "", line)
        # Add " " at the beginning of the line. Then it is possible to search for keywords
        # surrounded by blanks also at the beginning of text:
        text += " " + line_without_comment + "\n"
    text += " "  # Add " " at the end, so that keywords at the end are also surrounded by blanks.
    return text


def _remove_vhdl_block_comments(list_string):
    """Replace /* ... */ block comments with spaces to preserve character positions."""
    # block comments are replaced by blanks, so all remaining text holds its position.
    while True:
        match_object = BLOCK_COMMENT_RE.search(list_string)
        if match_object is None:
            break
        if match_object.start() == match_object.end():
            break
        list_string = (
            list_string[: match_object.start()]
            + " " * (match_object.end() - match_object.start())
            + list_string[match_object.end() :]
        )
    return list_string


def _remove_verilog_block_comments(hdl_text):
    return re.sub("/\\*.*\\*/", "", hdl_text, flags=re.DOTALL)
