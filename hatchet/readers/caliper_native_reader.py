# Copyright 2021 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT


import pandas as pd
import os

import caliperreader as cr

import hatchet.graphframe
from hatchet.node import Node
from hatchet.graph import Graph
from hatchet.frame import Frame
from hatchet.util.timer import Timer


class CaliperNativeReader:
    """Read in a native `.cali` file using Caliper's python reader."""

    def __init__(self, filename_or_caliperreader):
        """Read in a native cali with Caliper's python reader.

        Args:
            filename_or_caliperreader (str or CaliperReader): name of a `cali` file OR
                a CaliperReader object
        """
        self.filename_or_caliperreader = filename_or_caliperreader
        self.filename_ext = ""

        self.metric_columns = set()
        self.node_dicts = []

        self.timer = Timer()

        if isinstance(self.filename_or_caliperreader, str):
            _, self.filename_ext = os.path.splitext(filename_or_caliperreader)

    def create_graph(self, ctx="path"):
        list_roots = []
        visited = {}  # map frame to node
        parent_hnode = None

        # find nodes in the nodes section that represent the path hierarchy
        for node in self.filename_or_caliperreader.records:
            metrics = {}
            node_label = ""
            if ctx in node:
                # if it's a list, then it's a callpath
                if isinstance(node[ctx], list):
                    node_label = node[ctx][-1]
                    for i in node.keys():
                        if node[i] == node_label:
                            self.node_type = i
                        elif i != ctx:
                            self.metric_columns.add(i)
                            if (
                                self.filename_or_caliperreader.attribute(
                                    i
                                ).attribute_type()
                                == "double"
                            ):
                                metrics[i] = float(node[i])
                            elif (
                                self.filename_or_caliperreader.attribute(
                                    i
                                ).attribute_type()
                                == "int"
                            ):
                                metrics[i] = int(node[i])
                            elif i == "function":
                                if isinstance(node[i], list):
                                    metrics[i] = node[i][-1]
                                else:
                                    metrics[i] = node[i]
                            else:
                                metrics[i] = node[i]

                    frame = Frame({"type": self.node_type, "name": node_label})
                    parent_frame = None
                    for i in visited.keys():
                        parent_label = node[ctx][-2]
                        if i["name"] == parent_label:
                            parent_frame = i
                            break
                    parent_hnode = visited[parent_frame]

                    hnode = Node(frame, parent_hnode)

                    visited[frame] = hnode

                    node_dict = dict({"name": node_label, "node": hnode}, **metrics)
                    parent_hnode.add_child(hnode)
                    self.node_dicts.append(node_dict)
                # if it's a string, then it's a root
                else:
                    node_label = node[ctx]
                    for i in node.keys():
                        if node[i] == node_label:
                            self.node_type = i
                        else:
                            self.metric_columns.add(i)
                            if (
                                self.filename_or_caliperreader.attribute(
                                    i
                                ).attribute_type()
                                == "double"
                            ):
                                metrics[i] = float(node[i])
                            elif (
                                self.filename_or_caliperreader.attribute(
                                    i
                                ).attribute_type()
                                == "int"
                            ):
                                metrics[i] = int(node[i])
                            elif i == "function":
                                metrics[i] = node[i][-1]
                            else:
                                metrics[i] = node[i]

                    frame = Frame({"type": self.node_type, "name": node_label})

                    # since this node does not have a parent, this is a root
                    graph_root = Node(frame, None)
                    visited[frame] = graph_root
                    list_roots.append(graph_root)

                    node_dict = dict(
                        {"name": node_label, "node": graph_root}, **metrics
                    )
                    self.node_dicts.append(node_dict)
                    parent_hnode = graph_root

        return list_roots

    def read(self):
        """Read the caliper records to extract the calling context tree."""
        if isinstance(self.filename_or_caliperreader, str):
            if self.filename_ext != ".cali":
                raise ValueError("from_caliperreader() needs a .cali file")
            else:
                cali_file = self.filename_or_caliperreader
                self.filename_or_caliperreader = cr.CaliperReader()
                self.filename_or_caliperreader.read(cali_file)

        with self.timer.phase("graph construction"):
            list_roots = self.create_graph()

        # create a graph object once all the nodes have been added
        graph = Graph(list_roots)
        graph.enumerate_traverse()

        dataframe = pd.DataFrame(data=self.node_dicts)

        indices = ["node"]
        if "rank" in dataframe.columns:
            indices.append("rank")
        dataframe.set_index(indices, inplace=True)
        dataframe.sort_index(inplace=True)

        # change column names
        for idx, item in enumerate(dataframe.columns):
            # make other columns consistent with other readers
            if item == "mpi.rank":
                dataframe.columns.values[idx] = "rank"
            if item == "module#cali.sampler.pc":
                dataframe.columns.values[idx] = "module"

        # create list of exclusive and inclusive metric columns
        exc_metrics = []
        inc_metrics = []
        for column in self.metric_columns:
            if "(inc)" in column:
                inc_metrics.append(column)
            else:
                exc_metrics.append(column)

        return hatchet.graphframe.GraphFrame(graph, dataframe, exc_metrics, inc_metrics)
