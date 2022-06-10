# Copyright 2017-2021 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import re
import json
import pandas as pd

import hatchet.graphframe
from hatchet.node import Node
from hatchet.graph import Graph
from hatchet.frame import Frame


class LiteralReader:
    """Create a GraphFrame from a list of dictionaries.

    TODO: calculate inclusive metrics automatically.

    Example:

    .. code-block:: console

        dag_ldict = [
            {
                "frame": {"name": "A", "type": "function"},
                "metrics": {"time (inc)": 30.0, "time": 0.0},
                "children": [
                    {
                        "frame": {"name": "B",  "type": "function"},
                        "metrics": {"time (inc)": 11.0, "time": 5.0},
                        "children": [
                            {
                                "frame": {"name": "C", "type": "function"},
                                "metrics": {"time (inc)": 6.0, "time": 5.0},
                                "children": [
                                    {
                                        "frame": {"name": "D", "type": "function"},
                                        "metrics": {"time (inc)": 1.0, "time": 1.0},
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "frame": {"name": "E", "type": "function"},
                        "metrics": {"time (inc)": 19.0, "time": 10.0},
                        "children": [
                            {
                                "frame": {"name": "H", "type": "function"},
                                "metrics": {"time (inc)": 9.0, "time": 9.0}
                            }
                        ],
                    },
                ],
            }
        ]

    Return:
        (GraphFrame): graphframe containing data from dictionaries
    """

    def __init__(self, list_of_filenames_or_dicts):
        """Read from list of dictionaries.

        graph_dict (dict): List of dictionaries encoding nodes.
        """
        self.filenames = []
        self.list_of_dicts = []
        self.num_ranks = 1

        self.list_roots = []
        self.node_dicts = []
        self.frame_to_node_dict = {}
        self.seen_nids = []

        self.exc_metrics = []
        self.inc_metrics = []

        if isinstance(list_of_filenames_or_dicts[0], str):
            self.filenames = list_of_filenames_or_dicts
            self.num_ranks = len(self.filenames)
        else:
            self.list_of_dicts = list_of_filenames_or_dicts
            # TODO: fix for multi-process data
            self.num_ranks = 1

    def parse_node_literal(self, child_dict, hparent):
        """Create node_dict for one node and then call the function
        recursively on all children.
        """

        # pull out _hatchet_nid if it exists
        # so it will not be inserted into
        # dataframe like a normal metric
        hnid = -1
        if "_hatchet_nid" in child_dict["metrics"]:
            hnid = child_dict["metrics"]["_hatchet_nid"]

        frame = Frame(child_dict["frame"])
        if (hnid != -1 and hnid not in self.seen_nids) or (hnid == -1 and frame not in self.frame_to_node_dict):
            hnode = Node(frame, hparent, hnid=hnid)
            self.frame_to_node_dict[frame] = hnode

            # depending on the node type, the name may not be in the frame
            node_name = child_dict["frame"].get("name")
            if not node_name:
                node_name = child_dict["name"]

            node_dict = dict(
                {"node": hnode, "name": node_name}, **child_dict["metrics"]
            )
            if self.num_ranks > 1:
                node_dict["rank"] = rank

            self.node_dicts.append(node_dict)
        else:
            hnode = self.frame_to_node_dict.get(frame)

        if hnid != -1:
            self.seen_nids.append(hnid)

        hparent.add_child(hnode)

        if "children" in child_dict:
            for child in child_dict["children"]:
                self.parse_node_literal(child, hnode)

    def create_graph(self):
        for count in range(self.num_ranks):
            frame = None
            hnid = -1

            if self.filenames:
                rank = int(re.match(r"(.*)(\d+).json", self.filenames[count]).group(2))
                with open(self.filenames[count]) as json_file:
                    graph_dict = json.load(json_file)
            else:
                # TODO: fix for multi-process data
                graph_dict = self.list_of_dicts

            # start with creating a node_dict for each root
            for i in range(len(graph_dict)):
                if "_hatchet_nid" in graph_dict[i]["metrics"]:
                    hnid = graph_dict[i]["metrics"]["_hatchet_nid"]
                    self.seen_nids.append(hnid)
                frame = Frame(graph_dict[i]["frame"])
                if (hnid != -1 and hnid not in self.seen_nids) or (hnid == -1 and frame not in self.frame_to_node_dict):
                    graph_root = Node(frame, None, hnid=hnid)
                    self.frame_to_node_dict[frame] = graph_root

                    # depending on the node type, the name may not be in the frame
                    node_name = graph_dict[i]["frame"].get("name")
                    if not node_name:
                        node_name = graph_dict[i]["name"]

                    node_dict = dict(
                        {"node": graph_root, "name": node_name}, **graph_dict[i]["metrics"]
                    )
                    if self.num_ranks > 1:
                        node_dict["rank"] = rank

                    self.node_dicts.append(node_dict)
                else:
                    graph_root = self.frame_to_node_dict.get(frame)

                self.list_roots.append(graph_root)

                # call recursively on all children of root
                if "children" in graph_dict[i]:
                    for child in graph_dict[i]["children"]:
                        self.parse_node_literal(child, graph_root)

        for key in graph_dict[0]["metrics"].keys():
            if "(inc)" in key:
                self.inc_metrics.append(key)
            else:
                self.exc_metrics.append(key)


    def read(self):
        self.create_graph()

        graph = Graph(self.list_roots)

        # test if nids are already loaded
        if -1 in [n._hatchet_nid for n in graph.traverse()]:
            graph.enumerate_traverse()
        else:
            graph.enumerate_depth()

        dataframe = pd.DataFrame(data=self.node_dicts)
        dataframe.set_index(["node"], inplace=True)
        dataframe.sort_index(inplace=True)

        return hatchet.graphframe.GraphFrame(graph, dataframe, self.exc_metrics, self.inc_metrics)
