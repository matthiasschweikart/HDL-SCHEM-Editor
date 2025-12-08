"""
This class determines the hierarchy of a VHDL or a Verilog module.
"""
from tkinter import messagebox
import vhdl_parsing
import verilog_parsing

# This is an example of a hierarchy dictionary created here:
# hierarchy-dict = {
# 'instance_name'        : ' ',
# 'module_name'          : 'testbench_division_srt_radix2',
# 'filename'             : 'testbench_division_srt_radix2_e.vhd',
# 'sub_modules'          : [{'instance_name'        : 'division_srt_radix2_inst',
#                            'module_name'          : 'division_srt_radix2',
#                            'filename'             : 'division_srt_radix2.hse',
#                            'sub_modules': [{'instance_name'        : 'division_srt_radix2_calc_shifts_inst -- 4',
#                                             'module_name'          : 'division_srt_radix2_calc_shifts',
#                                             'filename'             : 'division_srt_radix2_calc_shifts.hse',
#                                             'sub_modules'          : []
#                                            },
#                                            {'instance_name'        : 'division_srt_radix2_core_inst -- 5',
#                                             'module_name'          : 'division_srt_radix2_core',
#                                             'filename'             : 'division_srt_radix2_core.hse',
#                                             'sub_modules'          : [{'instance_name'         : 'division_srt_radix2_control_inst -- 1',
#                                                                        'module_name'           : 'division_srt_radix2_control',
#                                                                        'filename'              : 'division_srt_radix2_control.hfe',
#                                                                        'sub_modules'           : []
#                                                                       },
#                                                                       {'instance_name'         : 'division_srt_radix2_step_inst',
#                                                                        'module_name'           : 'division_srt_radix2_step',
#                                                                        'filename'              : 'division_srt_radix2_step.hse',
#                                                                        'architecture_name'     : 'struct',
#                                                                        'sub_modules'           : []
#                                                                       }, ...
#

class ExtractHierarchy():
    def __init__(self, instance_dict):
        # The dictionary instance_dict has an empty list in instance_dict["sub_modules"]. This list is created here. All other entries are already filled.
        language = instance_dict["language"]
        if instance_dict["architecture_filename"]!="" and language=="VHDL": # True for 2-file-VHDL
            filelist = [instance_dict["architecture_filename"]] + instance_dict["additional_files"]
        else:
            filelist = [instance_dict["filename"]] + instance_dict["additional_files"]
        self.used_modules_dict = self.__create_used_modules_dict(filelist, language)
        self.list_of_sub_modules_dicts = self.__get_list_of_submodule_dicts_for_module(instance_dict["module_name"])

    def __get_list_of_submodule_dicts_for_module(self, module_name):
        list_of_submodul_dicts = []
        if "instance_types" in self.used_modules_dict[module_name]: # If only an entity (without architecture) is used for the instance, then "instance_types" does not exist.
            instances_in_this_module = self.used_modules_dict[module_name]["instance_types"]
            for index, sub_module_name in enumerate(instances_in_this_module):
                if (sub_module_name!="process" and              # Processes are instances without any hierarchy and are ignored.
                    sub_module_name in self.used_modules_dict): # When additional files are missing, entries will be missing in self.used_modules_dict.
                    sub_module_dict = {}
                    if self.used_modules_dict[module_name]["target_library"][index] is not None:
                        sub_module_dict["configuration_library"] = self.used_modules_dict[module_name]["target_library"][index]
                    else:
                        sub_module_dict["configuration_library"] = "work"
                    sub_module_dict["instance_name"        ] = self.used_modules_dict[module_name    ]["label_names"  ][index]
                    sub_module_dict["module_name"          ] = self.used_modules_dict[module_name    ]["instance_types"][index]
                    sub_module_dict["filename"             ] = self.used_modules_dict[sub_module_name]["filename"]
                    sub_module_dict["entity_filename"      ] = self.used_modules_dict[sub_module_name]["filename"]
                    sub_module_dict["architecture_filename"] = self.used_modules_dict[sub_module_name]["architecture_filename"]
                    sub_module_dict["env_language"         ] = self.used_modules_dict[module_name    ]["language"]
                    sub_module_dict["architecture_name"    ] = self.used_modules_dict[sub_module_name]["architecture_name"]
                    if sub_module_name!=module_name:
                        sub_module_dict["sub_modules"] = self.__get_list_of_submodule_dicts_for_module(sub_module_name)
                        list_of_submodul_dicts.append(sub_module_dict)
        return list_of_submodul_dicts

        # Dieser sub_module_dict soll mehr Informationen tragen, als nur für den Treeview gebraucht werden,
        # damit auch eine hdl_file_list erzeugt werden kann.
        # Der filename ist nötig, wenn in ihm die Architecture enthalten ist.
        # Der Architecture-File-Name ist nötig, wenn in filename nur die Entity steckt.
        # Aus der Architecture müssen die Sub-Module extrahiert werden.

    def get_list_of_sub_modules_dicts(self):
        return self.list_of_sub_modules_dicts

    def __create_used_modules_dict(self, file_name_list, language):
        used_modules_dict = {}
        for file_name in file_name_list:
            try:
                fileobject = open(file_name, 'r', encoding="utf-8")
                data_read  = fileobject.read()
                fileobject.close()
                if language=="VHDL":
                    hdl_dict = vhdl_parsing.VhdlParser(data_read, "entity_context")
                    entity_name_used_in_arch = hdl_dict.get("entity_name_used_in_architecture")
                else:
                    hdl_dict = verilog_parsing.VerilogParser(data_read, "module")
                    entity_name_used_in_arch = hdl_dict.get("entity_name")
                entity_name = hdl_dict.get("entity_name")
                if entity_name=="":
                    if entity_name_used_in_arch=="":
                        # The file is a package file.
                        #print("_create_used_modules_dict: found package file with filename:", file_name)
                        pass
                    else:
                        # The file contains only the architecture.
                        if entity_name_used_in_arch not in used_modules_dict: # Then the file with the entity was not read until now.
                            used_modules_dict[entity_name_used_in_arch] = {}
                        used_modules_dict[entity_name_used_in_arch]["architecture_filename"] = file_name
                else:
                    # The file is a file which contains at least the entity.
                    if entity_name not in used_modules_dict: # Then the file with the architecture was not read until now.
                        used_modules_dict[entity_name] = {}
                    used_modules_dict[entity_name]["filename"] = file_name
                    if entity_name_used_in_arch!="":
                        # The file contains entity and architecture.
                        used_modules_dict[entity_name]["architecture_filename"] = file_name
                if entity_name_used_in_arch!="": # An architecture or a Verilog-file is read.
                    #used_modules_dict[entity_name_used_in_arch]["configuration_library"] = ""
                    #used_modules_dict[entity_name_used_in_arch]["instance_name"]         = ""
                    used_modules_dict[entity_name_used_in_arch]["module_name"]           = entity_name_used_in_arch
                    used_modules_dict[entity_name_used_in_arch]["language"]              = language
                    #used_modules_dict[entity_name_used_in_arch]["env_language"]          = ""
                    if language=="VHDL":
                        used_modules_dict[entity_name_used_in_arch]["architecture_name"] = hdl_dict.get("architecture_name")
                    else:
                        used_modules_dict[entity_name_used_in_arch]["architecture_name"] = "struct"
                    used_modules_dict[entity_name_used_in_arch]["instance_types"]        = hdl_dict.get("instance_types")
                    used_modules_dict[entity_name_used_in_arch]["label_names"]           = hdl_dict.get("label_names")
                    used_modules_dict[entity_name_used_in_arch]["target_library"]        = [None] * len(hdl_dict.get("label_names"))
                    used_modules_dict[entity_name_used_in_arch]["target_module"]         = [None] * len(hdl_dict.get("label_names"))
                    used_modules_dict[entity_name_used_in_arch]["target_architecture"]   = [None] * len(hdl_dict.get("label_names"))
                    if language=="VHDL":
                        list_of_instance_names_with_configuration = hdl_dict.get("configuration_instance_names")
                        list_of_module_names_with_configuration   = hdl_dict.get("configuration_module_names")
                        list_of_target_libraries                  = hdl_dict.get("configuration_target_libraries")
                        list_of_target_modules                    = hdl_dict.get("configuration_target_modules")
                        list_of_target_architectures              = hdl_dict.get("configuration_target_architectures")
                    else:
                        list_of_instance_names_with_configuration = []
                        list_of_module_names_with_configuration   = []
                        list_of_target_libraries                  = []
                        list_of_target_modules                    = []
                        list_of_target_architectures              = []
                    for instance_type in used_modules_dict[entity_name_used_in_arch]["instance_types"]:
                        if instance_type in list_of_module_names_with_configuration:
                            instance_index      = used_modules_dict[entity_name_used_in_arch]["instance_types"].index(instance_type)
                            configuration_index = list_of_module_names_with_configuration.index(instance_type)
                            if (list_of_instance_names_with_configuration[configuration_index].lower()=="all" or
                                list_of_instance_names_with_configuration[configuration_index].lower()==
                                    used_modules_dict[entity_name_used_in_arch]["label_names"][instance_index].lower()):
                                used_modules_dict[entity_name_used_in_arch]["target_library"     ][instance_index] = list_of_target_libraries    [configuration_index]
                                used_modules_dict[entity_name_used_in_arch]["target_module"      ][instance_index] = list_of_target_modules      [configuration_index]
                                used_modules_dict[entity_name_used_in_arch]["target_architecture"][instance_index] = list_of_target_architectures[configuration_index]
            except FileNotFoundError:
                messagebox.showerror("Error in HDL-SCHEM-Editor", "File " + file_name + " could not be opened during extracting hierarchy.")
        return used_modules_dict
# Example of used_modules_dict:
# {'vector_rotation':  {'configuration_library': '',
#                       'instance_name'        : '',
#                       'module_name'          : 'vector_rotation',
#                       'language'             : 'VHDL',
#                       'env_language'         : '',
#                       'filename'             : 'M:/gesicherte Daten/Programmieren/Siemens/arithmetic/hdl/arithmetic_lib/vector_rotation_struct.vhd',
#                       'architecture_name'    : 'struct',
#                       'instance_type'        : ['cordic_length_correction'     , 'cordic_rot'     , 'cordic_rot_90'     ],
#                       'label_names'          : ['cordic_length_correction_inst', 'cordic_rot_inst', 'cordic_rot_90_inst']},
# 'cordic_rot_90':     {'configuration_library': '',
#                       'instance_name'        : '',
#                       'module_name'          : 'cordic_rot_90',
#                       'language'             : 'VHDL',
#                       'env_language'         : '',
#                       'filename'             : 'M:/gesicherte Daten/Programmieren/Siemens/arithmetic/hdl/arithmetic_lib/cordic_rot_90_rtl.vhd',
#                       'architecture_name'    : 'rtl',
#                       'instance_type'        : ['process'],
#                       'label_names'          : ['p_clk']},
# 'cordic_rot':        {'configuration_library': '',
#                       'instance_name'        : '',
#                       'module_name'          : 'cordic_rot',
#                       'language'             : 'VHDL',
#                       'env_language'         : '',
#                       'filename'             : 'M:/gesicherte Daten/Programmieren/Siemens/arithmetic/hdl/arithmetic_lib/cordic_rot_rtl.vhd',
#                       'architecture_name'    : 'rtl',
#                       'instance_type'        : ['process', 'process'],
#                       'label_names'          : ['p_it'   , 'p_clk'  ]} ...
