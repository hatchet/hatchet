# Copyright 2020 University of Maryland and other Hatchet Project
# Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import re

import pandas as pd

import hatchet.graphframe
from ..node import Node
from ..graph import Graph
from ..frame import Frame

# from ..util.timer import Timer


class TauReader:
    """Read in TAU profiling output."""

    def __init__(self, filename):
        self.tau_file = filename  # TODO: it should be dirname.

        self.name_to_hnode = {}
        self.name_to_dict = {}

    def create_graph(self):
        input_file = open(self.tau_file, "r").readlines()

        file_info = self.tau_file.split(".")
        rank = int(file_info[-3])
        thread = int(file_info[-1])

        # columns = re.match(r"\#\s(.*)\s\#", input_file[1]).group(1).split(" ")
        # TODO: store Matric Name <metadata><attribute><name>Metric Name</name><value>TIME</value></attribute>

        # ".TAU application" 1 1 272 15755429 0 GROUP="TAU_DEFAULT"
        root_line = re.match(r"\"(.*)\"\s(.*)\sG", input_file[2])
        root_name = root_line.group(1).strip(" ")
        root_values = list(map(int, root_line.group(2).split(" ")))

        list_roots = []

        # start with the root node
        src_hnode = Node(Frame({"name": root_name, "type": "function"}), None)
        self.name_to_hnode[root_name] = src_hnode
        list_roots.append(src_hnode)

        # create a dict with node properties
        node_dict = {
            "node": src_hnode,
            "rank": rank,  # TODO: Might be removed
            "thread": thread,  # TODO: Might be removed
            "name": root_name,
            "calls": root_values[0],
            "subroutines": root_values[1],
            "time": root_values[2],
            "time (inc)": root_values[3],
            "profile calls": root_values[4],
        }
        self.name_to_dict[root_name] = node_dict

        for line in input_file[3:]:
            if "=>" in line:
                call_line_regex = re.match(r"\"(.*)\"\s(.*)\sG", line)
                call_path = call_line_regex.group(1).split(" => ")
                src_name = call_path[-2].strip(" ")
                dst_name = call_path[-1].strip(" ")
                call_values = list(map(int, call_line_regex.group(2).split(" ")))

                src_hnode = self.name_to_hnode.get(src_name)
                if not src_hnode:
                    # create a node if it doesn't exist yet
                    src_hnode = Node(
                        Frame({"type": "function", "name": src_name}), None
                    )
                    self.name_to_hnode[src_name] = src_hnode
                    list_roots.append(src_hnode)

                dst_hnode = self.name_to_hnode.get(dst_name)
                if not dst_hnode:
                    # create a node if it doesn't exist yet
                    dst_hnode = Node(
                        Frame({"type": "function", "name": dst_name}), src_hnode
                    )
                    self.name_to_hnode[dst_name] = dst_hnode
                # add source node as parent
                dst_hnode.add_parent(src_hnode)

                # add destination node as child
                src_hnode.add_child(dst_hnode)

                # create a dict with node properties
                node_dict = {
                    "node": dst_hnode,
                    "rank": rank,  # TODO: Might be removed
                    "thread": thread,  # TODO: Might be removed
                    "name": dst_name,
                    "calls": call_values[0],
                    "subroutines": call_values[1],
                    "time": call_values[2],
                    "time (inc)": call_values[3],
                    "profile calls": call_values[4],
                }
                self.name_to_dict[dst_name] = node_dict

        return list_roots

    def read(self):
        """Read the TAU profile file to extract the calling context tree."""
        roots = self.create_graph()
        graph = Graph(roots)
        graph.enumerate_traverse()

        dataframe = pd.DataFrame.from_dict(data=list(self.name_to_dict.values()))

        index = ["node"]
        dataframe.set_index(index, inplace=True)
        dataframe.sort_index(inplace=True)

        return hatchet.graphframe.GraphFrame(graph, dataframe, ["time"], ["time (inc)"])
