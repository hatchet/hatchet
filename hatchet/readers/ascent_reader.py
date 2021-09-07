# Copyright 2021 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import re
import os
import glob

import pandas as pd
from pandas.api.types import is_numeric_dtype

import yaml as ym
import json

import hatchet.graphframe
from hatchet.node import Node
from hatchet.graph import Graph
from hatchet.frame import Frame
from hatchet.util.timer import Timer


class AscentReader:
    """Read in Ascent data (yaml or json) files."""

    def __init__(self, dir_name):
        """Read from Ascent files (yaml or json).

        Args:
            dir_name (str): name of directory containing Ascent files
        """
        # This is the name of the directory containing Ascent files. The directory
        # contains a set of yaml or json files, one per rank.
        self.dir_name = dir_name
        self.filename_ext = ""

        self.data_files = sorted(glob.glob(self.dir_name + "/*.*"))
        if not self.data_files:
            raise ValueError("from_ascent() cannot find data files")

        # check extension of first glob'ed file
        if isinstance(self.data_files[0], str):
            _, self.filename_ext = os.path.splitext(self.data_files[0])

        self.num_ranks = len(self.data_files)

        self.metric_columns = set()
        self.num_ops_all_ranks = 0

        self.node_dicts = []
        self.callpath_to_node = {}

        self.idx_to_node = {}
        self.node_to_idx = {}

        self.cycle = 0
        self.idx = 0
        self.lidx = 0

        self.global_nid = 0
        self.nnodes_per_rank = 0

        self.default_metric = None
        self.timer = Timer()

    def create_graph(self):
        def _get_child(d, hparent, parent_callpath):
            for k, v in d.items():
                if isinstance(v, dict):
                    node_label = k
                    if "\n" in node_label:
                        node_label = k.rstrip("\n")

                    node_callpath = parent_callpath
                    node_callpath.append(node_label)

                    if tuple(node_callpath) not in self.callpath_to_node:
                        hnode = Node(
                            frame_obj=Frame({"type": "operation", "name": node_label}),
                            parent=hparent,
                            hnid=self.global_nid,
                        )
                        hparent.add_child(hnode)

                        # Store callpaths to identify nodes
                        self.callpath_to_node[tuple(node_callpath)] = hnode

                        node_dict = {
                            "node": hnode,
                            "name": node_label,
                            "nid": self.global_nid,
                        }
                        self.node_dicts.append(node_dict)

                        self.idx_to_node[self.global_nid] = hnode
                        self.node_to_idx[hnode] = self.global_nid

                        self.global_nid += 1
                    else:
                        # Don't create a new node since it already exists
                        hnode = self.callpath_to_node.get(tuple(node_callpath))

                    self.nnodes_per_rank += 1
                    _get_child(v, hnode, node_callpath)
                else:
                    continue

        list_roots = []
        self.global_nid = 0
        for filename in self.data_files:
            with open(filename, "r") as stream:
                if self.filename_ext == ".yaml":
                    df_data = ym.safe_load(stream)
                elif self.filename_ext == ".json":
                    df_data = json.load(stream)

            self.nnodes_per_rank = 0
            for k, v in df_data.items():
                if isinstance(v, dict):
                    node_label = k
                    if "\n" in node_label:
                        node_label = k.rstrip("\n")
                    root_callpath = [node_label]

                    if tuple(root_callpath) not in self.callpath_to_node:
                        # Create the root node if it does not exist
                        graph_root = Node(
                            frame_obj=Frame({"type": "cycle", "name": node_label}),
                            parent=None,
                            hnid=self.global_nid,
                        )

                        # Store callpaths to identify nodes
                        self.callpath_to_node[tuple(root_callpath)] = graph_root
                        list_roots.append(graph_root)

                        node_dict = {
                            "node": graph_root,
                            "name": node_label,
                            "nid": self.global_nid,
                        }
                        self.node_dicts.append(node_dict)

                        self.idx_to_node[self.global_nid] = graph_root
                        self.node_to_idx[graph_root] = self.global_nid

                        self.global_nid += 1
                    else:
                        # Don't create a new node since it already exists
                        graph_root = self.callpath_to_node.get(tuple(root_callpath))

                    self.nnodes_per_rank += 1
                    _get_child(v, graph_root, list(root_callpath))
                else:
                    continue

        # Find the total number of nodes across all ranks
        if self.nnodes_per_rank > self.num_ops_all_ranks:
            self.num_ops_all_ranks = self.nnodes_per_rank

        return list_roots

    def get_header(self, data):
        """Read single Ascent file, single cycle only to get unique list
        of metric column headers (e.g., cycle, path, time, device, input_cells).

        Args:
          data (dict): dictionary of metric data
        """

        def _get_child(d):
            for k, v in d.items():
                if isinstance(v, dict):
                    _get_child(v)
                else:
                    self.metric_columns.add(k)

        for k, v in data.items():
            if isinstance(v, dict):
                _get_child(v)
            else:
                self.metric_columns.add(k)

        self.metric_columns.add("rank")

    def parse_ascent_data(self, fname):
        """Read each Ascent file, storing header and value for each node and
        each rank.

        Args:
          fname (str): name of single Ascent file

        Return:
          row (dict): for each node on a single rank, create dict of column name
            and metric value
        """

        def _parse_children(node_list, rows, f, hparent, rank):
            for k, v in node_list.items():
                if isinstance(v, dict):
                    temp = self.idx_to_node[self.lidx]

                    rows[self.idx] = {"rank": rank, "nid": self.node_to_idx[temp]}
                    self.idx += 1
                    self.lidx += 1
                    _parse_children(v, rows, f, temp, rank)
                else:
                    parent_idx = self.node_to_idx[hparent]
                    rows[parent_idx][k] = v

                    # manually add cycle to each operation, for easier
                    # filtering in dataframe
                    rows[parent_idx]["cycle"] = self.cycle

        rows = {}
        log = {}
        with open(fname, "r") as stream:
            self.lidx = 0
            self.idx = 0
            if self.filename_ext == ".yaml":
                log = ym.safe_load(stream)
                rank = int(re.search(r"(\d+).yaml$", fname).group(0).split(".")[0])
            elif self.filename_ext == ".json":
                log = json.load(stream)
                rank = int(re.search(r"(\d+).json$", fname).group(0).split(".")[0])

            for k, v in log.items():
                self.cycle = v["cycle"]
                rows[self.idx] = {"nid": self.lidx, "rank": rank}

                self.idx += 1
                self.lidx += 1

                _parse_children(v, rows, fname, self.idx_to_node[self.lidx - 1], rank)

        return rows

    def read(self):
        """Read the Ascent data to extract the calling context tree.

        Return:
            (GraphFrame): new GraphFrame with HPCToolkit data.
        """

        # Data metrics vary depending on the node (i.e., visualization operation)
        # Parse the first cycle in a single data file to get all unique metrics
        with self.timer.phase("get column headers"):
            with open(self.data_files[0], "r") as stream:
                if self.filename_ext == ".yaml":
                    df_data = ym.safe_load(stream)
                elif self.filename_ext == ".json":
                    df_data = json.load(stream)

                for _, v in df_data.items():
                    self.get_header(v)
                    break

        with self.timer.phase("graph construction"):
            list_roots = self.create_graph()

        all_metric_data = []
        with self.timer.phase("read data files"):
            for filename in self.data_files:
                rows = self.parse_ascent_data(filename)
                per_rank_data = pd.DataFrame.from_dict(rows, orient="index")
                all_metric_data.append(per_rank_data)

        self.df_fixed_data = pd.concat(all_metric_data)

        graph = Graph(list_roots)
        graph.enumerate_traverse()

        # Create a dataframe with all nodes in the call graph
        df_nodes = pd.DataFrame.from_dict(data=self.node_dicts)

        numeric_columns = []
        for col in self.df_fixed_data.columns:
            if is_numeric_dtype(self.df_fixed_data[col]):
                numeric_columns.append(col)

        # Create a standard dict to be used for filling all missing rows
        default_metric_dict = {}
        for idx, col in enumerate(list(self.metric_columns)):
            if col in numeric_columns:
                default_metric_dict[list(self.metric_columns)[idx]] = 0
            else:
                default_metric_dict[list(self.metric_columns)[idx]] = None

        # Create a list of dicts, one dict for each missing row
        missing_nodes = []
        rank_list = range(0, self.num_ranks)
        for iteridx, row in df_nodes.iterrows():
            # check if number of rows for a given nid is equal to number of ranks
            metric_rows = self.df_fixed_data.loc[
                self.df_fixed_data["nid"] == row["nid"]
            ]
            if metric_rows.empty:
                # add a row per MPI rank
                for rank in rank_list:
                    node_dict = dict(default_metric_dict)
                    node_dict["nid"] = row["nid"]
                    node_dict["rank"] = rank
                    missing_nodes.append(node_dict)
            elif len(metric_rows) < self.num_ranks:
                # add a row for each missing MPI rank
                present_ranks = metric_rows["rank"].values
                missing_ranks = [x for x in rank_list if x not in present_ranks]
                for rank in missing_ranks:
                    node_dict = dict(default_metric_dict)
                    for idx, item in enumerate(list(self.metric_columns)):
                        if item in numeric_columns:
                            continue
                        else:
                            node_dict[list(self.metric_columns)[idx]] = row[
                                list(self.metric_columns)[idx]
                            ]
                    node_dict["nid"] = row["nid"]
                    node_dict["rank"] = rank
                    missing_nodes.append(node_dict)

        df_missing = pd.DataFrame.from_dict(data=missing_nodes)
        df_metrics = pd.concat([self.df_fixed_data, df_missing])

        # Merge the metrics and node dataframes on the nid column
        with self.timer.phase("data frame"):
            dataframe = pd.merge(df_metrics, df_nodes, on="nid")
            dataframe.set_index(["node", "rank"], inplace=True)
            dataframe.sort_index(inplace=True)

        # create list of exclusive and inclusive metric columns
        exc_metrics = ["time"]
        inc_metrics = []

        # set the default metric
        if self.default_metric is None:
            if "time" in exc_metrics or "time" in inc_metrics:
                self.default_metric = "time"
            elif len(exc_metrics) > 0:
                self.default_metric = exc_metrics[0]
            elif len(inc_metrics) > 0:
                self.default_metric = inc_metrics[0]

        return hatchet.graphframe.GraphFrame(
            graph, dataframe, exc_metrics, inc_metrics, self.default_metric
        )
