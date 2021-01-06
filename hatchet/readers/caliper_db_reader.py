# Copyright 2017-2020 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT


import pandas as pd

import hatchet.graphframe
from hatchet.node import Node
from hatchet.graph import Graph
from hatchet.frame import Frame
from hatchet.util.timer import Timer


class CaliperDBReader:
    """Read in a Caliper file using Caliper's native python reader."""

    def __init__(self, cali_reader):
        """Read from Caliper python reader (cali).

        Args:
            records (CaliperReader): caliper reader object (after read() is called)
        """
        self.cali_reader = cali_reader

        self.metric_columns = set()
        self.node_dicts = []

        self.timer = Timer()

        self.node_types = ["function", "mpi.function", "loop"]

    def create_graph(self, ctx="path"):
        list_roots = []
        visited = {}  # map frame to node
        parent_hnode = None

        # find nodes in the nodes section that represent the path hierarchy
        for node in self.cali_reader.records:
            metrics = {}
            node_label = ""
            if ctx in node:
                # if it's a list, then it's a callpath
                if isinstance(node[ctx], list):
                    node_label = node[ctx][-1]
                    for i in node.keys():
                        if node[i] == node_label:
                            self.node_type = i
                        elif i != ctx:
                            self.metric_columns.add(i)
                            if self.cali_reader.attribute(i).attribute_type() == "double":
                                metrics[i] = float(node[i])
                            elif self.cali_reader.attribute(i).attribute_type() == "int":
                                metrics[i] = int(node[i])
                            elif i == "function":
                                if isinstance(node[i], list):
                                    metrics[i] = node[i][-1]
                                else:
                                    metrics[i] = node[i]
                            else:
                                metrics[i] = node[i]

                    frame = Frame({"type": self.node_type, "name": node_label})
                    parent_frame = None
                    for i in visited.keys():
                        parent_label = node[ctx][-2]
                        if i["name"] == parent_label:
                            parent_frame = i
                            break
                    parent_hnode = visited[parent_frame]

                    hnode = Node(frame, parent_hnode)
                    print("CREATING NODE", hnode)

                    visited[frame] = hnode

                    node_dict = dict({"name": node_label, "node": hnode}, **metrics)
                    parent_hnode.add_child(hnode)
                    self.node_dicts.append(node_dict)
                # if it's a string, then it's a root
                else:
                    node_label = node[ctx]
                    for i in node.keys():
                        if node[i] == node_label:
                            self.node_type = i
                        else:
                            self.metric_columns.add(i)
                            if self.cali_reader.attribute(i).attribute_type() == "double":
                                metrics[i] = float(node[i])
                            elif self.cali_reader.attribute(i).attribute_type() == "int":
                                metrics[i] = int(node[i])
                            elif i == "function":
                                metrics[i] = node[i][-1]
                            else:
                                metrics[i] = node[i]

                    frame = Frame({"type": self.node_type, "name": node_label})

                    # since this node does not have a parent, this is a root
                    graph_root = Node(frame, None)
                    visited[frame] = graph_root
                    print("CREATING ROOT node=", graph_root)
                    list_roots.append(graph_root)

                    node_dict = dict(
                        {"name": node_label, "node": graph_root}, **metrics
                    )
                    self.node_dicts.append(node_dict)
                    parent_hnode = graph_root

        return list_roots

    def read(self):
        """Read the caliper JSON string to extract the calling context tree."""
        with self.timer.phase("graph construction"):
            list_roots = self.create_graph()

        # create a graph object once all the nodes have been added
        graph = Graph(list_roots)
        graph.enumerate_traverse()

        dataframe = pd.DataFrame(data=self.node_dicts)

        dataframe.set_index(["node"], inplace=True)
        dataframe.sort_index(inplace=True)

        # change column names
        for idx, item in enumerate(dataframe.columns):
            # make other columns consistent with other readers
            if item == "mpi.rank":
                dataframe.columns.values[idx] = "rank"
            if item == "module#cali.sampler.pc":
                dataframe.columns.values[idx] = "module"
            if item == "sum#time.duration" or item == "sum#avg#sum#time.duration":
                dataframe.columns.values[idx] = "time"
            if (
                item == "inclusive#sum#time.duration"
                or item == "sum#avg#inclusive#sum#time.duration"
            ):
                dataframe.columns.values[idx] = "time (inc)"

#        for i in self.cali_reader.attributes():
#            print("RRR", i, self.cali_reader.attribute(i).attribute_type())
            #if self.cali_reader.attribute(i).get('attribute.unit'):
            #    print("HERE")
            #else:
            #    print("BAD")
            #r.attribute('figure_of_merit').get('adiak.type'), 'double'
            #if t:
            #    #print(i, t)
            #    print("HERE")

        # create list of exclusive and inclusive metric columns
        exc_metrics = []
        inc_metrics = []
        for column in self.metric_columns:
            if "(inc)" in column:
                inc_metrics.append(column)
            else:
                exc_metrics.append(column)

        return hatchet.graphframe.GraphFrame(graph, dataframe, exc_metrics, inc_metrics)
