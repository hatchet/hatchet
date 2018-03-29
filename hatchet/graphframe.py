##############################################################################
# Copyright (c) 2017-2018, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# This file is part of Hatchet.
# Created by Abhinav Bhatele <bhatele@llnl.gov>.
# LLNL-CODE-741008. All rights reserved.
#
# For details, see: https://github.com/LLNL/hatchet
# Please also read the LICENSE file for the MIT License notice.
##############################################################################

from hpctoolkit_reader import HPCToolkitReader
from caliper_reader import CaliperReader
import pandas as pd

class GraphFrame:
    """ This class associates the graph with a dataframe.
    """

    def __init__(self):
        self.num_pes = 0
        self.num_nodes = 0
        self.num_metrics = 0

        self.graph = None

    def from_hpctoolkit(self, dirname):
        reader = HPCToolkitReader(dirname)
        self.num_pes = reader.num_pes
        self.num_nodes = reader.num_nodes
        self.num_metrics = reader.num_metrics

        (self.graph, self.dataframe) = reader.create_graph()

    def from_caliper(self, filename):
        reader = CaliperReader(filename)

        (self.graph, self.dataframe) = reader.create_graph()

    def union(self, other):
        """Constructs a new graphframe from self and other.

        Unions the graphs of self's graphframe and other's graphframe then
        concatenates the dataframes. Updates self's and other's dataframes'
        nodes to point to new nodes in unioned graph.

        Args:
            other (:obj:`GraphFrame`): The other graphframe to union with.

        Returns:
            A graphframe constructed from unioning self with other.

        Raises:
            ValueError: When an argument is invalid.
        """
        # currently necessary hard-coded values
        self.node_column_name = 'node'

        # check for invalid arguments
        if not isinstance(other, GraphFrame):
            raise ValueError('other is not a GraphFrame.')

        # union the graphs
        old_to_new = {}
        unioned_graph = self.graph.union(other.graph, old_to_new)

        # concat both dataframes, map old nodes to new nodes, join indices
        unioned_dataframe = pd.concat([self.dataframe.reset_index(drop=True),
                                       other.dataframe.reset_index(drop=True)],
                                      ignore_index=True)
        old_node_column = unioned_dataframe[self.node_column_name]
        node_column_map = lambda x: old_to_new[x]
        new_node_column = old_node_column.map(node_column_map)
        unioned_dataframe[self.node_column_name] = new_node_column
        unioned_dataframe.reset_index(drop=True, inplace=True)
        indices = list(set(self.dataframe.index.names +
                           other.dataframe.index.names))
        if self.node_column_name in indices:
            indices.insert(0, indices.pop(indices.index(self.node_column_name)))
        unioned_dataframe.set_index(indices, drop=False, inplace=True)

        # construct unioned graphframe from unioned dataframe and unioned graph
        unioned_graphframe = GraphFrame()
        unioned_graphframe.dataframe = unioned_dataframe
        unioned_graphframe.graph = unioned_graph
        return unioned_graphframe
