# Copyright 2021 University of Maryland and other Hatchet Project
# Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import pandas as pd
import hatchet.graphframe
from hatchet.node import Node
from hatchet.graph import Graph
from hatchet.frame import Frame
from pycubexr import CubexParser
from pycubexr.utils.exceptions import MissingMetricError


class ScorepReader:
    """Read in cubex files generated using Scorep."""

    def __init__(self, filename):
        self.filename = filename
        self.node_dicts = []
        self.callpath_to_node = {}
        self.inc_metrics = []
        self.exc_metrics = []
        self.columns = []
        self.list_roots = []
        self.threads_per_rank = 0
        self.multiple_ranks = False
        self.multiple_threads = False

    def create_graph(self, cubex):
        def _create_node_dict(
            node_dict,
            callpath,
            location,
            metric,
            metric_values,
            hatchet_node,
            pycubexr_cnode,
            name,
        ):
            # calculate rank and thread numbers.
            # we should do this calculation for each node.
            # location.id is a number from 0 to (# of rank) * (# of threads) - 1
            rank = location.id // self.threads_per_rank
            # thread number is stored as rank in pyCubexR
            thread = int(location.rank)
            if not self.multiple_ranks and rank != 0:
                self.multiple_ranks = True
            if not self.multiple_threads and thread != 0:
                self.multiple_threads = True

            callpath_rank_thread = tuple((callpath, rank, thread))
            if callpath_rank_thread not in node_dict:
                node_dict[callpath_rank_thread] = {
                    "node": hatchet_node,
                    "name": name,
                    "rank": rank,
                    "thread": thread,
                }

            # example metrics: 'name', 'visits', 'time (inc)', 'min_time',
            # 'max_time', 'bytes_sent', 'bytes_received'.
            metric_name = metric.name
            if metric.metric_type == "INCLUSIVE":
                metric_name = "{}{}".format(metric.name, " (inc)")
            node_dict[callpath_rank_thread].update(
                {metric_name: metric_values.location_value(pycubexr_cnode, location.id)}
            )

        def _get_callpath_all_info(pycubexr_cnode, parent_callpath):
            node_dict = {}
            parent_node = self.callpath_to_node[parent_callpath]
            node_name = cubex.get_region(pycubexr_cnode).name
            callpath = parent_callpath + (node_name,)

            if callpath not in self.callpath_to_node:
                # Create the root node since it doesn't exist
                hatchet_node = Node(
                    Frame({"name": node_name, "type": "function"}), None
                )

                # Store callpaths to identify nodes
                self.callpath_to_node[callpath] = hatchet_node
                hatchet_node.add_parent(parent_node)
                parent_node.add_child(hatchet_node)
            else:
                # Don't create a new node since it is created earlier
                hatchet_node = self.callpath_to_node.get(callpath)

            # this for loop, try and except statements are taken from
            # pycubexr readme file on github.
            for metric in cubex.get_metrics():
                try:
                    metric_values = cubex.get_metric_values(metric)
                    for location in cubex.get_locations():
                        _create_node_dict(
                            node_dict,
                            callpath,
                            location,
                            metric,
                            metric_values,
                            hatchet_node,
                            pycubexr_cnode,
                            node_name,
                        )
                except MissingMetricError:
                    # Ignore missing metrics
                    pass

            self.node_dicts.extend(node_dict.values())

            for child in pycubexr_cnode.get_children():
                _get_callpath_all_info(child, callpath)

        root = cubex._anchor_result.cnodes[0]
        root_name = cubex.get_region(root).name
        callpath = tuple()
        if callpath not in self.callpath_to_node:
            # Create the root node since it doesn't exist
            root_node = Node(Frame({"name": root_name, "type": "function"}), None)

            # Store callpaths to identify nodes
            self.callpath_to_node[callpath] = root_node
            self.list_roots.append(root_node)
        else:
            # Don't create a new node since it is created earlier
            root_node = self.callpath_to_node.get(callpath)

        # get_locations() gets all the rank/thread information.
        # last location refers to the last thread information.
        # if there are 8 threads, it should return 7.
        node_dict = {}
        self.threads_per_rank = int(cubex.get_locations()[-1].rank) + 1
        for metric in cubex.get_metrics():
            try:
                # example metrics: 'name', 'visits', 'time (inc)', 'min_time',
                # 'max_time', 'bytes_sent', 'bytes_received'.
                metric_values = cubex.get_metric_values(metric)
                if metric.metric_type == "INCLUSIVE":
                    self.inc_metrics.append(metric.name + " (inc)")
                elif metric.metric_type == "EXCLUSIVE":
                    self.exc_metrics.append(metric.name)

                for location in cubex.get_locations():
                    _create_node_dict(
                        node_dict,
                        callpath,
                        location,
                        metric,
                        metric_values,
                        root_node,
                        root,
                        root_name,
                    )
            except MissingMetricError:
                # Ignore missing metrics
                pass

        self.node_dicts.extend(node_dict.values())

        for child in root.get_children():
            _get_callpath_all_info(child, callpath)

        return self.list_roots

    def read(self):
        cubex = CubexParser(self.filename).__enter__()
        # Add all nodes and roots.
        roots = self.create_graph(cubex)
        # Create a graph object once all nodes have been added.
        graph = Graph(roots)
        graph.enumerate_traverse()

        dataframe = pd.DataFrame.from_dict(data=self.node_dicts)

        indices = []
        # Set indices according to rank/thread numbers.
        if self.multiple_ranks and self.multiple_threads:
            indices = ["node", "rank", "thread"]
        elif self.multiple_ranks:
            dataframe.drop(columns=["thread"], inplace=True)
            indices = ["node", "rank"]
        elif self.multiple_threads:
            dataframe.drop(columns=["rank"], inplace=True)
            indices = ["node", "thread"]
        else:
            indices = ["node"]

        dataframe.set_index(indices, inplace=True)
        dataframe.sort_index(inplace=True)

        # Fill the missing ranks
        # After unstacking and iterating over rows, there
        # will be "NaN" values for some ranks. Find the first
        # rank that has notna value and use it for other rows/ranks
        # of the multiindex.
        # TODO: iterrows() is not the best way to iterate over rows.
        if self.multiple_ranks or self.multiple_threads:
            dataframe = dataframe.unstack()
            for idx, row in dataframe.iterrows():
                # There is always a valid name for an index.
                # Take that valid name and assign to other ranks/rows.
                name = row["name"][row["name"].first_valid_index()]
                dataframe.loc[idx, "name"] = name

                # Fill the rest with 0
                dataframe.fillna(0, inplace=True)

            # Stack the dataframe
            dataframe = dataframe.stack()

        default_metric = "time (inc)"

        return hatchet.graphframe.GraphFrame(
            graph, dataframe, self.exc_metrics, self.inc_metrics, default_metric
        )
