# Copyright 2017-2019 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import re
import os
import glob

import pandas as pd

import yaml as ym
import json

import hatchet.graphframe
from hatchet.node import Node
from hatchet.graph import Graph
from hatchet.frame import Frame
from hatchet.util.timer import Timer


class AscentReader:
    """Read in an Ascent data (yaml or json) file."""

    def __init__(self, dir_name):
        """Read from Ascent data file."""
        self.dir_name = dir_name
        self.filename_ext = ""

        data_files = glob.glob(self.dir_name + "/*.*")
        self.num_data_files = len(data_files)

        self.yaml_data = {}
        self.metric_columns = set()
        self.num_ops = 0
        self.num_ops_all_cyc = 0

        self.node_dicts = []

        self.idx_to_node = {}
        self.node_to_idx = {}

        self.cycle = 0
        self.idx = 0
        self.lidx = 0

        self.timer = Timer()

        # check extension of first glob'ed file
        if isinstance(data_files[0], str):
            _, self.filename_ext = os.path.splitext(data_files[0])

    def create_graph(self, d, list_roots):
        global c

        def _get_child(d, hparent):
            global c
            for k, v in d.items():
                if isinstance(v, dict):
                    node_label = k
                    if "\n" in node_label:
                        node_label = k.rstrip("\n")
                    hnode = Node(
                        frame_obj=Frame({"type": "operation", "name": node_label}),
                        parent=hparent,
                        hnid=c,
                    )
                    hparent.add_child(hnode)

                    node_dict = {"node": hnode, "name": node_label, "nid": c}

                    self.node_dicts.append(node_dict)

                    self.idx_to_node[c] = hnode
                    self.node_to_idx[hnode] = c

                    c += 1
                    _get_child(v, hnode)
                else:
                    continue

            return c

        c = 0
        for k, v in d.items():
            if isinstance(v, dict):
                node_label = k
                if "\n" in node_label:
                    node_label = k.rstrip("\n")
                graph_root = Node(
                    frame_obj=Frame({"type": "cycle", "name": node_label}),
                    parent=None,
                    hnid=c,
                )
                list_roots.append(graph_root)

                self.idx_to_node[c] = graph_root
                self.node_to_idx[graph_root] = c

                node_dict = {"node": graph_root, "name": node_label, "nid": c}

                self.node_dicts.append(node_dict)

                c += 1
                _get_child(v, graph_root)
            else:
                continue

        return list_roots

    # cycle, path, time, device, input_cells, input_domains, ...
    def get_header(self, d):
        """Read single Ascent data file, single cycle only to get unique list
           of metric column headers.
        """

        def _get_child(d):
            for k, v in d.items():
                if isinstance(v, dict):
                    self.num_ops += 1
                    _get_child(v)
                else:
                    self.metric_columns.add(k)

        for k, v in d.items():
            if isinstance(v, dict):
                self.num_ops += 1
                _get_child(v)
            else:
                self.metric_columns.add(k)

    def parse_ascent_data(self, f):
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
                    rows[parent_idx + rank * self.num_ops_all_cyc][k] = v

                    # manually add cycle to each operation, for easier
                    # filtering in dataframe
                    rows[parent_idx + rank * self.num_ops_all_cyc]["cycle"] = self.cycle

        rows = {}
        log = {}
        with open(f, "r") as stream:
            self.lidx = 0
            if self.filename_ext == ".yaml":
                log = ym.safe_load(stream)
                rank = int(re.search(r"(\d+).yaml$", f).group(0).split(".")[0])
            elif self.filename_ext == ".json":
                log = json.load(stream)
                rank = int(re.search(r"(\d+).json$", f).group(0).split(".")[0])

            for k, v in log.items():
                self.cycle = v["cycle"]
                rows[self.idx] = {"rank": rank, "nid": self.lidx}

                self.idx += 1
                self.lidx += 1
                _parse_children(v, rows, f, self.idx_to_node[self.lidx - 1], rank)

        return rows

    def read(self):
        """Read the Ascent data files to extract the calling context tree."""
        data_files = sorted(glob.glob(self.dir_name + "/*.*"))

        # data metrics vary depending on the node (i.e., visualization operation)
        # parse the first cycle in a single data file to get all unique metrics
        with self.timer.phase("get column headers"):
            with open(data_files[0], "r") as stream:
                if self.filename_ext == ".yaml":
                    data = ym.safe_load(stream)
                elif self.filename_ext == ".json":
                    data = json.load(stream)

                for k, v in data.items():
                    self.num_ops += 1
                    self.get_header(v)
                    break

        # read single data file, create graph
        with self.timer.phase("get nodes"):
            list_roots = []
            with open(data_files[0], "r") as stream:
                if self.filename_ext == ".yaml":
                    tmp = ym.safe_load(stream)
                elif self.filename_ext == ".json":
                    tmp = json.load(stream)

                self.create_graph(tmp, list_roots)

        self.num_ops_all_cyc = len(self.idx_to_node)

        with self.timer.phase("read data files"):
            all_rows = {}

            for filename in data_files:
                rows = self.parse_ascent_data(filename)
                all_rows.update(rows)

        with self.timer.phase("graph construction"):
            graph = Graph(list_roots)
            # this will modify the _hatchet_nid in self.idx_to_node and
            # self.node_to_idx
            graph.enumerate_traverse()

        with self.timer.phase("data frame"):
            self.metric_columns.add("rank")

            metrics = pd.DataFrame.from_dict(all_rows, orient="index")
            df_nodes = pd.DataFrame.from_dict(data=self.node_dicts)

            dataframe = pd.merge(metrics, df_nodes, on="nid")
            dataframe.set_index(["node", "rank", "cycle"], inplace=True)

        # create list of exclusive and inclusive metric columns
        exc_metrics = []
        inc_metrics = []
        for column in self.metric_columns:
            if "(inc)" in column:
                inc_metrics.append(column)
            else:
                exc_metrics.append(column)

        print("")
        print(self.timer)
        gf = hatchet.graphframe.GraphFrame(graph, dataframe, exc_metrics, inc_metrics)
        return gf
