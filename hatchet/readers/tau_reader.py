# Copyright 2021 University of Maryland and other Hatchet Project
# Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import re
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
        filenames = glob.glob(self.dirname + "/profile.*")
        list_roots = []
        first_file_info = filenames[0].split(".")
        prev_rank, prev_thread = int(first_file_info[-3]), int(first_file_info[-1])

        # read all files at once
        for filename in filenames:
            # create a dict to store files. "file name" -> "file data"
            file_info = filename.split(".")
            current_rank, current_thread = int(file_info[-3]), int(file_info[-1])
            self.rank_thread_to_data[(current_rank, current_thread)] = open(
                filename, "r"
            ).readlines()
            # check if there are more than one ranks or threads
            if self.multiple_ranks and self.multiple_threads:
                continue
            if prev_rank != current_rank:
                self.multiple_ranks = True
            if prev_thread != current_thread:
                self.multiple_threads = True

        # get metrics from this line: # Name Calls Subrs Excl Incl ProfileCalls #
        metrics = (
            re.match(r"\#\s(.*)\s\#", self.rank_thread_to_data[(0, 0)][1])
            .group(1)
            .split(" ")
        )

        # change the time columns and store inc and exc metrics
        for i in range(len(metrics)):
            metrics[i] = metrics[i].lower()
            if metrics[i] == "excl":
                metrics[i] = "time"
                self.exc_metrics.append(metrics[i])
            elif metrics[i] == "incl":
                metrics[i] = "time (inc)"
                self.inc_metrics.append(metrics[i])

        for rank_thread_tuple, file_data in self.rank_thread_to_data.items():
            rank = rank_thread_tuple[0]
            thread = rank_thread_tuple[1]

            # Example: ".TAU application" 1 1 272 15755429 0 GROUP="TAU_DEFAULT"
            root_line = re.match(r"\"(.*)\"\s(.*)\sG", file_data[2])
            root_name_tuple = tuple([root_line.group(1).strip(" ")])
            root_name = root_line.group(1).strip(" ")
            root_values = list(map(int, root_line.group(2).split(" ")))

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
            for line in file_data[3:]:
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
                        map(float, call_line_regex.group(2).split(" "))
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

        return hatchet.graphframe.GraphFrame(
            graph, dataframe, self.exc_metrics, self.inc_metrics
        )
