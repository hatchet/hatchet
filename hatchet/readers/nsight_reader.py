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
    def __init__(self, nsys_trace, ncu_metrics=None):
        fileObject = open(nsys_trace)
        self.nsys_trace = list(DictReader(fileObject))
        fileObject.close()
        self.ncu_metrics = ncu_metrics
        self.list_roots = []
        self.callpath_to_node_dicts = {}
        self.node_call_stack = []

    def create_graph(self):
        def _add_metrics():
            metrics_df = pd.read_csv(self.ncu_metrics)
            metrics_df = metrics_df.drop("Domain", axis=1)
            metrics_df.rename(
                columns={
                    "Range:PL_Type:PL_Value:CLR_Type:Color:Msg_Type:Msg": "Callstack"
                },
                inplace=True,
            )
            filter_cpu = metrics_df["Kernel Name"].str.contains("_kernel_agent")
            metrics_df = metrics_df[~filter_cpu]
            metrics_df["Callstack"] = metrics_df["Callstack"].apply(
                lambda x: x.replace(":none:none:none:none:none:none", "")
                .replace('"', "")
                .split()
            )
            metrics_df["Callstack"] = metrics_df["Callstack"].apply(lambda x: tuple(x))
            filter = metrics_df["Metric Name"].str.contains("device__attribute")
            metrics_df = metrics_df[~filter]
            kernels = metrics_df.Callstack.unique()
            for kernel in kernels:
                kernel_metrics = metrics_df.loc[metrics_df["Callstack"] == kernel][
                    ["Metric Name", "Average", "Minimum", "Maximum"]
                ]
                kernel_path = "("
                for k in kernel:
                    kernel_path += "Node({{'name': '{}', 'type': 'None'}}), ".format(k)
                kernel_path = kernel_path[:-2] + ")"
                self.callpath_to_node_dicts[kernel_path]["is_kernel"] = True
                metrics = kernel_metrics["Metric Name"].unique()
                for metric in metrics:
                    self.callpath_to_node_dicts[kernel_path][
                        metric
                    ] = kernel_metrics.loc[kernel_metrics["Metric Name"] == metric][
                        "Average"
                    ].values[
                        0
                    ]
                    self.callpath_to_node_dicts[kernel_path][
                        metric
                    ] = kernel_metrics.loc[kernel_metrics["Metric Name"] == metric][
                        "Minimum"
                    ].values[
                        0
                    ]
                    self.callpath_to_node_dicts[kernel_path][
                        metric
                    ] = kernel_metrics.loc[kernel_metrics["Metric Name"] == metric][
                        "Maximum"
                    ].values[
                        0
                    ]

        for i in range(len(self.nsys_trace)):
            if len(self.node_call_stack) == 0:
                graph_root = Node(Frame(name=self.nsys_trace[i]["Name"]), None)
                node_dict = dict(
                    {
                        "node": graph_root,
                        "name": graph_root.frame.get("name"),
                        "time": int(self.nsys_trace[i]["DurNonChild (ns)"])
                        / 1000000000,
                        "time (inc)": int(self.nsys_trace[i]["Duration (ns)"])
                        / 1000000000,
                    }
                )
                self.list_roots.append(graph_root)
                self.callpath_to_node_dicts[str(graph_root.path())] = node_dict
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
                child = Node(Frame(name=self.nsys_trace[i]["Name"]), parent)
                self.node_call_stack.append((self.nsys_trace[i], child))
                child_path = str(child.path())
                if self.callpath_to_node_dicts.get(child_path):
                    self.callpath_to_node_dicts[child_path]["time"] += (
                        int(self.nsys_trace[i]["DurNonChild (ns)"]) / 1000000000
                    )
                    self.callpath_to_node_dicts[child_path]["time (inc)"] += (
                        int(self.nsys_trace[i]["Duration (ns)"]) / 1000000000
                    )
                else:
                    parent.add_child(child)
                    node_dict = dict(
                        {
                            "node": child,
                            "name": child.frame.get("name"),
                            "time": int(self.nsys_trace[i]["DurNonChild (ns)"])
                            / 1000000000,
                            "time (inc)": int(self.nsys_trace[i]["Duration (ns)"])
                            / 1000000000,
                        }
                    )
                    self.callpath_to_node_dicts[child_path] = node_dict

        if self.ncu_metrics:
            _add_metrics()

        graph = Graph(self.list_roots)

        # test if nids are already loaded
        if -1 in [n._hatchet_nid for n in graph.traverse()]:
            graph.enumerate_traverse()
        else:
            graph.enumerate_depth()

        return graph

    def read(self):
        graph = self.create_graph()

        dataframe = pd.DataFrame(data=self.callpath_to_node_dicts.values())
        dataframe.set_index(["node"], inplace=True)
        dataframe.sort_index(inplace=True)

        return hatchet.graphframe.GraphFrame(graph, dataframe, ["time"], ["time (inc)"])
