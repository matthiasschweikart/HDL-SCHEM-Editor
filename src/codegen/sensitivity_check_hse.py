"""Runs the sensitivity check after collecting all needed information."""

import re

from . import hdl_generation_library, sensitivity_check

VHDL_PROCESS_REGEX = re.compile(r"process\s*\((.*?)\).*?\s+begin(.*?)\send\s+process\s*;", re.IGNORECASE | re.DOTALL)
VERILOG_PROCESS_REGEX = re.compile(r"always\s*@\s*\((.*?)\)\s*begin(.*?)\s*end\s*always;", re.IGNORECASE | re.DOTALL)


class SensitivityCheckHse:
    def __init__(self, hdl_file_name, input_decl, inout_decl, signal_decl, language):
        self.messages = []
        process_sensitivities_and_bodies = self._collect_process_sensitivities_and_bodies(hdl_file_name, language)
        readable_sigs = self._extract_names_from_declarations(input_decl, language)
        readable_sigs.extend(self._extract_names_from_declarations(inout_decl, language))
        readable_sigs.extend(self._extract_names_from_declarations(signal_decl, language))
        if process_sensitivities_and_bodies:
            self.messages = sensitivity_check.SensitivityCheck(
                readable_sigs, process_sensitivities_and_bodies, language, hdl_file_name
            ).get_results()

    def get_messages(self) -> list[str]:
        """Returns the messages of the sensitivity check."""
        return self.messages

    def _collect_process_sensitivities_and_bodies(self, file_name, language) -> list[dict[str, int | str]]:
        with open(file_name, encoding="utf-8") as f:
            hdl = f.read()
        if hdl == "":
            return []
        hdl = hdl_generation_library.remove_comments(hdl, language)  # Returns are needed for line number calculation
        process_regex = VHDL_PROCESS_REGEX if language == "VHDL" else VERILOG_PROCESS_REGEX
        process_matches = re.finditer(process_regex, hdl)
        process_sensitivities_and_bodies = []
        for process_match in process_matches:
            char_number = process_match.start()
            line_number = hdl[:char_number].count("\n") + 1
            process_sensitivity = hdl_generation_library.remove_comments_and_returns(process_match.group(1), language)
            process_body = hdl_generation_library.remove_comments_and_returns(process_match.group(2), language)
            clocked_process = re.search(r"\s*'\s*event", process_body, re.IGNORECASE)
            if "rising_edge" not in process_body and "falling_edge" not in process_body and clocked_process is None:
                process_sensitivities_and_bodies.append(
                    {
                        "line_number": line_number,
                        "process_sensitivity": process_sensitivity,
                        "process_body": process_body,
                    }
                )
        return process_sensitivities_and_bodies

    def _extract_names_from_declarations(self, declarations, language) -> list[str]:
        list_of_names = []
        for declaration in declarations:
            if language == "VHDL":
                list_of_names.append(re.sub(r":.*", "", declaration).strip().lower())
            else:
                declaration_without_ranges = re.sub(
                    r"\[.*?\]", "", declaration
                )  # remove range from type and from signal-name
                list_of_strings = declaration_without_ranges.split(" ")
                list_of_names.append(list_of_strings[-1])
        return list_of_names
