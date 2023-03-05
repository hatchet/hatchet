# Copyright 2021-2023 University of Maryland and other Hatchet Project
# Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import pandas as pd
import hatchet.graphframe
from hatchet.node import Node
from hatchet.graph import Graph
from hatchet.frame import Frame

# Requires pycubexr >= v1.2.0
from pycubexr.parsers.tar_parser import CubexParser
from pycubexr.utils.exceptions import MissingMetricError


class ScorePReader:
    """Read in cubex files generated using Scorep."""

    def __init__(self, filename):
        self.filename = filename
        self.callpath_to_node_dicts = {}
        self.callpath_to_node = {}
        self.inc_metrics = []
        self.exc_metrics = []
        self.list_roots = []
        self.threads_per_rank = 0
        self.multiple_ranks = False
        self.multiple_threads = False

    def create_graph(self, cubex):
        def _create_node_dict(
            node_dict,
            callpath_rank_thread,
            location,
            metric,
            metric_values,
            hatchet_node,
            pycubexr_cnode,
            name,
            begin_line,
            end_line,
            file,
        ):
            """Gets all the related information about a node
            and creates a node dictionary to be added to
            the dataframe"""
            if callpath_rank_thread not in node_dict:
                node_dict[callpath_rank_thread] = {
                    "node": hatchet_node,
                    "name": name,
                    "rank": callpath_rank_thread[1],
                    "thread": callpath_rank_thread[2],
                    "line": begin_line,
                    "end_line": end_line,
                    "file": file,
                }

            # example metrics: 'name', 'visits', 'time', 'min_time',
            # 'max_time', 'bytes_sent', 'bytes_received'.
            metric_name = metric.name
            metric_value = None
            if metric_name == "min_time" or metric_name == "max_time":
                metric_name = "{}{}".format(metric.name, " (inc)")
                # pycubexr stores min and max values in MinValue and MaxValue
                # format. We convert them to float.
                metric_value = metric_values.location_value(
                    pycubexr_cnode, location.id
                ).value
            else:
                # Store the value as it is if it is not MinValue or MaxValue.
                metric_value = metric_values.location_value(pycubexr_cnode, location.id)

            if metric_name != "time" and metric.metric_type == "INCLUSIVE":
                metric_name = "{}{}".format(metric.name, " (inc)")

            node_dict[callpath_rank_thread].update({metric_name: metric_value})

        def _calculate_rank_thread(location):
            """Calculates and returns the rank and thread number using
            the location information stored in Score-P. Location ID is
            a number between 0 and (# of ranks) * (# of threads) - 1.
            Also, checks if multiple ranks or threads exists to be
            able to create the dataframe accordingly."""
            # calculate rank and thread numbers.
            # we should do this calculation for each location.id.
            # location.id is a number from 0 to (# of ranks) * (# of threads) - 1
            rank = location.id // self.threads_per_rank
            # thread number is stored as rank in pyCubexR
            thread = int(location.rank)
            if not self.multiple_ranks and rank != 0:
                self.multiple_ranks = True
            if not self.multiple_threads and thread != 0:
                self.multiple_threads = True
            return (rank, thread)

        def _get_node_info(pycubexr_cnode, node_name, begin_line, end_line, file):
            """Gets the node name, begin and end line, and file info
            of a node from pycubexr."""
            node_name = cubex.get_region(pycubexr_cnode).name
            begin_line = cubex.get_region(pycubexr_cnode).begin
            end_line = cubex.get_region(pycubexr_cnode).end
            file = cubex.get_region(pycubexr_cnode).mod
            return node_name, begin_line, end_line, file

        def _get_callpath_info(pycubexr_cnode, parent_callpath):
            """Gets the callpath information by traversing the
            tree created by pycubexr.
            Checks if callpath of a node is already existing.
            If yes, does not create a new node. Otherwise, creates
            a new node and sets parent-child relationships."""
            node_dict = {}
            parent_node = self.callpath_to_node[parent_callpath]
            node_name, begin_line, end_line, file = None, None, None, None
            node_name, begin_line, end_line, file = _get_node_info(
                pycubexr_cnode, node_name, begin_line, end_line, file
            )
            callpath = parent_callpath + (node_name,)
            callpath_rank_thread = tuple()

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

            # this for loop and try-except statements are taken from
            # pycubexr readme file on github.
            for metric in cubex.get_metrics():
                try:
                    # get metric values for each metric.
                    metric_values = cubex.get_metric_values(metric)
                    for location in cubex.get_locations():
                        # get (callpath, rank, thread) tuple for each rank or thread
                        callpath_rank_thread = (callpath,) + _calculate_rank_thread(
                            location
                        )

                        _create_node_dict(
                            node_dict,
                            callpath_rank_thread,
                            location,
                            metric,
                            metric_values,
                            hatchet_node,
                            pycubexr_cnode,
                            node_name,
                            begin_line,
                            end_line,
                            file,
                        )
                except MissingMetricError:
                    # Ignore missing metrics on Score-P
                    pass

            # Sometimes pyCubexR stores some nodes with the same
            # callpath as different nodes even though the only
            # different is their metric values. Here we check if
            # we have already seen the (callpath, rank, thread) and
            # aggregate their values if we have seen it instead of
            # creating a new node not to get ambigous data error
            # on the dataframe.
            if callpath_rank_thread in self.callpath_to_node_dicts:
                for c_r_t in node_dict.keys():
                    for key, value in node_dict[c_r_t].items():
                        if key in self.inc_metrics or key in self.exc_metrics:
                            self.callpath_to_node_dicts[c_r_t][key] += value
            else:
                self.callpath_to_node_dicts.update(node_dict)

            for child in pycubexr_cnode.get_children():
                _get_callpath_info(child, callpath)

        root = cubex._anchor_result.cnodes[0]
        root_name, root_begin, root_end, root_file = None, None, None, None
        root_name, root_begin, root_end, root_file = _get_node_info(
            root, root_name, root_begin, root_end, root_file
        )

        callpath = (root_name,)
        if callpath not in self.callpath_to_node:
            # Create the root node since it doesn't exist
            root_node = Node(Frame({"name": root_name, "type": "function"}), None)

            # Store callpaths to identify nodes
            self.callpath_to_node[callpath] = root_node
            self.list_roots.append(root_node)
        else:
            # Don't create a new node since it is created earlier
            root_node = self.callpath_to_node.get(callpath)

        node_dict = {}
        # get_locations() gets all the rank/thread information.
        # last location refers to the last thread information.
        # if there are 8 threads, the last one should return 7.
        self.threads_per_rank = int(cubex.get_locations()[-1].rank) + 1
        for metric in cubex.get_metrics():
            try:
                # example metrics: 'name', 'visits', 'time (inc)', 'min_time',
                # 'max_time', 'bytes_sent', 'bytes_received'.
                metric_values = cubex.get_metric_values(metric)
                if metric.name == "min_time" or metric.name == "max_time":
                    self.inc_metrics.append(metric.name + " (inc)")
                else:
                    self.exc_metrics.append(metric.name)

                for location in cubex.get_locations():

                    callpath_rank_thread = (callpath,) + _calculate_rank_thread(
                        location
                    )
                    _create_node_dict(
                        node_dict,
                        callpath_rank_thread,
                        location,
                        metric,
                        metric_values,
                        root_node,
                        root,
                        root_name,
                        root_begin,
                        root_end,
                        root_file,
                    )
            except MissingMetricError:
                # Ignore missing metrics
                pass

        self.callpath_to_node_dicts.update(node_dict)
        for child in root.get_children():
            _get_callpath_info(child, callpath)

        return self.list_roots

    def read(self):
        cubex = CubexParser(self.filename).__enter__()
        # Add all nodes and roots.
        roots = self.create_graph(cubex)
        # Create a graph object once all nodes have been added.
        graph = Graph(roots)
        graph.enumerate_traverse()

        dataframe = pd.DataFrame.from_dict(data=self.callpath_to_node_dicts.values())

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

        default_metric = "time"

        return hatchet.graphframe.GraphFrame(
            graph, dataframe, self.exc_metrics, self.inc_metrics, default_metric
        )
