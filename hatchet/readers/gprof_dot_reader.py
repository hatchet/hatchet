# Copyright 2017-2019 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import re

import pandas as pd
import pydot

import hatchet.graphframe
from ..node import Node
from ..graph import Graph
from ..frame import Frame
from ..util.timer import Timer
from ..util.config import dot_keywords


class GprofDotReader:
    """Read in gprof/callgrind output in dot format generated by gprof2dot."""

    def __init__(self, filename):
        self.dotfile = filename

        self.name_to_hnode = {}
        self.name_to_dict = {}

        self.timer = Timer()

    def create_graph(self):
        """Read the DOT files to create a graph."""
        graphs = pydot.graph_from_dot_file(self.dotfile, encoding="utf-8")

        for graph in graphs:
            for edge in graph.get_edges():
                src_name = edge.get_source().strip('"')
                dst_name = edge.get_destination().strip('"')

                src_hnode = self.name_to_hnode.get(src_name)
                if not src_hnode:
                    # create a node if it doesn't exist yet
                    src_hnode = Node(
                        Frame({"type": "function", "name": src_name}), None
                    )
                    self.name_to_hnode[src_name] = src_hnode

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

            for node in graph.get_nodes():
                node_name = node.get_name()

                if node_name not in dot_keywords:
                    node_name = node_name.strip('"')
                    hnode = self.name_to_hnode.get(node_name)
                    if not hnode:
                        # create a node if it doesn't exist yet
                        hnode = Node(
                            Frame({"type": "function", "name": node_name}), None
                        )
                        self.name_to_hnode[node_name] = hnode

                    node_label = node.obj_dict["attributes"].get("label").strip('"')

                    module, _, inc, exc, _ = node_label.split(r"\n")

                    inc_time = float(re.sub(r"\%", "", inc))
                    exc_time = float(re.sub(r"[\(\%\)]", "", exc))

                    # create a dict with node properties
                    node_dict = {
                        "module": module,
                        "name": node_name,
                        "time (inc)": inc_time,
                        "time": exc_time,
                        "node": hnode,
                    }
                    self.name_to_dict[node_name] = node_dict

        # add all nodes with no parents to the list of roots
        list_roots = []
        for (key, val) in self.name_to_hnode.items():
            if not val.parents:
                list_roots.append(val)

        return list_roots

    def read(self):
        """Read the DOT file generated by gprof2dot to create a graphframe. The DOT file
        contains a call graph.
        """
        with self.timer.phase("graph construction"):
            roots = self.create_graph()
            graph = Graph(roots)
            graph.enumerate_traverse()

        with self.timer.phase("data frame"):
            dataframe = pd.DataFrame.from_dict(data=list(self.name_to_dict.values()))
            index = ["node"]
            dataframe.set_index(index, inplace=True)
            dataframe.sort_index(inplace=True)

        return hatchet.graphframe.GraphFrame(graph, dataframe, ["time"], ["time (inc)"])
