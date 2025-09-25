"""
Displays the messages from the executed compile command.
"""
import tkinter as tk
from   tkinter import ttk
from   tkinter import messagebox
import re
import subprocess
import psutil

import custom_text
import link_dictionary

class NotebookLogTab():
    def __init__(self, schematic_window, notebook):
        self.schematic_window               = schematic_window
        self.regex_message_find_for_vhdl    = "(.*?):([0-9]+):[0-9]+:.*"
        self.regex_message_find_for_verilog = "(.*?):([0-9]+): .*"       # Added ' ' after the second ':', to get no hit at time stamps (i.e. 16:58:36).
        self.regex_file_name_quote          = "\\1"
        self.regex_file_line_number_quote   = "\\2"
        self.line_number_under_pointer      = -1
        self.func_id_jump1                  = None
        self.func_id_jump2                  = None
        self.process_ref                    = None
        self.log_frame = ttk.Frame(notebook)
        self.log_frame.grid()
        self.log_frame.rowconfigure   (0, weight=0)
        self.log_frame.rowconfigure   (1, weight=1)
        self.log_frame.columnconfigure(0, weight=1)
        self.log_frame.columnconfigure(1, weight=0)
        self.log_frame_button_frame = ttk.Frame             (self.log_frame)
        self.log_frame_text         = custom_text.CustomText(self.log_frame, window=self.schematic_window, parser=None,
                                                                             tag_position_list=None, store_in_design=False, font=("Courier", 10), text_name="log_text", undo=False)
        self.log_frame_text_scroll  = ttk.Scrollbar         (self.log_frame, orient=tk.VERTICAL, cursor='arrow', command=self.log_frame_text.yview)
        self.log_frame_text.config(state=tk.DISABLED)
        self.log_frame_text.config(yscrollcommand=self.log_frame_text_scroll.set)
        self.log_frame_button_frame.grid(row=0, column=0, sticky=tk.W)
        self.log_frame_text        .grid(row=1, column=0, sticky=(tk.N,tk.W,tk.E,tk.S))
        self.log_frame_text_scroll .grid(row=1, column=1, sticky=(tk.W,tk.E,tk.S,tk.N))
        self.log_frame_kill_button  = ttk.Button(self.log_frame_button_frame, takefocus=False, text="Kill process", state=tk.DISABLED)
        self.log_frame_clear_button = ttk.Button(self.log_frame_button_frame, takefocus=False, text="Clear"                      )
        self.log_frame_regex_button = ttk.Button(self.log_frame_button_frame, takefocus=False, text="Define Regex for Hyperlinks")
        self.log_frame_kill_button .grid(row=0, column=0, sticky=tk.W)
        self.log_frame_clear_button.grid(row=0, column=1, sticky=tk.W)
        self.log_frame_regex_button.grid(row=0, column=2, sticky=tk.W)
        self.log_frame_text.bind("<Motion>", self.__cursor_move)
        self.log_frame_kill_button .bind ('<Button-1>', self.__kill_process)
        self.log_frame_clear_button.bind ('<Button-1>', self.__clear)
        self.log_frame_regex_button.bind ('<Button-1>', self.__edit_regex)
        self.debug_active = tk.IntVar()
        self.debug_active.set(1) # 1: inactive, 2: active
        notebook.add(self.log_frame, sticky=tk.N+tk.E+tk.W+tk.S, text="Messages")
        self.regex_dialog                  = None
        self.regex_dialog_header           = None
        self.regex_dialog_entry            = None
        self.regex_dialog_filename_label   = None
        self.regex_dialog_filename_entry   = None
        self.regex_dialog_linenumber_label = None
        self.regex_dialog_linenumber_entry = None
        self.regex_dialog_identifier_frame = None
        self.regex_dialog_store_button     = None
        self.regex_dialog_cancel_button    = None
        self.regex_error_happened          = False
        self.regex_button_frame            = None
        self.debug_stdout_label            = None
        self.debug_stdout_frame            = None
        self.debug_stdout_radio_button1    = None
        self.debug_stdout_radio_button2    = None

    def __kill_process(self, *_):
        if self.process_ref is not None:
            p = psutil.Process(self.process_ref.pid)
            for sub_process in p.children(recursive=True):
                sub_process.kill()
        self.log_frame_kill_button.config(state=tk.DISABLED)
        self.insert_line_in_log("Killed by button 'Kill process'\n", state_after_insert="disabled")

    def activate_kill_button(self, process_ref):
        self.log_frame_kill_button.config(state=tk.ACTIVE)
        self.process_ref = process_ref

    def deactivate_kill_button(self):
        self.log_frame_kill_button.config(state=tk.DISABLED)
        self.process_ref = None

    def __clear(self, *_):
        self.log_frame_text.config(state=tk.NORMAL)
        self.log_frame_text.delete("1.0", "end")
        self.log_frame_text.config(state=tk.DISABLED)

    def __edit_regex(self, *_):
        self.regex_dialog                  = tk.Toplevel()
        self.regex_dialog.title("Enter Regex for Python:")
        self.regex_dialog_header           = ttk.Label(self.regex_dialog, text="Regex for finding a message with\ngroup for file-name and\ngroup for line-number:", justify="left")
        self.regex_dialog_entry            = ttk.Entry(self.regex_dialog)
        self.regex_dialog_identifier_frame = ttk.Frame(self.regex_dialog)
        self.regex_button_frame            = ttk.Frame(self.regex_dialog)
        self.regex_dialog_header          .grid(row=0, sticky=(tk.W,tk.E))
        self.regex_dialog_entry           .grid(row=1, sticky=(tk.W,tk.E))
        self.regex_dialog_identifier_frame.grid(row=2)
        self.regex_button_frame           .grid(row=3, sticky=(tk.W,tk.E))
        self.regex_dialog_filename_label   = ttk.Label (self.regex_dialog_identifier_frame, text="Group identifier for file-name:", justify="left")
        self.regex_dialog_filename_entry   = ttk.Entry (self.regex_dialog_identifier_frame, width=40)
        self.regex_dialog_linenumber_label = ttk.Label (self.regex_dialog_identifier_frame, text="Group identifier for line-number:", justify="left")
        self.regex_dialog_linenumber_entry = ttk.Entry (self.regex_dialog_identifier_frame, width=40)
        self.regex_dialog_filename_label  .grid(row=0, column=0, sticky=tk.W)
        self.regex_dialog_filename_entry  .grid(row=0, column=1)
        self.regex_dialog_linenumber_label.grid(row=1, column=0, sticky=tk.W)
        self.regex_dialog_linenumber_entry.grid(row=1, column=1)
        self.regex_dialog_store_button     = ttk.Button(self.regex_button_frame, text="Store" , command=self.__regex_store)
        self.regex_dialog_cancel_button    = ttk.Button(self.regex_button_frame, text="Cancel", command=self.__regex_cancel)
        self.debug_stdout_label            = ttk.Label (self.regex_button_frame, text="Debug Regex at STDOUT:", padding=5)
        self.debug_stdout_frame            = ttk.Frame (self.regex_button_frame)
        self.regex_dialog_store_button    .grid(row=0, column=0)
        self.regex_dialog_cancel_button   .grid(row=0, column=1)
        self.debug_stdout_label           .grid(row=0, column=2, sticky=tk.W)
        self.debug_stdout_frame           .grid(row=0, column=3, sticky=tk.W)
        self.debug_stdout_radio_button1 = ttk.Radiobutton(self.debug_stdout_frame, takefocus=False, variable=self.debug_active, text="Inactive" , value=1)
        self.debug_stdout_radio_button2 = ttk.Radiobutton(self.debug_stdout_frame, takefocus=False, variable=self.debug_active, text="Active"   , value=2)
        self.debug_stdout_radio_button1.grid(row=0, column=1, sticky=tk.W)
        self.debug_stdout_radio_button2.grid(row=0, column=2, sticky=tk.W)
        if self.schematic_window.design.get_language()=="VHDL":
            self.regex_dialog_entry.insert(0, self.regex_message_find_for_vhdl)
        else:
            self.regex_dialog_entry.insert(0, self.regex_message_find_for_verilog)
        self.regex_dialog_filename_entry  .insert(0, self.regex_file_name_quote)
        self.regex_dialog_linenumber_entry.insert(0, self.regex_file_line_number_quote)

    def __regex_store(self, *_):
        if self.schematic_window.design.get_language()=="VHDL":
            self.regex_message_find_for_vhdl = self.regex_dialog_entry.get()
            self.schematic_window.design.store_regex_for_log_tab(self.regex_message_find_for_vhdl)
        else:
            self.regex_message_find_for_verilog = self.regex_dialog_entry.get()
            self.schematic_window.design.store_regex_for_log_tab(self.regex_message_find_for_verilog)
        self.regex_file_name_quote        = self.regex_dialog_filename_entry  .get()
        self.regex_file_line_number_quote = self.regex_dialog_linenumber_entry.get()
        self.schematic_window.design.store_regex_file_name_quote(self.regex_file_name_quote)
        self.schematic_window.design.store_regex_file_line_number_quote(self.regex_file_line_number_quote)
        self.regex_error_happened = False
        self.regex_dialog.destroy()

    def __regex_cancel(self, *_):
        self.regex_dialog.destroy()

    def __cursor_move(self, *_):
        if self.log_frame_text.get("1.0", tk.END + "- 1 char")=="":
            return
        if self.debug_active.get()==2:
            debug_active = True
        else:
            debug_active = False
        # Determine current cursor position:
        delta_x = self.log_frame_text.winfo_pointerx() - self.log_frame_text.winfo_rootx()
        delta_y = self.log_frame_text.winfo_pointery() - self.log_frame_text.winfo_rooty()
        index_string = self.log_frame_text.index(f"@{delta_x},{delta_y}")
        # Determine current line number:
        line_number = int(re.sub(r"\..*", "", index_string))
        if line_number!=self.line_number_under_pointer and not self.regex_error_happened:
            self.log_frame_text.tag_delete("underline")
            if self.schematic_window.design.get_language()=="VHDL":
                regex_message_find = self.regex_message_find_for_vhdl
            else:
                regex_message_find = self.regex_message_find_for_verilog
            content_of_line = self.log_frame_text.get(str(line_number) + ".0", str(line_number+1) + ".0")
            content_of_line = content_of_line[:-1] # Remove return
            match_object_of_message = re.match(regex_message_find, content_of_line)
            if debug_active:
                print("\nUsed Regex                         : ", regex_message_find)
            if match_object_of_message is not None:
                try:
                    file_name = re.sub(regex_message_find, self.regex_file_name_quote, content_of_line)
                    if debug_active:
                        print("Regex found line                   : ", content_of_line)
                        print("Regex found filename (group 1)     :", '"' + file_name + '"')
                    file_line_number_string = re.sub(regex_message_find, self.regex_file_line_number_quote, content_of_line)
                    if file_line_number_string!=content_of_line:
                        file_line_number = int(file_line_number_string)
                        if debug_active:
                            print("Regex found line-number (group 2)  :", '"' + file_line_number_string + '"')
                    else:
                        if debug_active:
                            print("Regex found no line-number         : Getting line-number by group 2 did not work.")
                        return
                    file_name = re.sub("_flipflop_stat", "", file_name) # The flipflop_stat files are not stored in the LinkDict.
                    if file_name in link_dictionary.LinkDictionary.link_dict_reference.link_dict: # For example ieee source files are not a key in link_dict.
                        if file_line_number in link_dictionary.LinkDictionary.link_dict_reference.link_dict[file_name]["lines"]:
                            if debug_active:
                                print("Filename and line-number are found in Link-Dictionary.")
                            self.log_frame_text.tag_add("underline", str(line_number) + ".0", str(line_number+1) + ".0" )
                            tag_names = self.log_frame_text.tag_names(str(line_number) + ".0")
                            if "message_green" not in tag_names:
                                self.log_frame_text.tag_config("underline", underline=1, foreground="red")
                            else:
                                self.log_frame_text.tag_config("underline", underline=1)
                            self.func_id_jump1 = self.log_frame_text.bind("<Control-Button-1>",
                                                                        lambda event : link_dictionary.LinkDictionary.link_dict_reference.jump_to_source(file_name,
                                                                                                                                                        file_line_number))
                            self.func_id_jump2 = self.log_frame_text.bind("<Alt-Button-1>",
                                                                        lambda event : link_dictionary.LinkDictionary.link_dict_reference.jump_to_hdl(file_name,
                                                                                                                                                    file_line_number))
                        else:
                            if debug_active:
                                print("Filename is found in Link-Dictionary but line-number not.")
                             # Add only tag (for coloring in red), but don't underline as no link exists.
                            self.log_frame_text.tag_add("underline", str(line_number) + ".0", str(line_number+1) + ".0" )
                    else: # A message regarding a VHDL/Verilog module is found, which is not a HDL-SCHEM-Editor design.
                        if debug_active:
                            print("Filename is not found in Link-Dictionary.")
                        self.log_frame_text.tag_add("underline", str(line_number) + ".0", str(line_number+1) + ".0" )
                        tag_names = self.log_frame_text.tag_names(str(line_number) + ".0")
                        if "message_green" not in tag_names:
                            self.log_frame_text.tag_config("underline", underline=1, foreground="red")
                        else:
                            self.log_frame_text.tag_config("underline", underline=1)
                        self.func_id_jump1 = self.log_frame_text.bind("<Control-Button-1>", lambda event : self.__open_hdl_file(file_name, file_line_number))
                        self.func_id_jump2 = self.log_frame_text.bind("<Alt-Button-1>"    , lambda event : self.__open_hdl_file(file_name, file_line_number))
                except Exception as e:
                    self.regex_error_happened = True
                    messagebox.showerror("Error in HDL-SCHEM-Editor by regular expression", repr(e))
            else:
                if debug_active:
                    print("Regex did not match line           : ", content_of_line)
                if self.func_id_jump1 is not None:
                    self.log_frame_text.unbind("<Button-1>", self.func_id_jump1)
                if self.func_id_jump2 is not None:
                    self.log_frame_text.unbind("<Button-1>", self.func_id_jump2)
                self.func_id_jump1 = None
                self.func_id_jump2 = None
            self.line_number_under_pointer = line_number

    def update_hdl_log_from(self, new_dict):
        if "regex_message_find" in new_dict and new_dict["regex_message_find"]!="":
            if new_dict["language"]=="VHDL":
                self.regex_message_find_for_vhdl = new_dict["regex_message_find"]
            else:
                self.regex_message_find_for_verilog = new_dict["regex_message_find"]
        if "regex_file_name_quote" in new_dict and new_dict["regex_file_name_quote"]!="":
            self.regex_file_name_quote = new_dict["regex_file_name_quote"]
        else:
            self.regex_file_name_quote = "\\1"
        if "regex_file_line_number_quote" in new_dict and new_dict["regex_file_line_number_quote"]!="":
            self.regex_file_line_number_quote = new_dict["regex_file_line_number_quote"]
        else:
            self.regex_file_line_number_quote = "\\2"

    def insert_line_in_log(self, text, state_after_insert):
        if self.schematic_window.design.get_language()=="VHDL":
            regex_message_find = self.regex_message_find_for_vhdl
        else:
            regex_message_find = self.regex_message_find_for_verilog
        text_low = text.lower()
        match_object_of_message = re.match(regex_message_find, text)
        if match_object_of_message is not None or " error " in text_low  or " warning " in text_low or " error:" in text_low  or " warning:" in text_low:
            if self.schematic_window.design.get_language()=="VHDL" and "report note" in text_low:
                self.log_frame_text.insert_line(text, state_after_insert, color="green")
            else:
                self.log_frame_text.insert_line(text, state_after_insert, color="red")
        else:
            self.log_frame_text.insert_line(text, state_after_insert)

    def __open_hdl_file(self, file_name, file_line_number):
        command = self.schematic_window.design.get_edit_cmd() + " -n" + str(file_line_number)
        if command=="" or command.isspace():
            messagebox.showerror("Error in HDL-SCHEM-Editor", 'Cannot open source code of module because no "edit command" is defined in the control tab.')
            return
        # Under linux the command must be an array:
        cmd = []
        cmd.extend(command.split())
        cmd.append(file_name)
        try:
            subprocess.Popen(cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        except FileNotFoundError:
            messagebox.showerror("Error in HDL-SCHEM-Editor", "File not found when running " + command + ' "' + file_name + '"')
