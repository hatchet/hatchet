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
import re

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
        self.nid_col_name = 'nid'


    def read_json_sections(self):
        with open(self.file_name) as cali_json:
            json_obj = json.load(cali_json)

        # read various sections of the Caliper JSON file
        self.json_data = json_obj["data"]
        self.json_cols = json_obj["columns"]
        self.json_cols_mdata = json_obj["column_metadata"]
        self.json_nodes = json_obj["nodes"]

        # decide which column to use as the primary path hierarchy
        # first preference to callpath if available
        if 'source.function#callpath.address' in self.json_cols:
            self.path_col_name = 'source.function#callpath.address'
        elif 'path' in self.json_cols:
            self.path_col_name = 'path'
        else:
            sys.exit('No hierarchy column in input file')

    def create_graph(self):
        list_roots = []

        # find nodes in the nodes section that represent the path hierarchy
        for idx, node in enumerate(self.json_nodes):
            node_label = node['label']
            self.idx_to_label[idx] = node_label

            if node['column'] == self.path_col_name:
                if 'parent' not in node:
                    # since this node does not have a parent, this is a root
                    node_callpath = []
                    node_callpath.append(node_label)
                    graph_root = Node(tuple(node_callpath), None)
                    list_roots.append(graph_root)

                    node_dict = {self.nid_col_name: idx, 'name': node_label, 'node': graph_root}
                    self.idx_to_node[idx] = node_dict
                else:
                    parent_hnode = (self.idx_to_node[node['parent']])['node']
                    node_callpath = list(parent_hnode.callpath)
                    node_callpath.append(node_label)
                    hnode = Node(tuple(node_callpath), parent_hnode)
                    parent_hnode.add_child(hnode)

                    node_dict = {self.nid_col_name: idx, 'name': node_label, 'node': hnode}
                    self.idx_to_node[idx] = node_dict

        return list_roots

    def create_graphframe(self):
        """ Read the caliper JSON file to extract the calling context tree.
        """
        with self.timer.phase('read json'):
            self.read_json_sections()

        with self.timer.phase('graph construction'):
            list_roots = self.create_graph()

        # create a dataframe with all nodes in the call graph
        self.df_nodes = pd.DataFrame.from_dict(data=self.idx_to_node.values())

        # change column names
        for idx, item in enumerate(self.json_cols):
            if item == self.path_col_name:
                # this column is just a pointer into the nodes section
                self.json_cols[idx] = self.nid_col_name
            # make other columns consistent with other readers
            if item == 'mpi.rank':
                self.json_cols[idx] = 'rank'
            if item == 'module#cali.sampler.pc':
                self.json_cols[idx] = 'module'
            if item == 'sum#time.duration':
                self.json_cols[idx] = 'time'
            if item == 'inclusive#sum#time.duration':
                self.json_cols[idx] = 'time (inc)'

        # create a dataframe of metrics from the data section
        self.df_samples = pd.DataFrame(self.json_data, columns=self.json_cols)

        # map non-numeric columns to their mappings in the nodes section
        for idx, item in enumerate(self.json_cols_mdata):
            if item['is_value'] is False and self.json_cols[idx] != self.nid_col_name:
                if self.json_cols[idx] == 'sourceloc#cali.sampler.pc':
                    # split source file and line number into two columns
                    self.df_samples['file'] = self.df_samples[self.json_cols[idx]].apply(lambda x: re.match('(.*):(\d+)', self.json_nodes[x]['label']).group(1))
                    self.df_samples['line'] = self.df_samples[self.json_cols[idx]].apply(lambda x: re.match('(.*):(\d+)', self.json_nodes[x]['label']).group(2))
                    self.df_samples.drop(self.json_cols[idx], axis=1, inplace=True)
                else:
                    self.df_samples[self.json_cols[idx]] = self.df_samples[self.json_cols[idx]].apply(lambda x: self.json_nodes[x]['label'])

        # add missing intermediate nodes to the df_samples dataframe
        if 'rank' in self.json_cols:
            self.num_ranks =  self.df_samples['rank'].max() + 1

        # create a standard dict to be used for filling all missing rows
        default_metric_dict = {}
        for idx, item in enumerate(self.json_cols_mdata):
            if self.json_cols[idx] != self.nid_col_name:
                if item['is_value'] is True:
                    default_metric_dict[self.json_cols[idx]] = 0
                else:
                    default_metric_dict[self.json_cols[idx]] = None

        # create a list of dicts, one dict for each missing row
        missing_nodes = []
        for iteridx, row in self.df_nodes.iterrows():
            # check if df_nodes row exists in df_samples
            metric_rows = self.df_samples.loc[self.df_samples[self.nid_col_name] == row[self.nid_col_name]]
            if 'rank' not in self.json_cols:
                if metric_rows.empty:
                    # add a single row
                    node_dict = dict(default_metric_dict)
                    node_dict[self.nid_col_name] = row[self.nid_col_name]
                    missing_nodes.append(node_dict)
            # TODO: implement the else (when there are multiple ranks)

        self.df_missing = pd.DataFrame.from_dict(data=missing_nodes)
        self.df_metrics = pd.concat([self.df_samples, self.df_missing])

        # merge the metrics and node dataframes on the idx column
        with self.timer.phase('data frame'):
            dataframe = pd.merge(self.df_metrics, self.df_nodes, on=self.nid_col_name)
            # set the index to be a MultiIndex
            indices = ['node']
            if 'rank' in self.json_cols:
                indices.append('rank')
            dataframe.set_index(indices, drop=False, inplace=True)

        graph = Graph(list_roots)
        return graph, dataframe
