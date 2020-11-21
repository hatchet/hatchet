# Copyright 2017-2020 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

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
                "name": "A",
                "type": "function",
                "metrics": {"time (inc)": 130.0, "time": 0.0},
                "children": [
                    {
                        "name": "B",
                        "type": "function",
                        "metrics": {"time (inc)": 20.0, "time": 5.0},
                        "children": [
                            {
                                "name": "C",
                                "type": "function",
                                "metrics": {"time (inc)": 5.0, "time": 5.0},
                                "children": [
                                    {
                                        "name": "D",
                                        "type": "function",
                                        "metrics": {"time (inc)": 8.0, "time": 1.0},
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "name": "E",
                        "type": "function",
                        "metrics": {"time (inc)": 55.0, "time": 10.0},
                        "children": [
                            {
                                "name": "H",
                                "type": "function",
                                "metrics": {"time (inc)": 1.0, "time": 9.0}
                            }
                        ],
                    },
                ],
            }
        ]

    Return:
        (GraphFrame): graphframe containing data from dictionaries
    """

    def __init__(self, graph_dict):
        """Read from list of dictionaries.

        graph_dict (dict): List of dictionaries encoding nodes.
        """
        self.graph_dict = graph_dict

    def parse_node_literal(self, frame_to_node_dict, node_dicts, child_dict, hparent):
        """Create node_dict for one node and then call the function
        recursively on all children.
        """
        frame = Frame(child_dict["frame"])
        if "duplicate" not in child_dict:
            hnode = Node(frame, hparent)

            # depending on the node type, the name may not be in the frame
            node_name = child_dict["frame"].get("name")
            if not node_name:
                node_name = child_dict["name"]

            node_dict = dict(
                {"node": hnode, "name": node_name}, **child_dict["metrics"]
            )

            node_dicts.append(node_dict)
            frame_to_node_dict[frame] = hnode
        elif "duplicate" in child_dict:
            hnode = frame_to_node_dict.get(frame)
            if not hnode:
                hnode = Node(frame, hparent)

                # depending on the node type, the name may not be in the frame
                node_name = child_dict["frame"].get("name")
                if not node_name:
                    node_name = child_dict["name"]

                node_dict = dict(
                    {"node": hnode, "name": node_name}, **child_dict["metrics"]
                )
                node_dicts.append(node_dict)
                frame_to_node_dict[frame] = hnode

        hparent.add_child(hnode)

        if "children" in child_dict:
            for child in child_dict["children"]:
                self.parse_node_literal(frame_to_node_dict, node_dicts, child, hnode)

    def read(self):
        list_roots = []
        node_dicts = []
        frame_to_node_dict = {}
        frame = None

        # start with creating a node_dict for each root
        for i in range(len(self.graph_dict)):
            frame = Frame(self.graph_dict[i]["frame"])
            graph_root = Node(frame, None)

            # depending on the node type, the name may not be in the frame
            node_name = self.graph_dict[i]["frame"].get("name")
            if not node_name:
                node_name = self.graph_dict[i]["name"]

            node_dict = dict(
                {"node": graph_root, "name": node_name}, **self.graph_dict[i]["metrics"]
            )
            node_dicts.append(node_dict)

            list_roots.append(graph_root)
            frame_to_node_dict[frame] = graph_root

            # call recursively on all children of root
            if "children" in self.graph_dict[i]:
                for child in self.graph_dict[i]["children"]:
                    self.parse_node_literal(
                        frame_to_node_dict, node_dicts, child, graph_root
                    )

        graph = Graph(list_roots)
        graph.enumerate_traverse()

        exc_metrics = []
        inc_metrics = []
        for key in self.graph_dict[i]["metrics"].keys():
            if "(inc)" in key:
                inc_metrics.append(key)
            else:
                exc_metrics.append(key)

        dataframe = pd.DataFrame(data=node_dicts)
        dataframe.set_index(["node"], inplace=True)
        dataframe.sort_index(inplace=True)

        return hatchet.graphframe.GraphFrame(graph, dataframe, exc_metrics, inc_metrics)
