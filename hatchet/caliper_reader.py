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

        # make list of metric columns
        self.metric_columns = []
        for idx, item in enumerate(self.json_cols_mdata):
            if self.json_cols[idx] != 'rank' and item['is_value'] is True:
                self.metric_columns.append(self.json_cols[idx])


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
                    graph_root = Node(idx, tuple(node_callpath), None)
                    list_roots.append(graph_root)

                    node_dict = {self.nid_col_name: idx, 'name': node_label, 'node': graph_root}
                    self.idx_to_node[idx] = node_dict
                else:
                    parent_hnode = (self.idx_to_node[node['parent']])['node']
                    node_callpath = list(parent_hnode.callpath)
                    node_callpath.append(node_label)
                    hnode = Node(idx, tuple(node_callpath), parent_hnode)
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

        # create a dataframe of metrics from the data section
        self.df_json_data = pd.DataFrame(self.json_data, columns=self.json_cols)

        # map non-numeric columns to their mappings in the nodes section
        for idx, item in enumerate(self.json_cols_mdata):
            if item['is_value'] is False and self.json_cols[idx] != self.nid_col_name:
                if self.json_cols[idx] == 'sourceloc#cali.sampler.pc':
                    # split source file and line number into two columns
                    self.df_json_data['file'] = self.df_json_data[self.json_cols[idx]].apply(lambda x: re.match('(.*):(\d+)', self.json_nodes[x]['label']).group(1))
                    self.df_json_data['line'] = self.df_json_data[self.json_cols[idx]].apply(lambda x: re.match('(.*):(\d+)', self.json_nodes[x]['label']).group(2))
                    self.df_json_data.drop(self.json_cols[idx], axis=1, inplace=True)
                    sourceloc_idx = idx
                else:
                    self.df_json_data[self.json_cols[idx]] = self.df_json_data[self.json_cols[idx]].apply(lambda x: self.json_nodes[x]['label'])

        # since we split sourceloc, we should update json_cols and
        # json_cols_mdata
        if 'sourceloc#cali.sampler.pc' in self.json_cols:
            self.json_cols.pop(sourceloc_idx)
            self.json_cols_mdata.pop(sourceloc_idx)
            self.json_cols.append('file')
            self.json_cols.append('line')
            self.json_cols_mdata.append({'is_value': False})
            self.json_cols_mdata.append({'is_value': False})

        max_nid = self.df_json_data[self.nid_col_name].max()

        if 'line' in self.df_json_data.columns:
            # split nodes that have multiple file:line numbers to have a child
            # each with a unique file:line number
            unique_nodes = self.df_json_data.groupby(self.nid_col_name)
            df_concat = [self.df_json_data]

            for nid, super_node in unique_nodes:
                line_groups = super_node.groupby('line')
                # only need to do something if there are more than one
                # file:line number entries for the node
                if len(line_groups.size()) > 1:
                    sn_hnode = self.idx_to_node[nid]['node']

                    for line, line_group in line_groups:
                        # create the node label
                        file_name = (line_group.head(1))['file'].item()
                        file_name = file_name.rpartition('/')[2]
                        node_label = file_name + ':' + line

                        # create a new hatchet node
                        node_callpath = list(sn_hnode.callpath)
                        node_callpath.append(node_label)
                        max_nid += 1
                        idx = max_nid
                        hnode = Node(idx, tuple(node_callpath), sn_hnode)
                        sn_hnode.add_child(hnode)

                        node_dict = {self.nid_col_name: idx, 'name': node_label, 'node': hnode}
                        self.idx_to_node[idx] = node_dict

                        # change nid of the original node to new node in place
                        for index, row in line_group.iterrows():
                            self.df_json_data.loc[index, 'nid'] = max_nid

                    # add new row for original node
                    node_copy = super_node.head(1).copy()
                    for cols in self.metric_columns:
                        node_copy[cols] = 0
                    df_concat.append(node_copy)

            # concatenate all the newly created dataframes with
            # self.df_json_data
            self.df_fixed_data = pd.concat(df_concat)
        else:
            self.df_fixed_data = self.df_json_data

        # create a dataframe with all nodes in the call graph
        self.df_nodes = pd.DataFrame.from_dict(data=self.idx_to_node.values())

        # add missing intermediate nodes to the df_fixed_data dataframe
        if 'rank' in self.json_cols:
            self.num_ranks = self.df_fixed_data['rank'].max() + 1
            rank_list = range(0, self.num_ranks)

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
            # check if df_nodes row exists in df_fixed_data
            metric_rows = self.df_fixed_data.loc[self.df_fixed_data[self.nid_col_name] == row[self.nid_col_name]]
            if 'rank' not in self.json_cols:
                if metric_rows.empty:
                    # add a single row
                    node_dict = dict(default_metric_dict)
                    node_dict[self.nid_col_name] = row[self.nid_col_name]
                    missing_nodes.append(node_dict)
            else:
                if metric_rows.empty:
                    # add a row per MPI rank
                    for rank in rank_list:
                        node_dict = dict(default_metric_dict)
                        node_dict[self.nid_col_name] = row[self.nid_col_name]
                        node_dict['rank'] = rank
                        missing_nodes.append(node_dict)
                elif len(metric_rows) < self.num_ranks:
                    # add a row for each missing MPI rank
                    present_ranks = metric_rows['rank'].values
                    missing_ranks = [x for x in rank_list if x not in present_ranks]
                    for rank in missing_ranks:
                        node_dict = dict(default_metric_dict)
                        node_dict[self.nid_col_name] = row[self.nid_col_name]
                        node_dict['rank'] = rank
                        missing_nodes.append(node_dict)

        self.df_missing = pd.DataFrame.from_dict(data=missing_nodes)
        self.df_metrics = pd.concat([self.df_fixed_data, self.df_missing])

        # merge the metrics and node dataframes on the idx column
        with self.timer.phase('data frame'):
            dataframe = pd.merge(self.df_metrics, self.df_nodes, on=self.nid_col_name)
            # set the index to be a MultiIndex
            indices = ['node']
            if 'rank' in self.json_cols:
                indices.append('rank')
            dataframe.set_index(indices, drop=False, inplace=True)

        # create list of exclusive and inclusive metric columns
        exc_metrics = []
        inc_metrics = []
        for column in self.metric_columns:
            if '(inc)' in column:
                inc_metrics.append(column)
            else:
                exc_metrics.append(column)

        graph = Graph(list_roots)
        return graph, dataframe, exc_metrics, inc_metrics
