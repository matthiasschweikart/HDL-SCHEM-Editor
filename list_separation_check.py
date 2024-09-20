import re

class ListSeparationCheck():
    def __init__(self, list_string, language):
        self.list_string = list_string
        if language=="VHDL":
            separator          = ';'
            comment_identifier = "--"
        else:
            separator          = ','
            comment_identifier = "//"
        list_string_without_block_comment = self.__replace_block_comments_by_blank(list_string)
        list_string_without_comments      = self.__replace_all_comments_at_line_end(list_string_without_block_comment, comment_identifier)
        self.__remove_illegal_separator(list_string_without_comments, separator)

    def get_fixed_list(self):
        return self.list_string

    def __replace_block_comments_by_blank(self, list_string):
        run_search = True
        while run_search:
            match_object = re.search(r"/\*.*?\*/", list_string, flags=re.DOTALL)
            if match_object is None:
                break
            list_string = list_string[:match_object.span()[0]] + ' '*(match_object.span()[1]-match_object.span()[0]) + list_string[match_object.span()[1]:]
        return list_string

    def __replace_all_comments_at_line_end(self, list_string_without_block_comment, comment_identifier):
        list_array = list_string_without_block_comment.split("\n")
        list_string_without_comments = ""
        for line in list_array:
            list_string_without_comments += self.__replace_comment_at_line_end_by_blank(comment_identifier, line) + "\n"
        return list_string_without_comments[:-1] # remove last return

    def __replace_comment_at_line_end_by_blank(self, comment_identifier, line):
        match_object = re.search(comment_identifier + ".*", line)
        if match_object is not None:
            line = line[:match_object.span()[0]] + ' '*(match_object.span()[1]-match_object.span()[0]) + line[match_object.span()[1]:]
        return line

    def __remove_illegal_separator(self, list_string_without_comments, separator):
        for index, char in enumerate(reversed(list_string_without_comments)):
            if char not in (' ', '\n'):
                if char==separator:
                    self.__remove_character_by_blank(index)
                break

    def __remove_character_by_blank(self, index):
        if index==0:
            self.list_string = self.list_string[:-index-1]
        else:
            self.list_string = self.list_string[:-index-1] + ' ' + self.list_string[-index:]
