import pandas as pd
import hatchet.graphframe
from hatchet.node import Node
from hatchet.graph import Graph
from hatchet.frame import Frame


class MetaReader:
    # adds new context id and return new nid
    def _add_context_id(self, context_id) -> int:
        self.nid_to_ctx[self.current_nid] = context_id
        self.current_nid += 1
        return self.current_nid - 1

    def __init__(self, file_location):
        # open the file to ready in binary mode (rb)
        self.file = open(file_location, "rb")

        # setting necessary read options
        self.byte_order = "little"
        self.signed = False
        self.encoding = "ASCII"
        self.current_nid = 0
        self.nid_to_ctx = {}
        self.node_map = {}

        # The meta.db header consists of the common .db header and n sections.
        # We're going to do a little set up work, so that's easy to change if
        # any revisions change the orders.

        # We're are going to specify 2 maps:
        #   - One dictionary maps the section name to an index
        #       (which follows the order that the sections are seen
        #        in the meta.db header)
        #   - The second dictionary maps the section name to a
        #       function that reads the section. Each function is defined
        #       as __read_<section_name>_section(self, section_pointer: int,
        #       section_size: int) -> None

        # Here I'm mapping the section name to it's order in the meta.db header
        header_map = {
            "General Properties": 0,
            "Identifier Names": 1,
            "Performance Metrics": 2,
            "Context Tree": 3,
            "Common String Table": 4,
            "Load Modules": 5,
            "Source Files": 6,
            "Functions": 7,
        }

        # Now let's create a function to section map
        reader_map = {
            "General Properties": self.__read_general_properties_section,
            "Common String Table": self.__read_common_string_table_section,
            "Source Files": self.__read_source_files_section,
            "Functions": self.__read_functions_section,
            "Load Modules": self.__read_load_modules_section,
            "Context Tree": self.__read_context_tree_section,
            "Identifier Names": self.__read_identifier_names_section,
            "Performance Metrics": self.__read_performance_metrics_section,
        }

        # Another thing thing that we should consider is the order to read the sections.
        # Here is a list of section references (x -> y means x references y)
        #   - "Source Files"    ->  "Common String Table"
        #   - "Functions"       ->  "Common String Table"
        #   - "Context Tree"    ->  "Common String Table"
        #   - "Load Modules"    ->  "Common String Table"
        #   - "Functions"       ->  "Source Files"
        #   - "Context Tree"    ->  "Functions"
        #   - "Context Tree"    ->  "Source Files"
        #   - "Functions"       ->  "Load Modules"
        #
        # Thus we want to keep this order when reading sections:
        # "Common String Table" -> "Source Files" -> "Functions" -> "Context Tree", and
        # "Common String Table -> "Load Modules" -> "Context Tree"
        # Here I'm specifying the order of reading the file
        self.read_order = [
            "Common String Table",
            "General Properties",
            "Source Files",
            "Load Modules",
            "Functions",
            "Context Tree",
            "Identifier Names",
            "Performance Metrics",
        ]

        # Let's make sure that we include every section in the read order and reader_map
        assert set(self.read_order) == set(header_map) and set(header_map) == set(
            reader_map
        )

        # Now to the actual reading of the meta.db file

        # reading the meta.db header
        self.__read_common_header()

        # now let's read all the sections
        for section_name in self.read_order:
            print("\n" + section_name)
            section_index = header_map[section_name]
            section_pointer = self.section_pointer[section_index]
            section_size = self.section_size[section_index]
            section_reader = reader_map[section_name]
            # print(section_index, section_pointer, section_size, section_reader)
            section_reader(section_pointer, section_size)

    def get_information_from_context_id(self, context_id: int):
        context: dict = self.context_map[context_id]
        if "string_index" in context:
            return {
                "module": "",
                "file": "",
                "function": self.common_strings[context["string_index"]],
                "relation": -1,
                "lexical_type": -1,
                "line": -1,
                "loop_type": False,
            }

            # return self.common_strings[context["string_index"]]
        # context = {"relation": relation, "lexical_type": lexical_type, \
        #                "function_index": function_index, \
        #                "source_file_index": source_file_index, \
        #                "source_file_line": source_file_line, \
        #                "load_module_index":load_module_index, \
        #                "load_module_offset": load_module_offset}

        load_module_index = context["load_module_index"]
        source_file_index = context["source_file_index"]
        source_file_line = context["source_file_line"]
        function_index = context["function_index"]
        lexical_type = context["lexical_type"]
        load_module_offset = context["load_module_offset"]

        source_file_string = None
        module_string = None
        function_string = None
        file_line = -1
        type = None

        if lexical_type == 1:
            # loop construct
            function_string = "loop"
            type = "loop"
        elif lexical_type == 2:
            type = "line"
        elif lexical_type == 3:
            type = "instruction"
        elif lexical_type == 0:
            type = "function"
        elif function_index is not None:
            # The function map
            function = self.functions_list[function_index]
            # current_function_map = {"string_index": function_name_index, \
            #                         "source_line": source_line,
            #                         "load_modules_index": load_module_index, \
            #                         "source_file_index": source_file_index}

            # getting function name
            function_string = self.common_strings[function["string_index"]]
        else:
            # function is unkown
            function_string = "<unkown function>"

        if load_module_offset is not None:
            load_module_offset = hex(int(load_module_offset))

        if load_module_index is not None:
            load_module = self.load_modules_list[load_module_index]
            module_string = self.common_strings[load_module["string_index"]]
        if source_file_index is not None:
            source_file = self.source_files_list[source_file_index]
            source_file_string = self.common_strings[source_file["string_index"]]
        if function_index is not None:
            function = self.functions_list[function_index]
            function_string = self.common_strings[function["string_index"]]
        if source_file_line is not None:
            file_line = str(source_file_line)
        # print(context)
        return {
            "module": module_string,
            "file": source_file_string,
            "function": function_string,
            "line": file_line,
            "type": type,
            "relation": context["relation"],
            "instruction": load_module_offset,
            # "loop_type": loop_type,
        }

    def __read_common_header(self) -> None:
        """
        Reads common .db file header version 4.0
        """

        # read Magic identifier ("HPCPROF-tracedb_")
        # first ten buyes are HPCTOOLKIT in ASCII
        identifier = str(self.file.read(10), encoding=self.encoding)
        assert identifier == "HPCTOOLKIT"

        # next 4 bytes (u8) are the "Specific format identifier"
        format_identifier = str(self.file.read(4), encoding=self.encoding)
        assert format_identifier == "meta"

        # next byte (u8) contains the "Common major version, currently 4"
        self.major_version = int.from_bytes(
            self.file.read(1), byteorder=self.byte_order, signed=self.signed
        )
        # next byte (u8) contains the "Specific minor version"
        self.minor_version = int.from_bytes(
            self.file.read(1), byteorder=self.byte_order, signed=self.signed
        )

        self.section_pointer = []
        self.section_size = []
        # In the header each section is given 16 bytes:
        #   - First 8 bytes specify the total size of the section (in bytes)
        #   - Last 8 bytes specify a pointer to the beggining of the section
        for i in range(len(self.read_order)):
            self.section_size.append(
                int.from_bytes(
                    self.file.read(8), byteorder=self.byte_order, signed=self.signed
                )
            )
            self.section_pointer.append(
                int.from_bytes(
                    self.file.read(8), byteorder=self.byte_order, signed=self.signed
                )
            )

    def __read_general_properties_section(
        self, section_pointer: int, section_size: int
    ) -> None:
        """Reads the general properties of the trace.
        Sets:

        self.database_title: Title of the database. May be provided by the user.

        self.database_description: Human-readable Markdown description of the database.
        """

        # go to the right spot in the file
        self.file.seek(section_pointer)
        title_pointer = int.from_bytes(
            self.file.read(8), byteorder=self.byte_order, signed=self.signed
        )
        description_pointer = int.from_bytes(
            self.file.read(8), byteorder=self.byte_order, signed=self.signed
        )

        self.database_title = self.__read_string(title_pointer)
        self.database_description = self.__read_string(description_pointer)
        print(self.database_title, self.database_description)

    def __get_common_string(self, string_pointer: int) -> str:
        """Given the file pointer to find string, returns the string."""
        if string_pointer in self.common_string_index_map:
            return self.common_strings[self.common_string_index_map[string_pointer]]
        else:
            return None

    def __read_common_string_table_section(
        self, section_pointer: int, section_size: int
    ) -> None:
        # Let's go to the section
        self.file.seek(section_pointer)

        # We know that this section is just a densely packed list of strings,
        # seperated by the null character
        # So to create a list of these strings, we'll read them all into one string then
        # split them by the null character

        # Reading entire section into a string
        total_section: str = str(self.file.read(section_size), encoding="UTF-8")

        # Splitting entire section into list of strings
        self.common_strings: list[str] = total_section.split("\0")

        # Now we are creating a map between the original location to the string
        # to the index of the string in self.common_strings.
        # This is because we are passed pointers to find the string in other sections
        pointer_index = section_pointer
        # pointer_index = 0
        self.common_string_index_map: dict = {}
        for i in range(len(self.common_strings)):
            self.common_string_index_map[pointer_index] = i
            pointer_index += len(self.common_strings[i]) + 1
        print(self.common_strings)

    def __get_load_modules_index(self, load_module_pointer: int) -> int:
        """
        Given the pointer to where the file would exists in meta.db,
        returns the index of the file in self.source_files_list.
        """
        return (
            load_module_pointer - self.load_modules_pointer
        ) // self.load_module_size

    def __read_load_modules_section(
        self, section_pointer: int, section_size: int
    ) -> None:
        """
        Reads the "Load Modules" Section of meta.db.
        """
        # go to the right spot in meta.db
        self.file.seek(section_pointer)

        # Load modules used in this database
        self.load_modules_pointer = int.from_bytes(
            self.file.read(8), byteorder=self.byte_order, signed=self.signed
        )
        # Number of load modules listed in this section (u32)
        num_load_modules = int.from_bytes(
            self.file.read(4), byteorder=self.byte_order, signed=self.signed
        )
        # Size of a Load Module Specification, currently 16 (u16)
        self.load_module_size = int.from_bytes(
            self.file.read(2), byteorder=self.byte_order, signed=self.signed
        )

        # Going to store file's path in self.load_modules_list.
        # Each will contain the index of file's path string in
        # self.common_string
        self.load_modules_list: list[dict] = []

        for i in range(num_load_modules):
            current_index = self.load_modules_pointer + (i * self.load_module_size)
            self.file.seek(current_index)

            # Flags -- Reserved for future use (u32)
            # flags = int.from_bytes(
            #     self.file.read(4), byteorder=self.byte_order, signed=self.signed
            # )
            self.file.read(4)
            # empty space that we need to skip
            self.file.read(4)
            # Full path to the associated application binary
            path_pointer = int.from_bytes(
                self.file.read(8), byteorder=self.byte_order, signed=self.signed
            )
            module_map = {"string_index": self.common_string_index_map[path_pointer]}
            self.load_modules_list.append(module_map)
        print(self.load_modules_list)

    def __read_string(self, file_pointer: int) -> str:
        """
        Helper function to read a string from the file starting at the file_pointer
        and ending at the first occurence of the null character
        """
        self.file.seek(file_pointer)
        name = ""
        while True:
            read = str(self.file.read(1), encoding="UTF-8")
            if read == "\0":
                break
            name += read
        return name

    def get_identifier_name(self, kind: int):
        """
        returns the identifier name, given the kind
        """
        return self.identifier_names[kind]

    def __read_identifier_names_section(
        self, section_pointer: int, section_size: int
    ) -> None:
        """
        Reads "Identifier Names" Section and Identifier Name strings in self.names_list
        """

        # go to correct section of file
        self.file.seek(section_pointer)

        # Human-readable names for Identifier kinds
        names_pointer_pointer = int.from_bytes(
            self.file.read(8), byteorder=self.byte_order, signed=self.signed
        )
        # Number of names listed in this section
        num_names = int.from_bytes(
            self.file.read(1), byteorder=self.byte_order, signed=self.signed
        )

        self.identifier_names: list[str] = []

        for i in range(num_names):
            self.file.seek(names_pointer_pointer + (i * 8))
            names_pointer = int.from_bytes(
                self.file.read(8), byteorder=self.byte_order, signed=self.signed
            )
            self.identifier_names.append(self.__read_string(names_pointer))
        print(self.identifier_names)

    def __read_performance_metrics_section(
        self, section_pointer: int, section_size: int
    ) -> None:
        pass

    def __get_function_index(self, function_pointer: int) -> int:
        """
        Given the pointer to where the function would exists in meta.db,
        returns the index of the file in self.functions_list.
        """
        index = (function_pointer - self.functions_array_pointer) // self.function_size
        assert index < len(self.functions_list)
        return index

    def __read_functions_section(self, section_pointer: int, section_size: int) -> None:
        """
        Reads the "Functions" section of meta.db.
        """

        # go to correct section in file
        self.file.seek(section_pointer)

        self.functions_array_pointer = int.from_bytes(
            self.file.read(8), byteorder=self.byte_order, signed=self.signed
        )
        num_functions = int.from_bytes(
            self.file.read(4), byteorder=self.byte_order, signed=self.signed
        )
        self.function_size = int.from_bytes(
            self.file.read(2), byteorder=self.byte_order, signed=self.signed
        )

        self.functions_list: list[dict] = []
        for i in range(num_functions):
            current_index = self.functions_array_pointer + (i * self.function_size)
            self.file.seek(current_index)
            function_name_pointer = int.from_bytes(
                self.file.read(8), byteorder=self.byte_order, signed=self.signed
            )
            modules_pointer = int.from_bytes(
                self.file.read(8), byteorder=self.byte_order, signed=self.signed
            )
            modules_offset = int.from_bytes(
                self.file.read(8), byteorder=self.byte_order, signed=self.signed
            )
            file_pointer = int.from_bytes(
                self.file.read(8), byteorder=self.byte_order, signed=self.signed
            )
            source_line = int.from_bytes(
                self.file.read(4), byteorder=self.byte_order, signed=self.signed
            )
            # flags = int.from_bytes(
            #     self.file.read(4), byteorder=self.byte_order, signed=self.signed
            # )
            self.file.read(4)
            source_file_index = None
            load_module_index = None
            function_name_index = None
            if function_name_pointer != 0:
                function_name_index = self.common_string_index_map[
                    function_name_pointer
                ]
            if modules_pointer != 0:
                load_module_index = self.__get_load_modules_index(modules_pointer)
                # currently ignoring offset -- no idea how that's used
            if file_pointer != 0:
                source_file_index = self.__get_source_file_index(file_pointer)

            current_function_map = {
                "string_index": function_name_index,
                "source_line": source_line,
                "load_modules_index": load_module_index,
                "source_file_index": source_file_index,
                "load_modules_offset": modules_offset,
            }
            self.functions_list.append(current_function_map)
        print(self.functions_list)

    def __get_source_file_index(self, source_file_pointer: int) -> int:
        """
        Given the pointer to where the file would exists in meta.db,
        returns the index of the file in self.source_files_list.
        """
        index = (
            source_file_pointer - self.source_files_pointer
        ) // self.source_file_size
        assert index < len(self.source_files_list)
        return index

    def __read_source_files_section(
        self, section_pointer: int, section_size: int
    ) -> None:
        """
        Reads the "Source Files" Section of meta.db.
        """

        self.file.seek(section_pointer)

        # Source files used in this database
        self.source_files_pointer = int.from_bytes(
            self.file.read(8), byteorder=self.byte_order, signed=self.signed
        )

        # Number of source files listed in this section (u32)
        num_files = int.from_bytes(
            self.file.read(4), byteorder=self.byte_order, signed=self.signed
        )

        # Size of a Source File Specification, currently 16 (u16)
        self.source_file_size = int.from_bytes(
            self.file.read(2), byteorder=self.byte_order, signed=self.signed
        )

        # Looping through individual files to get there information now
        self.file.seek(self.source_files_pointer)

        # Going to store file's path in self.files_list.
        # Each will contain the index of file's path string in
        # self.common_string
        self.source_files_list: list[dict] = []
        for i in range(num_files):
            # Reading information about each individual source file
            self.file.seek(self.source_files_pointer + (i * self.source_file_size))

            # flag = int.from_bytes(
            #     self.file.read(4), byteorder=self.byte_order, signed=self.signed
            # )
            self.file.read(4)
            # empty space that we need to skip
            self.file.read(4)
            # Path to the source file. Absolute, or relative to the root database
            # directory. The string pointed to by pPath is completely within the
            # Common String Table section, including the terminating NUL byte.
            file_path_pointer = int.from_bytes(
                self.file.read(8), byteorder=self.byte_order, signed=self.signed
            )
            string_index = self.common_string_index_map[file_path_pointer]
            source_file_map = {"string_index": string_index}
            self.source_files_list.append(source_file_map)
        print(self.source_files_list)

    def __read_context_tree_section(
        self, section_pointer: int, section_size: int
    ) -> None:
        """
        Reads the "Context Tree" section of meta.db.

        Loops and calls __read_single_entry_point with the correct pointer to read
        the correct entry and add it to the CCT.
        """

        self.roots = []
        self.context_map: dict[int, dict] = {}

        # Reading "Context Tree" section header

        # make sure we're in the right spot of the file
        self.file.seek(section_pointer)

        # ({Entry}[nEntryPoints]*)
        entry_points_array_pointer = int.from_bytes(
            self.file.read(8), byteorder=self.byte_order, signed=self.signed
        )
        # (u16)
        num_entry_points = int.from_bytes(
            self.file.read(2), byteorder=self.byte_order, signed=self.signed
        )
        # (u8)
        entry_point_size = int.from_bytes(
            self.file.read(1), byteorder=self.byte_order, signed=self.signed
        )

        for i in range(num_entry_points):
            current_pointer = entry_points_array_pointer + (i * entry_point_size)
            self.__read_single_entry_point(current_pointer)

        graph = Graph(self.roots)
        for node in graph.traverse():
            print(node)

    def __read_single_entry_point(self, entry_point_pointer: int) -> None:
        """
        Reads single (root) context entry.

        Reads the correct entry and adds it to the CCT.
        """

        self.file.seek(entry_point_pointer)

        # Reading information about child contexts
        # Total size of *pChildren (I call pChildren children_pointer), in bytes (u64)
        children_size = int.from_bytes(
            self.file.read(8), byteorder=self.byte_order, signed=self.signed
        )
        # Pointer to the array of child contexts
        children_pointer = int.from_bytes(
            self.file.read(8), byteorder=self.byte_order, signed=self.signed
        )

        # Reading information about this context
        # Unique identifier for this context (u32)
        context_id = int.from_bytes(
            self.file.read(4), byteorder=self.byte_order, signed=self.signed
        )
        # Type of entry point used here (u16)
        # entry_point_type = int.from_bytes(
        #     self.file.read(2), byteorder=self.byte_order, signed=self.signed
        # )
        self.file.read(2)
        # next 2 bytes are blank
        self.file.read(2)
        # Human-readable name for the entry point
        pretty_name_pointer = int.from_bytes(
            self.file.read(8), byteorder=self.byte_order, signed=self.signed
        )

        # map context for this context
        string_index = self.common_string_index_map[pretty_name_pointer]

        context = {
            "relation": -1,
            "lexical_type": -1,
            "function_index": -1,
            "source_file_index": -1,
            "source_file_line": -1,
            "load_module_index": -1,
            "load_module_offset": -1,
            "string_index": string_index,
        }
        # context = {"string_index": string_index}
        self.context_map[context_id] = context
        # Create Node for this context
        print(context_id, self.get_information_from_context_id(context_id))
        node: Node = Node(self._add_context_id(context_id), None)
        # print(node)
        # Adding the Node to the CCT
        self.roots.append(node)
        self.node_map[context_id] = node

        # Reading the children contexts
        self.__read_children_contexts(children_pointer, children_size, node, context_id)

    def __read_children_contexts(
        self,
        context_array_pointer: int,
        total_size: int,
        parent_node: Node,
        parent_context_id: int,
    ) -> None:
        """
        Recursive function to read all child contexts and add it to the CCT
        """

        if total_size <= 0 or context_array_pointer <= 0:
            return
        self.file.seek(context_array_pointer)
        index = 0
        while index < total_size:
            # Reading information about child contexts (as in the children of
            # this context)
            # Total size of *pChildren (I call pChildren children_pointer),
            # in bytes (u64)
            children_size = int.from_bytes(
                self.file.read(8), byteorder=self.byte_order, signed=self.signed
            )
            index += 8
            # Pointer to the array of child contexts
            children_pointer = int.from_bytes(
                self.file.read(8), byteorder=self.byte_order, signed=self.signed
            )
            index += 8

            # Reading information about this context
            # Unique identifier for this context (u32)
            context_id = int.from_bytes(
                self.file.read(4), byteorder=self.byte_order, signed=self.signed
            )
            index += 4
            # Reading flags (u8)
            flags = int.from_bytes(
                self.file.read(1), byteorder=self.byte_order, signed=self.signed
            )
            index += 1
            # Relation this context has with its parent (u8)
            relation = int.from_bytes(
                self.file.read(1), byteorder=self.byte_order, signed=self.signed
            )
            index += 1
            # Type of lexical context represented (u8)
            lexical_type = int.from_bytes(
                self.file.read(1), byteorder=self.byte_order, signed=self.signed
            )
            index += 1
            # Size of flex, in u8[8] "words" (bytes / 8) (u8)
            num_flex_words = int.from_bytes(
                self.file.read(1), byteorder=self.byte_order, signed=self.signed
            )
            index += 1
            # Bitmask for defining propagation scopes (u16)
            # propogation = int.from_bytes(
            #     self.file.read(2), byteorder=self.byte_order, signed=self.signed
            # )
            self.file.read(2)
            index += 2
            # Empty space
            self.file.read(6)
            index += 6

            # reading flex
            flex = self.file.read(8 * num_flex_words)
            index += 8 * num_flex_words

            function_index: int = None
            source_file_index: int = None
            source_file_line: int = None
            load_module_index: int = None
            load_module_offset: int = None

            # flex is u8[8][num_flex],
            # meaning that one flex word is 8 bytes or u64

            # Bit 0: hasFunction. If 1, the following sub-fields of flex are present:
            #   flex[0]: FS* pFunction: Function associated with this context
            if flags & 1 != 0:
                sub_flex = int.from_bytes(
                    flex[0:8], byteorder=self.byte_order, signed=self.signed
                )
                flex = flex[8:]
                function_index = self.__get_function_index(sub_flex)

            # Bit 1: hasSrcLoc. If 1, the following sub-fields of flex are present:
            #   flex[1]: SFS* pFile: Source file associated with this context
            #   flex[2]: u32 line: Associated source line in pFile
            if flags & 2 != 0:
                sub_flex_1 = int.from_bytes(
                    flex[0:8], byteorder=self.byte_order, signed=self.signed
                )
                sub_flex_2 = int.from_bytes(
                    flex[8:10], byteorder=self.byte_order, signed=self.signed
                )
                flex = flex[10:]
                source_file_index = self.__get_source_file_index(sub_flex_1)
                source_file_line = sub_flex_2

            # Bit 2: hasPoint. If 1, the following sub-fields of flex are present:
            #   flex[3]: LMS* pModule: Load module associated with this context
            #   flex[4]: u64 offset: Associated byte offset in *pModule
            if flags & 4 != 0:
                sub_flex_1 = int.from_bytes(
                    flex[0:8], byteorder=self.byte_order, signed=self.signed
                )
                sub_flex_2 = int.from_bytes(
                    flex[8:16], byteorder=self.byte_order, signed=self.signed
                )
                flex = flex[16:]
                load_module_index = self.__get_load_modules_index(sub_flex_1)
                load_module_offset = sub_flex_2

            # Now we take a look at the relationship and type of the context
            if lexical_type == 2 or lexical_type == 3:
                # source line type or single line instruction
                # meaning we don't want to create a node for this
                self.node_map[context_id] = parent_node
                next_parent_node = parent_node

            else:
                # otherwise we do want to create a node
                # Creating Node for this context
                node = Node(self._add_context_id(context_id), parent_node)

                # Connecting this node to the parent node
                parent_node.add_child(node)

                # Adding this node to the graph
                self.node_map[context_id] = node

                if lexical_type == 0:
                    # function call
                    # this means that information about the
                    # source file and module are with the parent
                    parent_information = self.context_map[parent_context_id]
                    if (
                        "string_index" in parent_information
                        and function_index is not None
                    ):
                        # This means that the parent is the root, and it's
                        # information is useless
                        function = self.functions_list[function_index]
                        # Getting source file line
                        source_file_line = function["source_line"]
                        # Getting source file name
                        source_file_index = function["source_file_index"]
                        # Getting Load Module Name
                        load_module_index = function["load_modules_index"]
                        # Getting Load Module Offset

                        load_module_offset = function["load_modules_offset"]
                    else:
                        if source_file_index is None:
                            source_file_index = parent_information["source_file_index"]
                        if source_file_line is None:
                            source_file_line = parent_information["source_file_line"]
                        if load_module_index is None:
                            load_module_index = parent_information["load_module_index"]
                            load_module_offset = parent_information[
                                "load_module_offset"
                            ]
                next_parent_node = node

            # creating a map for this context
            context = {
                "relation": relation,
                "lexical_type": lexical_type,
                "function_index": function_index,
                "source_file_index": source_file_index,
                "source_file_line": source_file_line,
                "load_module_index": load_module_index,
                "load_module_offset": load_module_offset,
            }

            self.context_map[context_id] = context
            print(context_id, self.get_information_from_context_id(context_id))

            # recursively call this function to add more children
            return_address = self.file.tell()
            self.__read_children_contexts(
                children_pointer, children_size, next_parent_node, context_id
            )
            self.file.seek(return_address)


class ProfileReader:
    # class to read self.data from profile.db file

    def __init__(self, file_location, meta_reader):
        # gets the pi_ptr variable to be able to read the identifier tuples
        self.meta_reader: MetaReader = meta_reader

        # open the file to ready in binary mode (rb)
        self.file = open(file_location, "rb")

        # setting necessary read options
        self.byte_order = "little"
        self.signed = False
        self.encoding = "ASCII"

        # The meta.db header consists of the common .db header and n sections.
        # We're going to do a little set up work, so that's easy to change if
        # any revisions change the orders.

        # We're are going to specify 2 maps:
        #   - One dictionary maps the section name to an index
        #       (which follows the order that the sections are seen
        #        in the meta.db header)
        #   - The second dictionary maps the section name to a
        #       function that reads the section. Each function is defined
        #       as __read_<section_name>_section(self, section_pointer: int,
        #       section_size: int) -> None

        # Here I'm mapping the section name to it's order in the meta.db header
        header_map = {"Profiles Information": 0, "Hierarchical Identifier Tuples": 1}

        # Now let's create a function to section map
        reader_map = {
            "Profiles Information": self.__read_profiles_information_section,
            "Hierarchical Identifier Tuples": self.__read_hit_section,
        }
        # Another thing thing that we should consider is the order to read the sections.
        # Here is a list of section references (x -> y means x references y)
        #   - "Profiles Information" -> "Hierarchical Identifier Tuples"
        #
        # Thus we want to keep this order when reading sections:
        # "Profiles Information" -> "Hierarchical Identifier Tuples"
        # Here I'm specifying the order of reading the file
        self.read_order = ["Hierarchical Identifier Tuples", "Profiles Information"]

        # Let's make sure that we include every section in the read order and reader_map
        assert set(self.read_order) == set(header_map) and set(header_map) == set(
            reader_map
        )

        # Now to the actual reading of the meta.db file

        # reading the meta.db header
        self.__read_common_header()

        # now let's read all the sections
        for section_name in self.read_order:
            section_index = header_map[section_name]
            section_pointer = self.section_pointer[section_index]
            section_size = self.section_size[section_index]
            section_reader = reader_map[section_name]
            section_reader(section_pointer, section_size)

    def __read_profiles_information_section(
        self, section_pointer: int, section_size: int
    ) -> None:
        """
        Reads Profile Information section.
        """

        self.file.seek(section_pointer)

        # Description for each profile (u64)
        profiles_pointer = int.from_bytes(
            self.file.read(8), byteorder=self.byte_order, signed=self.signed
        )
        # Number of profiles listed in this section (u32)
        num_profiles = int.from_bytes(
            self.file.read(4), byteorder=self.byte_order, signed=self.signed
        )
        # Size of a {PI} structure, currently 40 (u8)
        profile_size = int.from_bytes(
            self.file.read(1), byteorder=self.byte_order, signed=self.signed
        )

        self.profile_info_list = []

        for i in range(num_profiles):
            file_index = profiles_pointer + (i * profile_size)
            self.file.seek(file_index)
            # Header for the values for this profile
            psvb = self.file.read(0x20)
            # Identifier tuple for this profile
            hit_pointer = int.from_bytes(
                self.file.read(8), byteorder=self.byte_order, signed=self.signed
            )
            # (u32)
            flags = int.from_bytes(
                self.file.read(4), byteorder=self.byte_order, signed=self.signed
            )
            profile_map = {"hit_pointer": hit_pointer, "flags": flags, "psvb": psvb}
            self.profile_info_list.append(profile_map)
            if hit_pointer == 0:
                # this is a summary profile
                self.summary_profile_index = i
        print(self.profile_info_list)

    def get_hit_from_profile(self, index: int) -> list:
        profile = self.profile_info_list[index]
        hit_pointer = profile["hit_pointer"]
        if hit_pointer != 0:
            return self.hit_map[hit_pointer]
        else:
            profile = self.profile_info_list[self.summary_profile_index]
            hit_pointer = profile["hit_pointer"]
            return self.hit_map[hit_pointer]

    def __read_hit_section(self, section_pointer: int, section_size: int) -> None:
        """
        Reads Hierarchical Identifier Tuples section of profile.db
        """
        # let's get to the correct spot in the file
        self.file.seek(section_pointer)

        self.hit_map = {}

        while (self.file.tell() - section_pointer) < section_size:
            # hit pointer
            hit_pointer = self.file.tell()

            # print((self.file.tell() - section_pointer))
            # Number of identifications in this tuple (u16)
            num_tuples = int.from_bytes(
                self.file.read(2), byteorder=self.byte_order, signed=self.signed
            )

            # empty space
            self.file.read(6)

            # Identifications for an application thread
            # Read H.I.T.s
            tuples_list = []
            for i in range(num_tuples):
                # One of the values listed in the meta.db Identifier Names section. (u8)
                kind = int.from_bytes(
                    self.file.read(1), byteorder=self.byte_order, signed=self.signed
                )
                # empty space
                self.file.read(1)
                # flag
                # flags = int.from_bytes(
                #     self.file.read(2), byteorder=self.byte_order, signed=self.signed
                # )
                self.file.read(2)
                # Logical identifier value, may be arbitrary but dense towards 0. (u32)
                # logical_id = int.from_bytes(
                #     self.file.read(4), byteorder=self.byte_order, signed=self.signed
                # )
                self.file.read(4)
                # Physical identifier value, eg. hostid or PCI bus index. (u64)
                physical_id = int.from_bytes(
                    self.file.read(8), byteorder=self.byte_order, signed=self.signed
                )
                identifier_name = self.meta_reader.get_identifier_name(kind)
                tuples_list.append((identifier_name, physical_id))
            self.hit_map[hit_pointer] = tuples_list

    def __read_common_header(self) -> None:
        """
        Reads common .db file header version 4.0
        """

        # read Magic identifier ("HPCPROF-tracedb_")
        # first ten buyes are HPCTOOLKIT in ASCII
        identifier = str(self.file.read(10), encoding=self.encoding)
        assert identifier == "HPCTOOLKIT"

        # next 4 bytes (u8) are the "Specific format identifier"
        format_identifier = str(self.file.read(4), encoding=self.encoding)
        assert format_identifier == "prof"

        # next byte (u8) contains the "Common major version, currently 4"
        self.major_version = int.from_bytes(
            self.file.read(1), byteorder=self.byte_order, signed=self.signed
        )
        # next byte (u8) contains the "Specific minor version"
        self.minor_version = int.from_bytes(
            self.file.read(1), byteorder=self.byte_order, signed=self.signed
        )

        self.section_pointer = []
        self.section_size = []
        # In the header each section is given 16 bytes:
        #   - First 8 bytes specify the total size of the section (in bytes)
        #   - Last 8 bytes specify a pointer to the beggining of the section
        for i in range(len(self.read_order)):
            self.section_size.append(
                int.from_bytes(
                    self.file.read(8), byteorder=self.byte_order, signed=self.signed
                )
            )
            self.section_pointer.append(
                int.from_bytes(
                    self.file.read(8), byteorder=self.byte_order, signed=self.signed
                )
            )


class CCTReader:
    def __init__(
        self, file_location: str, meta_reader: MetaReader, profile_reader: ProfileReader
    ) -> None:
        # open file
        self.file = open(file_location, "rb")
        self.meta_reader = meta_reader
        self.profile_reader = profile_reader

        # setting necessary read options
        self.byte_order = "little"
        self.signed = False
        self.encoding = "ASCII"

        # The trace.db header consists of the common .db header and n sections.
        # We're going to do a little set up work, so that's easy to change if
        # any revisions change the orders.

        # We're are going to specify 2 maps:
        #   - One dictionary maps the section name to an index
        #       (which follows the order that the sections are seen
        #        in the meta.db header)
        #   - The second dictionary maps the section name to a
        #       function that reads the section. Each function is defined
        #       as __read_<section_name>_section(self, section_pointer: int,
        #       section_size: int) -> None

        # Here I'm mapping the section name to it's order in the meta.db header
        header_map = {"Context Headers": 0}

        # Now let's create a function to section map
        reader_map = {"Context Headers": self.__read_cct_info_section}

        # Another thing thing that we should consider is the order to read the sections.
        # Here I'm specifying the order of reading the file
        self.read_order = ["Context Headers"]

        # Let's make sure that we include every section in the read order and reader_map
        assert set(self.read_order) == set(header_map) and set(header_map) == set(
            reader_map
        )

        # Now to the actual reading of the meta.db file

        # reading the meta.db header
        self.__read_common_header()

        # now let's read all the sections
        for section_name in self.read_order:
            section_index = header_map[section_name]
            section_pointer = self.section_pointer[section_index]
            section_size = self.section_size[section_index]
            section_reader = reader_map[section_name]
            section_reader(section_pointer, section_size)

    def __read_common_header(self) -> None:
        """
        Reads common .db file header version 4.0
        """

        # read Magic identifier ("HPCPROF-tracedb_")
        # first ten buyes are HPCTOOLKIT in ASCII
        identifier = str(self.file.read(10), encoding=self.encoding)
        assert identifier == "HPCTOOLKIT"

        # next 4 bytes (u8) are the "Specific format identifier"
        format_identifier = str(self.file.read(4), encoding=self.encoding)
        assert format_identifier == "ctxt"

        # next byte (u8) contains the "Common major version, currently 4"
        self.major_version = int.from_bytes(
            self.file.read(1), byteorder=self.byte_order, signed=self.signed
        )
        # next byte (u8) contains the "Specific minor version"
        self.minor_version = int.from_bytes(
            self.file.read(1), byteorder=self.byte_order, signed=self.signed
        )

        self.section_pointer = []
        self.section_size = []
        # In the header each section is given 16 bytes:
        #   - First 8 bytes specify the total size of the section (in bytes)
        #   - Last 8 bytes specify a pointer to the beggining of the section
        for i in range(len(self.read_order)):
            self.section_size.append(
                int.from_bytes(
                    self.file.read(8), byteorder=self.byte_order, signed=self.signed
                )
            )
            self.section_pointer.append(
                int.from_bytes(
                    self.file.read(8), byteorder=self.byte_order, signed=self.signed
                )
            )

    def __read_cct_info_section(self, section_pointer: int, section_size: int) -> None:
        """
        Reader Context Trace Headers section of trace.db
        """

        # get to the right place in the file
        self.file.seek(section_pointer)

        # Header for each trace (u64)
        context_pointer = int.from_bytes(
            self.file.read(8), byteorder=self.byte_order, signed=self.signed
        )
        # Number of traces listed in this section (u32)
        num_contexts = int.from_bytes(
            self.file.read(4), byteorder=self.byte_order, signed=self.signed
        )
        # Size of a {CI} structure, currently 32
        context_size = int.from_bytes(
            self.file.read(1), byteorder=self.byte_order, signed=self.signed
        )

        # empty space
        self.file.read(4)

        print(context_pointer, num_contexts, context_size)

        for i in range(num_contexts):
            header_pointer = context_pointer + (i * context_size)
            self.__read_single_context_header(header_pointer)

    def __read_single_context_header(self, header_pointer: int) -> None:
        """
        Reads a single context header and all context elements associated with it
        """
        self.file.seek(header_pointer)

        # Header for each trace (u64)
        nonzero_vals = int.from_bytes(
            self.file.read(8), byteorder=self.byte_order, signed=self.signed
        )

        profile_value_pointer = int.from_bytes(
            self.file.read(8), byteorder=self.byte_order, signed=self.signed
        )

        nonempyt_metrics = int.from_bytes(
            self.file.read(2), byteorder=self.byte_order, signed=self.signed
        )

        metrics_values_pointer = int.from_bytes(
            self.file.read(8), byteorder=self.byte_order, signed=self.signed
        )

        self.file.seek(profile_value_pointer)
        print(
            "prof_index",
            int.from_bytes(
                self.file.read(4), byteorder=self.byte_order, signed=self.signed
            ),
        )
        print(
            "value",
            int.from_bytes(
                self.file.read(8), byteorder=self.byte_order, signed=self.signed
            ),
        )

        self.file.seek(metrics_values_pointer)
        print(
            "metric_id",
            int.from_bytes(
                self.file.read(4), byteorder=self.byte_order, signed=self.signed
            ),
        )
        print(
            "start_idx",
            int.from_bytes(
                self.file.read(8), byteorder=self.byte_order, signed=self.signed
            ),
        )

    # def __read_single_trace_header(self, header_pointer: int) -> None:
    #     """
    #     Reads a single trace header and all trace elements associated with it
    #     """
    #     self.file.seek(header_pointer)

    #     # Index of a profile listed in the profile.db (u32)
    #     profile_index = int.from_bytes(
    #         self.file.read(4), byteorder=self.byte_order, signed=self.signed
    #     )
    #     hit = self.profile_reader.get_hit_from_profile(profile_index)

    #     # empty space
    #     self.file.read(4)
    #     # Pointer to the first element of the trace line (array)
    #     start_pointer = int.from_bytes(
    #         self.file.read(8), byteorder=self.byte_order, signed=self.signed
    #     )
    #     # Pointer to the after-end element of the trace line (array)
    #     end_pointer = int.from_bytes(
    #         self.file.read(8), byteorder=self.byte_order, signed=self.signed
    #     )

    #     self.file.seek(start_pointer)

    #     # setting up some variables
    #     last_id = -1  # refers to the previous context id
    #     last_node: Node = None  # refers to the node associated with the last context
    #     context_id: int = -1  # refers to the current context id
    #     current_node: Node = (
    #         None  # refers to the current node associated with the current context id
    #     )

    #     # refers to the least common ancestor between common_node and last_node
    #     common_node: Node = None

    #     while self.file.tell() < end_pointer:
    #         # Timestamp (nanoseconds since epoch)
    #         timestamp = (
    #             int.from_bytes(
    #                 self.file.read(8), byteorder=self.byte_order, signed=self.signed
    #             )
    #             - self.min_time_stamp
    #         )

    #         # Sample calling context id (in experiment.xml)
    #         # can use this to get name of function from experiement.xml
    #         # Procedure tab
    #         context_id = int.from_bytes(
    #             self.file.read(4), byteorder=self.byte_order, signed=self.signed
    #         )

    #         if context_id == last_id:
    #             # nothing changed between samples.
    #             # means we don't have to do anything
    #             continue
    #         elif context_id == 0:
    #             # process is idling
    #             current_node = None
    #         else:
    #             # at a new non-idle context
    #             current_node = self.meta_reader.node_map[context_id]

    #         # First we want to close all the "enter" events from the last sample
    #         # that aren't still running
    #         if last_node is not None:
    #             if current_node is None:
    #                 common_node: Node = None
    #             else:
    #                 common_node: Node = current_node.get_intersection(last_node)

    #             # closing each "enter" column until we reach the common_node
    #             while last_node != common_node:
    #                 curr_ctx_id = self.meta_reader.nid_to_ctx[last_node._pipit_nid]
    #                 context_information = (
    #                     self.meta_reader.get_information_from_context_id(curr_ctx_id)
    #                 )

    #                 self.data["Name"].append(str(context_information["function"]))
    #                 if context_information["loop_type"]:
    #                     self.data["Event Type"].append("Loop Leave")
    #                 else:
    #                     self.data["Event Type"].append("Leave")
    #                 self.data["Timestamp (ns)"].append(timestamp)
    #                 self.data["Process"].append(hit[1][1])
    #                 self.data["Thread"].append(hit[2][1])
    #                 self.data["Host"].append(hit[0][1])
    #                 self.data["Node"].append(last_node)
    #                 self.data["Source File Name"].append(context_information["file"])
    #                 self.data["Source File Line Number"].append(
    #                     context_information["line"]
    #                 )
    #                 self.data["Calling Context ID"].append(curr_ctx_id)

    #                 last_node = last_node.parent
    #         # Now we want to add all the new "enter" events after
    #         # the common_node event
    #         if current_node is not None:
    #             if common_node is None:
    #                 intersect_level = -1
    #             else:
    #                 intersect_level = common_node.get_level()
    #             entry_nodes = current_node.get_node_list(intersect_level)
    #             for i in range(len(entry_nodes)):
    #                 entry_node = entry_nodes[-1 * i - 1]
    #                 curr_ctx_id = self.meta_reader.nid_to_ctx[entry_node._pipit_nid]
    #                 context_information = (
    #                     self.meta_reader.get_information_from_context_id(curr_ctx_id)
    #                 )

    #                 self.data["Name"].append(str(context_information["function"]))
    #                 if context_information["loop_type"]:
    #                     self.data["Event Type"].append("Loop Enter")
    #                 else:
    #                     self.data["Event Type"].append("Enter")
    #                 self.data["Timestamp (ns)"].append(timestamp)
    #                 self.data["Process"].append(hit[1][1])
    #                 self.data["Thread"].append(hit[2][1])
    #                 self.data["Host"].append(hit[0][1])
    #                 self.data["Node"].append(entry_node)
    #                 self.data["Source File Name"].append(context_information["file"])
    #                 self.data["Source File Line Number"].append(
    #                     context_information["line"]
    #                 )
    #                 self.data["Calling Context ID"].append(curr_ctx_id)

    #         last_node = current_node
    #         last_id = context_id

    #     # Now we want to close all the "enter" events from the last sample
    #     current_node = None
    #     timestamp = self.max_time_stamp - self.min_time_stamp
    #     if last_node is not None:
    #         if current_node is None:
    #             common_node: Node = None
    #         else:
    #             common_node: Node = current_node.get_intersection(last_node)

    #         # closing each "enter" column until we reach the common_node
    #         while last_node != common_node:
    #             curr_ctx_id = self.meta_reader.nid_to_ctx[last_node._pipit_nid]
    #             context_information = self.meta_reader.get_information_from_context_id(
    #                 curr_ctx_id
    #             )

    #             self.data["Name"].append(str(context_information["function"]))
    #             if context_information["loop_type"]:
    #                 self.data["Event Type"].append("Loop Leave")
    #             else:
    #                 self.data["Event Type"].append("Leave")
    #             self.data["Timestamp (ns)"].append(timestamp)
    #             self.data["Process"].append(hit[1][1])
    #             self.data["Thread"].append(hit[2][1])
    #             self.data["Host"].append(hit[0][1])
    #             self.data["Node"].append(last_node)
    #             self.data["Source File Name"].append(context_information["file"])
    #             self.data["Source File Line Number"].append(context_information["line"])
    #             self.data["Calling Context ID"].append(curr_ctx_id)
    #             last_node = last_node.parent


class HPCToolkitReaderDB:
    def __init__(self, directory: str) -> None:
        print("\nREAD METADB")
        self.meta_reader: MetaReader = MetaReader(directory + "/meta.db")
        print("\nREAD PROFILEDB")
        self.profile_reader = ProfileReader(directory + "/profile.db", self.meta_reader)
        print("\nREAD CONTEXTDB")
        self.trace_reader = CCTReader(
            directory + "/cct.db", self.meta_reader, self.profile_reader
        )

    def read(self):
        print("end")
