# Copyright 2017-2020 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import json

import pandas as pd

import hatchet.graphframe
from hatchet.node import Node
from hatchet.graph import Graph
from hatchet.frame import Frame
from hatchet.util.timer import Timer


class HatchetSnapshotReader:
    """Read in a Hatchet snapshot file."""

    def __init__(self, file_name):
        """Read from Hatchet snapshot file."""
        self.file_name = file_name

        self.json_data = {}
        self.json_cols = {}
        self.json_nodes = {}

        self.idx_to_label = {}
        self.idx_to_node = {}

        self.timer = Timer()
        self.nid_col_name = "_hnid"

    def read_json_sections(self):
        with open(self.file_name) as hatchet_json:
            json_obj = json.load(hatchet_json)

        # read various sections of the Hatchet snapshot file
        self.json_data = json_obj["data"]
        self.json_cols = json_obj["columns"]
        self.json_nodes = json_obj["nodes"]

        # make list of metric columns
        self.metric_columns = self.json_cols

    def create_graph(self):
        list_roots = []

        # find nodes in the nodes section that represent the path hierarchy
        for idx, node in enumerate(self.json_nodes):
            node_label = node.get("name")
            self.idx_to_label[idx] = node_label

            # create frame attributes from fields in the node
            frame_dict = {}
            for k, v in node.items():
                if k != "parent":
                    frame_dict[k] = v

            if "parent" not in node:
                # since this node does not have a parent, this is a root
                graph_root = Node(Frame(frame_dict), None)
                list_roots.append(graph_root)

                node_dict = {
                    self.nid_col_name: idx,
                    "name": node_label,
                    "node": graph_root,
                }
                self.idx_to_node[idx] = node_dict
            else:
                parent_hnode = (self.idx_to_node[node["parent"]])["node"]
                hnode = Node(Frame(frame_dict), parent_hnode)
                parent_hnode.add_child(hnode)

                node_dict = {self.nid_col_name: idx, "name": node_label, "node": hnode}
                self.idx_to_node[idx] = node_dict

        return list_roots

    def read(self):
        """ Read the hatchet snapshot file to extract the calling context tree.
        """
        with self.timer.phase("read json"):
            self.read_json_sections()

        with self.timer.phase("graph construction"):
            list_roots = self.create_graph()
            graph = Graph(list_roots)
            graph.enumerate_traverse()

        # create a dataframe of metrics from the data section
        self.df_metrics = pd.DataFrame(self.json_data, columns=self.json_cols)

        # create a dataframe with all nodes in the call graph
        self.df_nodes = pd.DataFrame.from_dict(data=list(self.idx_to_node.values()))

        # remove name filled from node data (use the name column from the metrics
        # dataframe, which is complete (no missing names for the node)
        self.df_nodes.drop(["name"], axis=1, inplace=True)

        with self.timer.phase("data frame"):
            # merge the metrics and node dataframes on the _hnid column
            dataframe = pd.merge(self.df_metrics, self.df_nodes, on=[self.nid_col_name])
            # set the index to be a MultiIndex
            indices = ["node"]
            if "rank" in self.json_cols:
                indices.append("rank")
            # remove _hnid column added in save operation for merging metrics and node
            # dataframes
            dataframe.drop("_hnid", axis=1, inplace=True)
            # set and sort index
            dataframe.set_index(indices, inplace=True)
            dataframe.sort_index(inplace=True)

        # create list of exclusive and inclusive metric columns
        exc_metrics = []
        inc_metrics = []
        for column in self.metric_columns:
            if "(inc)" in column:
                inc_metrics.append(column)
            else:
                exc_metrics.append(column)

        return hatchet.graphframe.GraphFrame(graph, dataframe, exc_metrics, inc_metrics)
