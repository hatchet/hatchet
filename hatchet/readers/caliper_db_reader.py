# Copyright 2017-2020 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import json
import sys
import re
import subprocess
import os

import pandas as pd

import hatchet.graphframe
from hatchet.node import Node
from hatchet.graph import Graph
from hatchet.frame import Frame
from hatchet.util.profiler import Timer
from hatchet.util.executable import which


class CaliperDBReader:
    """Read in a Caliper file (`cali` or split JSON) or file-like object."""

    def __init__(self, json_str):
        """Read from Caliper data reader (JSON).

        Args:
            stream (file-like): an open file object
        """
        self.json_str = json_str

        self.json_data = {}
        self.json_cols = {}
        self.json_cols_mdata = {}
        self.json_nodes = {}

        self.idx_to_label = {}
        self.idx_to_node = {}

        self.timer = Timer()
        self.nid_col_name = "nid"

        self.node_types = ["function", "mpi.function", "loop"]

    def _makelist(elem_or_list):
        if isinstance(elem_or_list, list):
            return elem_or_list
        else:
            return [ elem_or_list ]

    def print_metrics(records, ctx_key='path', metric_key='avg#inclusive#sum#time.duration'):
        for rec in records:
            if ctx_key in rec and metric_key in rec:
                print("  {0}: {1}s".format('/'.join(_makelist(rec[ctx_key])), rec[metric_key]))

    def read_json_sections(self, ctx_key="path", metric_key="avg#inclusive#sum#time.duration"):
#        print(self.json_str)
#        # read various sections of the Caliper JSON file
#        self.json_data = json_obj["data"]
#        self.json_cols = json_obj["columns"]
#        self.json_cols_mdata = json_obj["column_metadata"]
        self.json_nodes = self.json_str
#
#        # decide which column to use as the primary path hierarchy
#        # first preference to callpath if available
#        if "source.function#callpath.address" in self.json_cols:
#            self.path_col_name = "source.function#callpath.address"
#            self.node_type = "function"
#        elif "path" in self.json_cols:
#            self.path_col_name = "path"
#            self.node_type = "region"
#        else:
#            sys.exit("No hierarchy column in input file")
#
#        # remove data entries containing None in `path` column (null in json file)
#        # first, get column where `path` data is
#        # then, parse json_data list of lists to identify lists containing None in
#        # `path` column
#        path_col = self.json_cols.index(self.path_col_name)
#        entries_to_remove = []
#        for sublist in self.json_data:
#            if sublist[path_col] is None:
#                entries_to_remove.append(sublist)
#        # then, remove them from the json_data list
#        for i in entries_to_remove:
#            self.json_data.remove(i)
#
#        # change column names
#        for idx, item in enumerate(self.json_cols):
#            if item == self.path_col_name:
#                # this column is just a pointer into the nodes section
#                self.json_cols[idx] = self.nid_col_name
#            # make other columns consistent with other readers
#            if item == "mpi.rank":
#                self.json_cols[idx] = "rank"
#            if item == "module#cali.sampler.pc":
#                self.json_cols[idx] = "module"
#            if item == "sum#time.duration" or item == "sum#avg#sum#time.duration":
#                self.json_cols[idx] = "time"
#            if (
#                item == "inclusive#sum#time.duration"
#                or item == "sum#avg#inclusive#sum#time.duration"
#            ):
#                self.json_cols[idx] = "time (inc)"
#
        # make list of metric columns
        self.metric_columns = [metric_key]

    def create_graph(self, ctx="path"):
        list_roots = []
        visited = {}
        idx = 0

        # find nodes in the nodes section that represent the path hierarchy
        for node in self.json_nodes:
            node_label = ""
            if ctx in node:
                # if it's a list, then it's a callpath
                if isinstance(node[ctx], list):
                    node_label = node[ctx][-1]
                    for i in node.keys():
                        if i in self.node_types:
                            self.node_type = i
                    visited[node_label] = idx

                    print(node[ctx])
                    print("  node =", node[ctx][-1], "-->", str(idx))

                    if node[ctx][-2] in visited:
                        print("    ", node[ctx][-2], visited[node[ctx][-2]], "add child ^^")
                    else:
                        print("    this shouldn't happen")
                        #print("    parent =", node[ctx][i])

#                    tmp = node[ctx][-2]
#                    print("node=", node[ctx][-1], "-->", idx, "parent=", tmp)
                    #parent_hnode = (self.idx_to_node[node["parent"]])["node"]
                    #hnode = Node(
                    #    Frame({"type": self.node_type, "name": node_label}),
                    #    parent_hnode,
                    #)
                    #parent_hnode.add_child(hnode)

                    #node_dict = {
                    #    self.nid_col_name: idx,
                    #    "name": node_label,
                    #    "node": hnode,
                    #}
                    #self.idx_to_node[idx] = node_dict
                # if it's a string, then it's a root
                else:
                    node_label = node[ctx]
                    for i in node.keys():
                        if i in self.node_types:
                            self.node_type = i
                    print("node=", node[ctx], "-->", idx)

                    # since this node does not have a parent, this is a root
                    graph_root = Node(
                        Frame({"type": self.node_type, "name": node_label}), None
                    )
                    #visited[graph_root] = idx
                    visited[node_label] = idx
                    list_roots.append(graph_root)

                    node_dict = {
                        self.nid_col_name: idx,
                        "name": node_label,
                        "node": graph_root,
                    }
                    self.idx_to_node[idx] = node_dict
                idx += 1

#            if node["column"] == self.path_col_name:
#                if "parent" not in node:
#                    # since this node does not have a parent, this is a root
#                    graph_root = Node(
#                        Frame({"type": self.node_type, "name": node_label}), None
#                    )
#                    list_roots.append(graph_root)
#
#                    node_dict = {
#                        self.nid_col_name: idx,
#                        "name": node_label,
#                        "node": graph_root,
#                    }
#                    self.idx_to_node[idx] = node_dict
#                else:
#                    parent_hnode = (self.idx_to_node[node["parent"]])["node"]
#                    hnode = Node(
#                        Frame({"type": self.node_type, "name": node_label}),
#                        parent_hnode,
#                    )
#                    parent_hnode.add_child(hnode)
#
#                    node_dict = {
#                        self.nid_col_name: idx,
#                        "name": node_label,
#                        "node": hnode,
#                    }
#                    self.idx_to_node[idx] = node_dict

        return list_roots

    def read(self):
        """ Read the caliper JSON file to extract the calling context tree.
        """
        with self.timer.phase("read json"):
            self.read_json_sections()

        with self.timer.phase("graph construction"):
            list_roots = self.create_graph()
#
#        # create a dataframe of metrics from the data section
#        self.df_json_data = pd.DataFrame(self.json_data, columns=self.json_cols)
#
#        # map non-numeric columns to their mappings in the nodes section
#        for idx, item in enumerate(self.json_cols_mdata):
#            if item["is_value"] is False and self.json_cols[idx] != self.nid_col_name:
#                if self.json_cols[idx] == "sourceloc#cali.sampler.pc":
#                    # split source file and line number into two columns
#                    self.df_json_data["file"] = self.df_json_data[
#                        self.json_cols[idx]
#                    ].apply(
#                        lambda x: re.match(
#                            r"(.*):(\d+)", self.json_nodes[x]["label"]
#                        ).group(1)
#                    )
#                    self.df_json_data["line"] = self.df_json_data[
#                        self.json_cols[idx]
#                    ].apply(
#                        lambda x: re.match(
#                            r"(.*):(\d+)", self.json_nodes[x]["label"]
#                        ).group(2)
#                    )
#                    self.df_json_data.drop(self.json_cols[idx], axis=1, inplace=True)
#                    sourceloc_idx = idx
#                else:
#                    self.df_json_data[self.json_cols[idx]] = self.df_json_data[
#                        self.json_cols[idx]
#                    ].apply(lambda x: self.json_nodes[x]["label"])
#
#        # since we split sourceloc, we should update json_cols and
#        # json_cols_mdata
#        if "sourceloc#cali.sampler.pc" in self.json_cols:
#            self.json_cols.pop(sourceloc_idx)
#            self.json_cols_mdata.pop(sourceloc_idx)
#            self.json_cols.append("file")
#            self.json_cols.append("line")
#            self.json_cols_mdata.append({"is_value": False})
#            self.json_cols_mdata.append({"is_value": False})
#
#        max_nid = self.df_json_data[self.nid_col_name].max()
#
#        if "line" in self.df_json_data.columns:
#            # split nodes that have multiple file:line numbers to have a child
#            # each with a unique file:line number
#            unique_nodes = self.df_json_data.groupby(self.nid_col_name)
#            df_concat = [self.df_json_data]
#
#            for nid, super_node in unique_nodes:
#                line_groups = super_node.groupby("line")
#                # only need to do something if there are more than one
#                # file:line number entries for the node
#                if len(line_groups.size()) > 1:
#                    sn_hnode = self.idx_to_node[nid]["node"]
#
#                    for line, line_group in line_groups:
#                        # create the node label
#                        file_path = (line_group.head(1))["file"].item()
#                        file_name = os.path.basename(file_path)
#                        node_label = file_name + ":" + line
#
#                        # create a new hatchet node
#                        max_nid += 1
#                        idx = max_nid
#                        hnode = Node(
#                            Frame(
#                                {"type": "statement", "file": file_path, "line": line}
#                            ),
#                            sn_hnode,
#                        )
#                        sn_hnode.add_child(hnode)
#
#                        node_dict = {
#                            self.nid_col_name: idx,
#                            "name": node_label,
#                            "node": hnode,
#                        }
#                        self.idx_to_node[idx] = node_dict
#
#                        # change nid of the original node to new node in place
#                        for index, row in line_group.iterrows():
#                            self.df_json_data.loc[index, "nid"] = max_nid
#
#                    # add new row for original node
#                    node_copy = super_node.head(1).copy()
#                    for cols in self.metric_columns:
#                        node_copy[cols] = 0
#                    df_concat.append(node_copy)
#
#            # concatenate all the newly created dataframes with
#            # self.df_json_data
#            self.df_fixed_data = pd.concat(df_concat)
#        else:
#            self.df_fixed_data = self.df_json_data
#
#        # create a dataframe with all nodes in the call graph
#        self.df_nodes = pd.DataFrame.from_dict(data=list(self.idx_to_node.values()))
#
#        # add missing intermediate nodes to the df_fixed_data dataframe
#        if "rank" in self.json_cols:
#            self.num_ranks = self.df_fixed_data["rank"].max() + 1
#            rank_list = range(0, self.num_ranks)
#
#        # create a standard dict to be used for filling all missing rows
#        default_metric_dict = {}
#        for idx, item in enumerate(self.json_cols_mdata):
#            if self.json_cols[idx] != self.nid_col_name:
#                if item["is_value"] is True:
#                    default_metric_dict[self.json_cols[idx]] = 0
#                else:
#                    default_metric_dict[self.json_cols[idx]] = None
#
#        # create a list of dicts, one dict for each missing row
#        missing_nodes = []
#        for iteridx, row in self.df_nodes.iterrows():
#            # check if df_nodes row exists in df_fixed_data
#            metric_rows = self.df_fixed_data.loc[
#                self.df_fixed_data[self.nid_col_name] == row[self.nid_col_name]
#            ]
#            if "rank" not in self.json_cols:
#                if metric_rows.empty:
#                    # add a single row
#                    node_dict = dict(default_metric_dict)
#                    node_dict[self.nid_col_name] = row[self.nid_col_name]
#                    missing_nodes.append(node_dict)
#            else:
#                if metric_rows.empty:
#                    # add a row per MPI rank
#                    for rank in rank_list:
#                        node_dict = dict(default_metric_dict)
#                        node_dict[self.nid_col_name] = row[self.nid_col_name]
#                        node_dict["rank"] = rank
#                        missing_nodes.append(node_dict)
#                elif len(metric_rows) < self.num_ranks:
#                    # add a row for each missing MPI rank
#                    present_ranks = metric_rows["rank"].values
#                    missing_ranks = [x for x in rank_list if x not in present_ranks]
#                    for rank in missing_ranks:
#                        node_dict = dict(default_metric_dict)
#                        node_dict[self.nid_col_name] = row[self.nid_col_name]
#                        node_dict["rank"] = rank
#                        missing_nodes.append(node_dict)
#
#        self.df_missing = pd.DataFrame.from_dict(data=missing_nodes)
#        self.df_metrics = pd.concat([self.df_fixed_data, self.df_missing])
#
        # create a graph object once all the nodes have been added
        list_roots = []
        graph = Graph(list_roots)
        graph.enumerate_traverse()
#
#        # merge the metrics and node dataframes on the idx column
#        with self.timer.phase("data frame"):
#            dataframe = pd.merge(self.df_metrics, self.df_nodes, on=self.nid_col_name)
#            # set the index to be a MultiIndex
#            indices = ["node"]
#            if "rank" in self.json_cols:
#                indices.append("rank")
#            dataframe.set_index(indices, inplace=True)
#            dataframe.sort_index(inplace=True)
#
#        # create list of exclusive and inclusive metric columns
        exc_metrics = []
        inc_metrics = []
#        for column in self.metric_columns:
#            if "(inc)" in column:
#                inc_metrics.append(column)
#            else:
#                exc_metrics.append(column)

        dataframe = pd.DataFrame()
        return hatchet.graphframe.GraphFrame(graph, dataframe, exc_metrics, inc_metrics)
