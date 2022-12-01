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

NANOSEC_IN_SEC = 1000000000


class NsightReader:
    def __init__(self, nsight_trace, ncu_metrics=None):
        fileObject = open(nsight_trace)
        # nsight systems trace data
        self.nsight_trace = list(DictReader(fileObject))
        fileObject.close()
        # nsight compute metrics file path (optional)
        self.ncu_metrics = ncu_metrics
        self.list_roots = []
        self.callpath_to_node_dicts = {}
        self.node_call_stack = []

    def create_graph(self):
        # helper function to create node dictionaries
        def create_node_dict(node, trace_event):
            return dict(
                {
                    "node": node,
                    "name": node.frame.get("name"),
                    "time": int(trace_event["DurNonChild (ns)"]) / NANOSEC_IN_SEC,
                    "time (inc)": int(trace_event["Duration (ns)"]) / NANOSEC_IN_SEC,
                }
            )

        # add additional metric data to dataframe if an ncu metrics file is provided
        def _add_metrics():
            metrics_df = pd.read_csv(self.ncu_metrics)
            # preprocessing
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

        for i in range(len(self.nsight_trace)):
            # if call stack is empty, current trace event is a root
            if len(self.node_call_stack) == 0:
                graph_root = Node(Frame(name=self.nsight_trace[i]["Name"]), None)
                node_dict = create_node_dict(graph_root, self.nsight_trace[i])
                self.list_roots.append(graph_root)
                self.callpath_to_node_dicts[str(graph_root.path())] = node_dict
                self.node_call_stack.append((self.nsight_trace[i], graph_root))
            else:
                # start time of current trace event
                currentStartTime = int(self.nsight_trace[i]["Start (ns)"])
                # end time of node atop the call stack
                previousEndTime = int(self.node_call_stack[-1][0]["End (ns)"])
                # if the start time is greater than the end time, the current trace
                # event is not a child of the node atop the call stack
                if previousEndTime < currentStartTime:
                    # keep popping the call stack until the current trace event's parent
                    # object is reached
                    while int(self.node_call_stack[-1][0]["End (ns)"]) < int(
                        self.nsight_trace[i]["Start (ns)"]
                    ):
                        self.node_call_stack.pop()
                # if all nodes in the call stack were popped, current trace event is a
                # new root
                if len(self.node_call_stack) == 0:
                    graph_root = Node(Frame(name=self.nsight_trace[i]["Name"]), None)
                    node_dict = create_node_dict(graph_root, self.nsight_trace[i])
                    self.list_roots.append(graph_root)
                    self.callpath_to_node_dicts[str(graph_root.path())] = node_dict
                    self.node_call_stack.append((self.nsight_trace[i], graph_root))
                else:
                    parent = self.node_call_stack[-1][1]
                    child = Node(Frame(name=self.nsight_trace[i]["Name"]), parent)
                    self.node_call_stack.append((self.nsight_trace[i], child))
                    child_path = str(child.path())
                    # if there is an existing node with the same callpath as the current
                    # trace event, aggregate their metrics
                    if self.callpath_to_node_dicts.get(child_path):
                        self.callpath_to_node_dicts[child_path]["time"] += (
                            int(self.nsight_trace[i]["DurNonChild (ns)"])
                            / NANOSEC_IN_SEC
                        )
                        self.callpath_to_node_dicts[child_path]["time (inc)"] += (
                            int(self.nsight_trace[i]["Duration (ns)"]) / NANOSEC_IN_SEC
                        )
                    else:
                        parent.add_child(child)
                        node_dict = create_node_dict(child, self.nsight_trace[i])
                        self.callpath_to_node_dicts[child_path] = node_dict

        if self.ncu_metrics:
            _add_metrics()

        graph = Graph(self.list_roots)
        graph.enumerate_depth()

        return graph

    def read(self):
        graph = self.create_graph()

        dataframe = pd.DataFrame(data=self.callpath_to_node_dicts.values())
        dataframe.set_index(["node"], inplace=True)
        dataframe.sort_index(inplace=True)

        return hatchet.graphframe.GraphFrame(graph, dataframe, ["time"], ["time (inc)"])
