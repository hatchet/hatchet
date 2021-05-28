# Copyright 2021 University of Maryland and other Hatchet Project
# Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import re
import os
import glob
import pandas as pd
import hatchet.graphframe
from hatchet.node import Node
from hatchet.graph import Graph
from hatchet.frame import Frame


class TAUReader:
    """Read in a profile generated using TAU."""

    def __init__(self, dirname):
        self.dirname = dirname
        self.node_dicts = []
        self.callpath_to_node = {}
        self.rank_thread_to_data = {}
        self.filepath_to_data = {}
        self.inc_metrics = []
        self.exc_metrics = []
        self.columns = []
        self.multiple_ranks = False
        self.multiple_threads = False

    def create_node_dict(
        self,
        node,
        columns,
        metric_values,
        name,
        filename,
        module,
        start_line,
        end_line,
        rank,
        thread,
    ):
        node_dict = {
            "node": node,
            "rank": rank,
            "thread": thread,
            "name": name,
            "file": filename,
            "module": module,
            "line": start_line,
            "end_line": end_line,
        }
        for i in range(len(metric_values)):
            node_dict[columns[i + 1]] = metric_values[i]
        return node_dict

    def create_graph(self):
        def _create_parent(child_node, parent_callpath):
            """In TAU output, sometimes we see a node as a parent
            in the callpath even though we haven't seen it before
            as a child. In this case, we need to create a parent node
            for the child.

            We can't create a node_dict for the parent because we don't
            know its metric values when we first see it in a callpath.

            Example: a => b => c "<c_metric_values>"
            Here if we don't see b before, we should create it when we create
            c.

            This function recursively creates parent nodes in a callpath
            until it reaches the already existing parent in that callpath.
            """
            parent_node = self.callpath_to_node.get(parent_callpath)

            # Return if arrives to the parent
            # Else create a parent and add parent/child
            if parent_node is not None:
                parent_node.add_child(child_node)
                child_node.add_parent(parent_node)
                return
            else:
                grand_parent_callpath = parent_callpath[:-1]
                parent_info = parent_callpath[-1]
                parent_name = ""

                # Sometimes we see additional information about a function
                # line file, line, module, etc.
                # We just want to have the name and type to create a parent node.
                # type can be [UNWIND] or [SAMPLE].
                if "[{" in parent_info:
                    if " C " in parent_info:
                        # Example: <name> C [{<file>} {<line>}]
                        parent_name = parent_info.split(" C ")[0]
                    elif " [@] " in parent_info:
                        # Example: [UNWIND] <file> [@] <name> [{} {}]
                        parent_name = (
                            "[UNWIND] " + parent_info.split(" [@] ")[1].split()[0]
                        )
                    else:
                        # Example: [<type>] <name> [{} {}]
                        parent_name = parent_info.split(" [")[0]
                else:
                    if " [@] " in parent_info:
                        # Example: [UNWIND] <file> [@] <name> <module>
                        parent_name = (
                            "[UNWIND] " + parent_info.split(" [@] ")[1].split()[0]
                        )
                    else:
                        # Example 1: [<type>] <name> <file>
                        # Example 2: [<type>] <name>
                        # Example 3: <name>
                        dst_info = parent_info.split()
                        if len(dst_info) == 3:
                            parent_name = dst_info[0] + " " + dst_info[1]

                parent_node = Node(
                    Frame({"type": "function", "name": parent_name}), None
                )
                self.callpath_to_node[parent_callpath] = parent_node

                parent_node.add_child(child_node)
                child_node.add_parent(parent_node)
                _create_parent(parent_node, grand_parent_callpath)

        def _construct_column_list(first_rank_filenames):
            """This function constructs columns, exc_metrics, and
            inc_metrics using all metric files of a rank. It gets the
            all metric files of a rank as a tuple and only loads the
            second line (metadata) of these files.
            """
            columns = []
            for file_index in range(len(first_rank_filenames)):
                with open(first_rank_filenames[file_index], "r") as f:
                    # Skip the first line: "192 templated_functions_MULTI_TIME"
                    next(f)
                    # No need to check if the metadata is the same for all metric files.
                    metadata = next(f)

                    # Get first three columns from # Name Calls Subrs Excl Incl ProfileCalls #
                    # ProfileCalls is removed since it is is typically set to 0 and not used.
                    # We only do this once since these column names are the same for all files.
                    if file_index == 0:
                        columns.extend(
                            re.match(r"\#\s(.*)\s\#", metadata).group(1).split(" ")[:-3]
                        )

                    # Example metric_name: "PAPI_L2_TCM"
                    # TODO: Decide if Calls and Subrs should be inc or exc metrics
                    metric_name = re.search(r"<value>(.*?)<\/value>", metadata).group(1)
                    if metric_name == "CPU_TIME" or metric_name == "TIME":
                        metric_name = "time"
                    elif metric_name == "Name":
                        metric_name == "name"
                    columns.extend([metric_name, metric_name + " (inc)"])
                    self.exc_metrics.append(metric_name)
                    self.inc_metrics.append(metric_name + " (inc)")
            return columns

        # dirpath -> returns path of a directory, string
        # dirnames -> returns directory names, list
        # files -> returns filenames in a directory, list
        profile_filenames = []
        for dirpath, dirnames, files in os.walk(self.dirname):
            profiles_in_foler = glob.glob(dirpath + "/profile.*")
            if profiles_in_foler:
                profile_filenames.append(profiles_in_foler)

        # Store all files in a list of tuples.
        # Each tuple stores every metric file of a rank.
        # We process one rank at a time.
        # Example: [(metric1/0.0.0, metric2/0.0.0), (metric1/1.0.0, metric2/1.0.0), ...]
        profile_filenames = list(zip(*profile_filenames))

        # Get column information from the metric files of a rank.
        self.columns = _construct_column_list(profile_filenames[0])

        list_roots = []
        prev_rank, prev_thread = 0, 0
        # Example filenames_per_rank: (metric1/0.0.0, metric1/0.0.0, ...)
        for filenames_per_rank in profile_filenames:
            file_info = filenames_per_rank[0].split(".")
            rank, thread = int(file_info[-3]), int(file_info[-1])
            self.multiple_ranks = True if rank != prev_rank else False
            self.multiple_threads = True if thread != prev_thread else False

            # Load all files represent a different metric for a rank or a thread.
            # If there are 2 metrics, load metric1\profile.0.0.0 and metric2\profile.0.0.0
            file_data = []
            for f_index in range(len(filenames_per_rank)):
                # Store the lines after metadata.
                file_data.append(open(filenames_per_rank[f_index], "r").readlines()[2:])

            # Get the root information from only the first file to compare them
            # with others.
            # Example: ".TAU application" 1 1 272 15755429 0 GROUP="TAU_DEFAULT"
            root_line = re.match(r"\"(.*)\"\s(.*)\sG", file_data[0][0])
            root_name = root_line.group(1).strip(" ")
            # convert it to a tuple to use it as a key in callpath_to_node dictionary
            root_name_tuple = tuple([root_name])
            root_values = list(map(int, root_line.group(2).split(" ")[:-1]))

            # After first profile.0.0.0, only get Excl and Incl metric values
            # from other files since other columns will be the same.
            # We assume each metric file of a rank has the same root.
            first_file_root_name = re.search(r"\"(.*?)\"", file_data[0][0]).group(1)
            for f_index in range(1, len(file_data)):
                root_name = re.search(r"\"(.*?)\"", file_data[f_index][0]).group(1)
                # Below assert statement throws an error if the roots are not the
                # same for different metric files.
                # TODO: We need to find a solution if this throws an error.
                assert first_file_root_name == root_name, (
                    "Metric files for a rank has different roots.\n"
                    + "File: "
                    + filenames_per_rank[f_index]
                    + "\nLine: 2"
                )
                root_line = re.match(r"\"(.*)\"\s(.*)\sG", file_data[f_index][0])
                root_values.extend(list(map(int, root_line.group(2).split(" ")[2:4])))

            # If root doesn't exist
            if root_name_tuple not in self.callpath_to_node:
                # Create the root node since it doesn't exist
                root_node = Node(Frame({"name": root_name, "type": "function"}), None)

                # Store callpaths to identify nodes
                self.callpath_to_node[root_name_tuple] = root_node
                list_roots.append(root_node)
            else:
                # Don't create a new node since it is created earlier
                root_node = self.callpath_to_node.get(root_name_tuple)

            node_dict = self.create_node_dict(
                root_node,
                self.columns,
                root_values,
                root_name,
                None,
                None,
                0,
                0,
                rank,
                thread,
            )
            self.node_dicts.append(node_dict)

            # Start from the line after root.
            # Iterate over only the first metric file of a rank
            # since the lines should be exactly the same across
            # all metric files of a rank.
            # Uses the same "line_index" for other metric files of a rank.
            for line_index in range(1, len(file_data[0])):
                line = file_data[0][line_index]
                metric_values = []
                if "=>" in line:
                    # Example: ".TAU application  => foo()  => bar()" 31 0 155019 155019 0 GROUP="TAU_SAMPLE|TAU_CALLPATH"
                    callpath_line_regex = re.match(r"\"(.*)\"\s(.*)\sG", line)
                    # callpath: ".TAU application  => foo()  => bar()"
                    callpath = [
                        name.strip(" ")
                        for name in callpath_line_regex.group(1).split("=>")
                    ]

                    # Example dst_name: StrToInt [{lulesh-util.cc} {13,1}-{29,1}]
                    dst_name = callpath[-1]
                    dst_file, dst_module = None, None
                    dst_start_line, dst_end_line = 0, 0
                    callpath = tuple(callpath)
                    parent_callpath = callpath[:-1]
                    # Don't include the value for ProfileCalls.
                    # metric_values: 31 0 155019 155019
                    metric_values = list(
                        map(float, callpath_line_regex.group(2).split(" ")[:-1])
                    )

                    # There are several different formats in TAU outputs.
                    # There might be file, line, and module information.
                    # The following if-else block covers all possible output
                    # formats. Example formats are given in comments.
                    if "[{" in dst_name:
                        # Sometimes we see file and module information inside of [{}]
                        # Example 1: [UNWIND] <file> [@] [{<file_or_module>} {<line>}]
                        # Example 2: <name> C [{<file>} {<line>}]
                        # Example 3: [<type>] <name> [{} {}]
                        tmp_module_or_file_line = (
                            re.search(r"\{.*\}\]", dst_name).group(0).split()
                        )
                        dst_line_number = (
                            tmp_module_or_file_line[1].strip("}]").replace("{", "")
                        )
                        if "-" in dst_line_number:
                            # Sometimes there is "-" between start line and end line
                            # Example: {341,1}-{396,1}
                            dst_line_list = dst_line_number.split("-")
                            dst_start_line = int(dst_line_list[0].split(",")[0])
                            dst_end_line = int(dst_line_list[1].split(",")[0])
                        else:
                            if "," in dst_line_number:
                                # Sometimes we don't have "-".
                                # Example: {15,0}
                                dst_start_line = int(dst_line_number.split(",")[0])
                                dst_end_line = int(dst_line_number.split(",")[1])
                        if " C " in dst_name:
                            # Sometimes we see "C" symbol which means it's a C function.
                            # Example: <name> C [{<file>} {<line>}]
                            dst_name = dst_name.split(" C ")[0]
                        elif " [@] " in dst_name:
                            # type is always UNWIND if there is [@] symbol.
                            # Example: [UNWIND] <file> [@] <name> [{} {}]
                            dst_info = dst_name.split(" [@] ")
                            dst_file = dst_info[0].split()[1]
                            dst_name_module = dst_info[1].split(" [{")
                            dst_module = dst_name_module[1].split()[0].strip("}")
                            # Remove file or module if they are the same
                            if dst_module in dst_file:
                                if ".so" in dst_file:
                                    dst_file = None
                                if ".c" in dst_module:
                                    dst_module = None
                            dst_name = "[UNWIND] " + dst_name_module[0]
                        else:
                            # If there isn't "C" or "[@]""
                            # Example: [<type>] <name> [{} {}]
                            dst_info = dst_name.split(" [{")
                            dst_file = dst_info[1].split()[0].strip("}{")
                            dst_name = dst_info[0]
                    else:
                        # If we don't see "[{", there won't be line number info.
                        if " [@] " in dst_name:
                            # Example: [UNWIND] <file> [@] <name> <module>
                            dst_info = dst_name.split(" [@] ")
                            dst_file = dst_info[0].split()[1]
                            dst_name_module = dst_info[1].split()
                            dst_module = dst_name_module[1]
                            # Remove file or module if they are the same
                            if dst_module in dst_file:
                                if ".so" in dst_file:
                                    dst_file = None
                                if ".c" in dst_module:
                                    dst_module = None
                            dst_name = "[UNWIND] " + dst_name_module[0]
                        else:
                            # Example 1: [<type>] <name> <module>
                            # Example 2: [<type>] <name>
                            # Example 3: <name>
                            dst_info = dst_name.split()
                            if len(dst_info) == 3:
                                dst_info = dst_name.split()
                                dst_module = dst_info[2]
                                dst_name = dst_info[0] + " " + dst_info[1]

                    # Example: ".TAU application  => foo()  => bar()" 31 0 155019..."
                    first_file_callpath_line = re.search(
                        r"\"(.*?)\"", file_data[0][line_index]
                    ).group(1)
                    # After first profile.0.0.0, only get Excl and Incl metric values
                    # from other files.
                    for f_index in range(1, len(file_data)):
                        other_file_callpath_line = re.search(
                            r"\"(.*?)\"", file_data[f_index][line_index]
                        ).group(1)
                        # We assume metric files of a rank should have the exact same lines.
                        # Only difference should be the Incl and Excl metric values.
                        # TODO: We should find a solution if this raises an error.
                        assert first_file_callpath_line == other_file_callpath_line, (
                            "Lines across metric files for a rank are not the same.\n"
                            + "File: "
                            + filenames_per_rank[f_index]
                            + "\nLine: "
                            + str(line_index + 3)
                        )
                        # Get the information from the same line in each file. "line_index".
                        callpath_line_regex = re.match(
                            r"\"(.*)\"\s(.*)\sG", file_data[f_index][line_index]
                        )
                        metric_values.extend(
                            map(float, callpath_line_regex.group(2).split(" ")[2:4])
                        )

                    dst_node = self.callpath_to_node.get(callpath)
                    # Check if that node is created earlier
                    if dst_node is None:
                        # Create the node since it doesn't exist
                        dst_node = Node(
                            Frame({"type": "function", "name": dst_name}), None
                        )
                        self.callpath_to_node[callpath] = dst_node

                        # Get its parent from its callpath.
                        parent_node = self.callpath_to_node.get(parent_callpath)
                        if parent_node is None:
                            # Create parent if it doesn't exist.
                            _create_parent(dst_node, parent_callpath)
                        else:
                            parent_node.add_child(dst_node)
                            dst_node.add_parent(parent_node)

                    node_dict = self.create_node_dict(
                        dst_node,
                        self.columns,
                        metric_values,
                        dst_name,
                        dst_file,
                        dst_module,
                        dst_start_line,
                        dst_end_line,
                        rank,
                        thread,
                    )

                    self.node_dicts.append(node_dict)

        return list_roots

    def read(self):
        """Read the TAU profile file to extract the calling context tree."""
        # Add all nodes and roots.
        roots = self.create_graph()
        # Create a graph object once all nodes have been added.
        graph = Graph(roots)
        graph.enumerate_traverse()

        dataframe = pd.DataFrame.from_dict(data=self.node_dicts)

        indices = []
        # Set indices according to rank/thread numbers.
        if self.multiple_ranks and self.multiple_threads:
            indices = ["node", "rank", "thread"]
        elif self.multiple_ranks:
            dataframe.drop(columns=["thread"], inplace=True)
            indices = ["node", "rank"]
        elif self.multiple_threads:
            dataframe.drop(columns=["rank"], inplace=True)
            indices = ["node", "thread"]
        else:
            indices = ["node"]

        dataframe.set_index(indices, inplace=True)
        dataframe.sort_index(inplace=True)

        # Fill the missing ranks
        # After unstacking and iterating over rows, there
        # will be "NaN" values for some ranks. Find the first
        # rank that has notna value and use it for other rows/ranks
        # of the multiindex.
        # TODO: iterrows() is not the best way to iterate over rows.
        if self.multiple_ranks or self.multiple_threads:
            dataframe = dataframe.unstack()
            for idx, row in dataframe.iterrows():

                # There is always a valid name for an index.
                # Take that valid name and assign to other ranks/rows.
                name = row["name"][row["name"].first_valid_index()]
                dataframe.loc[idx, "name"] = name

                # Sometimes there is no file information.
                if row["file"].first_valid_index() is not None:
                    file = row["file"][row["file"].first_valid_index()]
                    dataframe.loc[idx, "file"] = file

                # Sometimes there is no module information.
                if row["module"].first_valid_index() is not None:
                    module = row["module"][row["module"].first_valid_index()]
                    dataframe.loc[idx, "module"] = module

                # Fill the rest with 0
                dataframe.fillna(0, inplace=True)

            # Stack the dataframe
            dataframe = dataframe.stack()

        default_metric = "time (inc)"

        return hatchet.graphframe.GraphFrame(
            graph, dataframe, self.exc_metrics, self.inc_metrics, default_metric
        )
