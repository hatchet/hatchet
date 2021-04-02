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
        self.multiple_ranks = False
        self.multiple_threads = False

    def create_node_dict(self, node, metric_names, metric_values, name, rank, thread):
        node_dict = {
            "node": node,
            "rank": rank,
            "thread": thread,
            "name": name,
        }
        for i in range(len(metric_values)):
            node_dict[metric_names[i + 1]] = metric_values[i]

        return node_dict

    def create_graph(self):

        all_files = []
        profile_files = glob.glob(self.dirname + "/profile.*")

        # check if there are profile files in given directory
        # if not, check subdirectories
        if not profile_files:
            for dirpath, dirnames, files in os.walk(self.dirname):
                profile_files = glob.glob(dirpath + "/profile.*")
                if profile_files:
                    all_files.append(profile_files)
        else:
            all_files.append(profile_files)

        # store all files in a list of tuples
        # Example: [(event1/0.0.0, event2/0.0.0), (event1/1.0.0, event2/1.0.0), ...]
        all_files = list(zip(*all_files))

        list_roots = []
        metrics = []
        prev_rank, prev_thread = 0, 0

        # example files_tuple: (event1/0.0.0, event2/0.0.0)
        for files_tuple in all_files:
            file_data_list = []
            file_info = files_tuple[0].split(".")
            rank, thread = int(file_info[-3]), int(file_info[-1])

            self.multiple_ranks = True if rank != prev_rank else False
            self.multiple_threads = True if thread != prev_thread else False

            # read all files for a rank or thread
            # if there are 4 events, there will be 4 profile.0.0.0
            for f_index in range(len(files_tuple)):
                file_data = open(files_tuple[f_index], "r").readlines()
                file_data_list.append(file_data)

            second_line = file_data_list[0][1]
            # get metrics from this line: # Name Calls Subrs Excl Incl ProfileCalls #
            # ProfileCalls is removed since it is is typically set to 0 and not used.
            metrics.extend(
                re.match(r"\#\s(.*)\s\#", second_line).group(1).split(" ")[:-1]
            )
            # Example metric_type: "CPU_TIME"
            metric_type = re.search(r"<value>(.*?)<\/value>", second_line).group(1)

            # TODO: decide if calls and subrs are excl or incl
            for i in range(len(metrics)):
                metrics[i] = metrics[i]
                if metrics[i] == "Excl":
                    metrics[i] = metric_type
                    self.exc_metrics.append(metrics[i])
                elif metrics[i] == "Incl":
                    metrics[i] = metric_type + " (inc)"
                    self.inc_metrics.append(metrics[i])

            # After first profile.0.0.0, only get Excl and Incl metrics
            for f_index in range(1, len(file_data_list)):
                second_line = file_data_list[f_index][1]

                # Example metric_type: "PAPI_L2_TCM"
                metric_type = re.search(r"<value>(.*?)<\/value>", second_line).group(1)
                self.exc_metrics.append(metric_type)
                self.inc_metrics.append(metric_type + " (inc)")
                metrics.extend([metric_type, metric_type + " (inc)"])

            # Example: ".TAU application" 1 1 272 15755429 0 GROUP="TAU_DEFAULT"
            root_line = re.match(r"\"(.*)\"\s(.*)\sG", file_data_list[0][2])
            root_name = root_line.group(1).strip(" ")
            root_name_tuple = tuple([root_name])
            root_values = list(map(int, root_line.group(2).split(" ")[:-1]))

            # After first profile.0.0.0, only get Excl and Incl metric values
            for f_index in range(1, len(file_data_list)):
                root_line = re.match(r"\"(.*)\"\s(.*)\sG", file_data_list[f_index][2])
                root_values.extend(list(map(int, root_line.group(2).split(" ")[2:4])))

            # if root doesn't exist
            if root_name_tuple not in self.callpath_to_node:
                # create the root node since it doesn't exist
                root_node = Node(Frame({"name": root_name, "type": "function"}), None)

                # store callpaths to identify nodes
                self.callpath_to_node[root_name_tuple] = root_node
                list_roots.append(root_node)
            else:
                # directly create a node dict since the root node is created earlier
                root_node = self.callpath_to_node.get(root_name_tuple)

            node_dict = self.create_node_dict(
                root_node, metrics, root_values, root_name, rank, thread
            )
            self.node_dicts.append(node_dict)

            # start from the line after metadata
            for line_index in range(3, len(file_data_list[0])):
                line = file_data_list[0][line_index]
                metric_values = []
                if "=>" in line:
                    # Example: ".TAU application  => foo()  => bar()" 31 0 155019 155019 0 GROUP="TAU_SAMPLE|TAU_CALLPATH"
                    call_line_regex = re.match(r"\"(.*)\"\s(.*)\sG", line)
                    callpath = [
                        name.strip(" ") for name in call_line_regex.group(1).split("=>")
                    ]
                    dst_name = callpath[-1]
                    callpath = tuple(callpath)
                    parent_callpath = callpath[:-1]
                    metric_values = list(
                        map(float, call_line_regex.group(2).split(" ")[:-1])
                    )

                    # After first profile.0.0.0, only get Excl and Incl metric values
                    for f_index in range(1, len(file_data_list)):
                        call_line_regex = re.match(
                            r"\"(.*)\"\s(.*)\sG", file_data_list[f_index][line_index]
                        )
                        metric_values.extend(
                            map(float, call_line_regex.group(2).split(" ")[2:4])
                        )

                    # dst_node is bar() in the example in line 116
                    dst_node = self.callpath_to_node.get(callpath)
                    # check if that node is created earlier
                    if dst_node is None:
                        # create the node since it doesn't exist
                        dst_node = Node(
                            Frame({"type": "function", "name": dst_name}), None
                        )
                        self.callpath_to_node[callpath] = dst_node

                        # this assumes parent will appear before the child
                        # get its parent from its callpath. foo() is the parent in line 116
                        parent_node = self.callpath_to_node.get(parent_callpath)

                        parent_node.add_child(dst_node)
                        dst_node.add_parent(parent_node)

                    node_dict = self.create_node_dict(
                        dst_node, metrics, metric_values, dst_name, rank, thread
                    )

                    self.node_dicts.append(node_dict)

        return list_roots

    def read(self):
        """Read the TAU profile file to extract the calling context tree."""
        # add all nodes and roots
        roots = self.create_graph()
        # create a graph object once all nodes have been added
        graph = Graph(roots)
        graph.enumerate_traverse()

        dataframe = pd.DataFrame.from_dict(data=self.node_dicts)

        indices = []
        # set indices according to rank/thread numbers
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

        # add rows with 0 values for the missing rows
        # no need to handle if there is only one rank and thread
        # name is taken from the corresponding node for that row
        if (self.multiple_ranks or self.multiple_threads) is not False:
            dataframe = dataframe.unstack().fillna(0).stack()
            dataframe["name"] = dataframe.apply(
                lambda x: x.name[0].frame["name"], axis=1
            )

        default_metric = ""
        if "TIME" in self.exc_metrics:
            default_metric = "TIME"
        else:
            default_metric = "CPU_TIME"

        return hatchet.graphframe.GraphFrame(
            graph, dataframe, self.exc_metrics, self.inc_metrics, default_metric
        )
