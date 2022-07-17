# Copyright 2017-2022 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import pandas as pd

import hatchet.graphframe
from hatchet.node import Node
from hatchet.graph import Graph
from hatchet.frame import Frame

from csv import DictReader


class NsightReader:
    def __init__(self, nsys_trace):
        fileObject = open(nsys_trace)
        self.nsys_trace = list(DictReader(fileObject))
        fileObject.close()
        self.list_roots = []
        self.node_dicts = []
        self.node_call_stack = []

    def create_graph(self):
        for i in range(len(self.nsys_trace)):
            if len(self.node_call_stack) == 0:
                graph_root = Node(
                    Frame(name=self.nsys_trace[i]["Name"], type="function"), None
                )
                node_dict = dict(
                    {
                        "node": graph_root,
                        "name": graph_root.frame.get("name"),
                        "time": self.nsys_trace[i]["DurNonChild (ns)"],
                        "time (inc)": self.nsys_trace[i]["Duration (ns)"],
                    }
                )
                self.list_roots.append(graph_root)
                self.node_dicts.append(node_dict)
                self.node_call_stack.append((self.nsys_trace[i], graph_root))
            else:
                currentStartTime = int(self.nsys_trace[i]["Start (ns)"])
                previousEndTime = int(self.node_call_stack[-1][0]["End (ns)"])
                if previousEndTime < currentStartTime:
                    while int(self.node_call_stack[-1][0]["End (ns)"]) < int(
                        self.nsys_trace[i]["Start (ns)"]
                    ):
                        self.node_call_stack.pop()
                parent = self.node_call_stack[-1][1]
                child = Node(
                    Frame(name=self.nsys_trace[i]["Name"], type="function"), parent
                )
                node_dict = dict(
                    {
                        "node": child,
                        "name": child.frame.get("name"),
                        "time": self.nsys_trace[i]["DurNonChild (ns)"],
                        "time (inc)": self.nsys_trace[i]["Duration (ns)"],
                    }
                )
                self.node_dicts.append(node_dict)
                self.node_call_stack.append((self.nsys_trace[i], child))

        graph = Graph(self.list_roots)

        # test if nids are already loaded
        if -1 in [n._hatchet_nid for n in graph.traverse()]:
            graph.enumerate_traverse()
        else:
            graph.enumerate_depth()

        return graph

    def read(self):
        graph = self.create_graph()

        dataframe = pd.DataFrame(data=self.node_dicts)
        dataframe.set_index(["node"], inplace=True)

        return hatchet.graphframe.GraphFrame(graph, dataframe, ["time"], ["time (inc)"])
