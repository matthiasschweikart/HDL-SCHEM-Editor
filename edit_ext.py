"""
    This class is used to edit an file in an external editor.
    It is used by NotebookControlTab to read an additional file.
    It is used by block_edit und custom_text: Dort wird aber zuerst eine datei angelegt und diese anschliessend mit dem externen Editor bearbeitet
"""
import shlex
import subprocess
from tkinter import messagebox

class EditExt():
    def __init__(self, design, file_name):
        # Under linux the command must be an array:
        cmd = []
        cmd.extend(shlex.split(design.get_edit_cmd())) # Does not split quoted sub-strings with blanks.
        cmd.append(file_name)
        try:
            process = subprocess.Popen(cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        except FileNotFoundError:
            cmd_string = ""
            for entry in cmd:
                cmd_string += entry + ' '
            messagebox.showerror("Error in HDL-SCHEM-Editor", "FileNotFoundError when running:\n" + cmd_string)
            return
        while True:
            poll = process.poll()
            if poll is not None:
                break
        # # Under linux the command must be an array:
        # cmd = []
        # #cmd.extend(design.edit_cmd.split())
        # cmd.extend(shlex.split(design.get_edit_cmd())) # Does not split quoted sub-strings with blanks.
        # cmd.append(file_name_tmp)
        # try:
        #     process = subprocess.Popen(cmd, #shell=True,
        #         stdout=subprocess.PIPE,
        #         stderr=subprocess.PIPE)
        # except FileNotFoundError:
        #     cmd_string = ""
        #     for entry in cmd:
        #         cmd_string += entry + ' '
        #     messagebox.showerror("Error in HDL-SCHEM-Editor", "FileNotFoundError when running:\n" + cmd_string)
        #     return
        # while True:
        #     poll = process.poll()
        #     if poll is not None:
        #         break
