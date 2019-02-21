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
import pandas as pd

from .hpctoolkit_reader import HPCToolkitReader
from .caliper_reader import CaliperReader
from .node import Node
from .graph import Graph


class GraphFrame:
    """ An input dataset is read into an object of this type, which includes a
        graph and a dataframe.
    """

    def __init__(self):
        self.num_pes = 0
        self.num_nodes = 0
        self.num_metrics = 0

        self.graph = None

    def from_hpctoolkit(self, dirname):
        """ Read in an HPCToolkit database directory.
        """
        reader = HPCToolkitReader(dirname)
        self.num_pes = reader.num_pes
        self.num_nodes = reader.num_nodes
        self.num_metrics = reader.num_metrics

        (self.graph, self.dataframe) = reader.create_graphframe()

    def from_caliper(self, filename):
        """ Read in a Caliper Json-split file.
        """
        reader = CaliperReader(filename)

        (self.graph, self.dataframe) = reader.create_graphframe()

    def from_literal(self, graph_dict):
        """ Read graph from a dict literal.
        """
        def parse_node_literal(child_dict, hparent, parent_callpath):
            """ Create node_dict for one node and then call the function
                recursively on all children.
            """
            node_callpath = parent_callpath
            node_callpath.append(child_dict['name'])
            hnode = Node(tuple(node_callpath), hparent)

            node_dicts.append(dict({'node': hnode, 'rank': 0, 'name': child_dict['name']}, **child_dict['metrics']))
            hparent.add_child(hnode)

            if 'children' in child_dict:
                for child in child_dict['children']:
                    parse_node_literal(child, hnode, node_callpath)

        # start with creating a node_dict for the root
        root_callpath = []
        root_callpath.append(graph_dict['name'])
        graph_root = Node(tuple(root_callpath), None)

        node_dicts = []
        node_dicts.append(dict({'node': graph_root, 'rank': 0, 'name': graph_dict['name']}, **graph_dict['metrics']))

        # call recursively on all children of root
        if 'children' in graph_dict:
            for child in graph_dict['children']:
                parse_node_literal(child, graph_root, root_callpath)

        self.graph = Graph([graph_root])
        self.dataframe = pd.DataFrame(data=node_dicts)
        indices = ['node', 'rank']
        self.dataframe.set_index(indices, drop=False, inplace=True)

    def filter(self, filter_function):
        """ Filter the dataframe using a user supplied function.
        """
        filtered_rows = self.dataframe.apply(filter_function, axis=1)
        filtered_df = self.dataframe[filtered_rows]

        filtered_gf = GraphFrame()
        filtered_gf.dataframe = filtered_df
        filtered_gf.graph = self.graph
        return filtered_gf
