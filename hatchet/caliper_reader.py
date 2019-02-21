##############################################################################
# Copyright (c) 2017-2019, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# This file is part of Hatchet.
# Created by Abhinav Bhatele <bhatele@llnl.gov>.
# LLNL-CODE-741008. All rights reserved.
#
# For details, see: https://github.com/LLNL/hatchet
# Please also read the LICENSE file for the MIT License notice.
##############################################################################
import json
import pandas as pd
import sys

from .node import Node
from .graph import Graph
from .util.timer import Timer


class CaliperReader:
    """ Read in a Caliper split JSON file.
    """

    def __init__(self, file_name):
        self.file_name = file_name

        self.json_data = {}
        self.json_cols = {}
        self.json_cols_mdata = {}
        self.json_nodes = {}

        self.idx_to_label = {}
        self.idx_to_node = {}

        self.timer = Timer()

    def read_json_sections(self):
        with open(self.file_name) as cali_json:
            json_obj = json.load(cali_json)

        self.json_data = json_obj["data"]
        self.json_cols = json_obj["columns"]
        self.json_cols_mdata = json_obj["column_metadata"]
        self.json_nodes = json_obj["nodes"]

        if 'source.function#callpath.address' in self.json_cols:
            self.path_col_name = 'source.function#callpath.address'
        elif 'path' in self.json_cols:
            self.path_col_name = 'path'
        else:
            sys.exit('No hierarchy column in input file')

    def create_graph(self):
        # find the first node in the nodes section that is a
        # source.function#callpath.address or path
        for idx, node in enumerate(self.json_nodes):
            node_label = node['label']
            self.idx_to_label[idx] = node_label

            if node['column'] == self.path_col_name:
                if 'parent' not in node:
                    # this is the root
                    node_callpath = []
                    node_callpath.append(node_label)
                    graph_root = Node(tuple(node_callpath), None)
                    node_dict = {'idx': idx, 'name': node_label, 'node': graph_root}
                    self.idx_to_node[idx] = node_dict
                else:
                    parent_hnode = (self.idx_to_node[node['parent']])['node']
                    node_callpath = list(parent_hnode.callpath)
                    node_callpath.append(node_label)
                    hnode = Node(tuple(node_callpath), parent_hnode)
                    parent_hnode.add_child(hnode)

                    node_dict = {'idx': idx, 'name': node_label, 'node': hnode}
                    self.idx_to_node[idx] = node_dict

        return graph_root

    def create_graphframe(self):
        """ Read the caliper JSON file to extract the calling context tree.
        """
        with self.timer.phase('read json'):
            self.read_json_sections()

        with self.timer.phase('graph construction'):
            graph_root = self.create_graph()

        self.df_nodes = pd.DataFrame.from_dict(data=self.idx_to_node.values())

        for idx, item in enumerate(self.json_cols):
            if item == self.path_col_name:
                self.json_cols[idx] = 'idx'
            if item == 'mpi.rank':
                self.json_cols[idx] = 'rank'

        self.df_metrics = pd.DataFrame(self.json_data, columns=self.json_cols)

        with self.timer.phase('data frame'):
            dataframe = pd.merge(self.df_metrics, self.df_nodes, on='idx')
            # set the index to be a MultiIndex
            indices = ['node', 'rank']
            dataframe.set_index(indices, drop=False, inplace=True)

        graph = Graph([graph_root])
        return graph, dataframe
