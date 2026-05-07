"""
This class is used to edit an file in an external editor.
It is used by NotebookControlTab to read an additional file.
It is used by block_edit und custom_text to read a temporary file.
"""

import shlex
import subprocess
from tkinter import messagebox


class EditExt:
    """This class is used to edit an file in an external editor."""

    def __init__(self, design, file_name, number_of_line):
        # Under linux the command must be an array:
        cmd = []
        cmd.extend(shlex.split(design.get_edit_cmd()))  # Does not split quoted sub-strings with blanks.
        edit_jmp_parameter = design.get_edit_jmp()
        if edit_jmp_parameter != "" and not edit_jmp_parameter.isspace():
            cmd.append(edit_jmp_parameter + str(number_of_line))  # Jump-to-line number
        cmd.append(file_name)
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            cmd_string = ""
            for entry in cmd:
                cmd_string += entry + " "
            messagebox.showerror("Error in HDL-SCHEM-Editor", "FileNotFoundError when running:\n" + cmd_string)
            return
        while True:
            poll = process.poll()
            if poll is not None:
                break
