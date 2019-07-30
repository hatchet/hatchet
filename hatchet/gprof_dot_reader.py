##############################################################################
# Copyright (c) 2017-2019, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# This file is part of Hatchet.
# Created by Abhinav Bhatele <bhatele@llnl.gov>.
# LLNL-CODE-741008. All rights reserved.
#
# For details, see: https://github.com/LLNL/hatchet
# Please also read the LICENSE file for the MIT License notice.
##############################################################################
import re
import pandas as pd
import pydot

from .node import Node
from .graph import Graph
from .frame import Frame
from .util.timer import Timer
from .util.config import *


class GprofDotReader:
    """ Read in gprof/callgrind output in dot format generated by gprof2dot.
    """

    def __init__(self, filename):
        self.dotfile = filename

        self.name_to_hnode = {}
        self.name_to_dict = {}

        self.timer = Timer()


    def create_graph(self):
        """ Read the DOT files to create a graph.
        """
        graphs = pydot.graph_from_dot_file(self.dotfile, encoding='utf-8')

        for graph in graphs:
            for edge in graph.get_edges():
                src_name = edge.get_source().strip('"')
                dst_name = edge.get_destination().strip('"')

                if src_name not in self.name_to_hnode:
                    # create a node if it doesn't exist yet
                    src_hnode = Node(Frame({'type': 'function',
                                            'name': src_name}),
                                     None)
                    self.name_to_hnode[src_name] = src_hnode
                else:
                    src_hnode = self.name_to_hnode[src_name]

                if dst_name not in self.name_to_hnode:
                    # create a node if it doesn't exist yet
                    dst_hnode = Node(Frame({'type': 'function',
                                            'name': dst_name}),
                                     src_hnode)
                    self.name_to_hnode[dst_name] = dst_hnode
                else:
                    # add source node as parent
                    dst_hnode = self.name_to_hnode[dst_name]
                    dst_hnode.add_parent(src_hnode)

                # add destination node as child
                src_hnode.add_child(dst_hnode)

            for node in graph.get_nodes():
                node_name = node.get_name().strip('"')

                if node_name not in dot_keywords:
                    if node_name not in self.name_to_hnode:
                        # create a node if it doesn't exist yet
                        hnode = Node(Frame({'type': 'function',
                                            'name': node_name}),
                                     None)
                        self.name_to_hnode[node_name] = hnode
                    else:
                        hnode = self.name_to_hnode[node_name]

                    node_label = node.obj_dict['attributes'].get('label').strip('"')

                    module, _, inc, exc, _ = node_label.split(r'\n')

                    inc_time = float(re.sub(r'\%', '', inc))
                    exc_time = float(re.sub(r'[\(\%\)]', '', exc))

                    # create a dict with node properties
                    node_dict = {
                        'module': module,
                        'name': node_name,
                        'time (inc)': inc_time,
                        'time': exc_time,
                        'node': hnode
                    }
                    self.name_to_dict[node_name] = node_dict

        # add all nodes with no parents to the list of roots
        list_roots = []
        for (key, val) in self.name_to_hnode.items():
            if not val.parents:
                list_roots.append(val)

        return list_roots


    def create_graphframe(self):
        """ Read the DOT file generated by gprof2dot to create a graphframe.
            The DOT file contains a call graph.
        """
        with self.timer.phase('graph construction'):
            roots = self.create_graph()
            graph = Graph(roots)

        with self.timer.phase('data frame'):
            dataframe = pd.DataFrame.from_dict(data=list(self.name_to_dict.values()))
            index = ['node']
            dataframe.set_index(index, drop=False, inplace=True)

        return graph, dataframe, ['time'], ['time (inc)']
