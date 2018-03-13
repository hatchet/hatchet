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
from node import Node
from graph import Graph
import pandas as pd

class GraphFrame:
    """ This class associates the graph with a dataframe.
    """

    def __init__(self):
        self.node_column_name = 'node'
        self.rank_column_name = 'mpi.rank'
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

    def filter(self, is_row_qualified, has_descendants=False):
        """Filters self's dataframe.

        Gets rows from self's dataframe that qualify, and possibly rows of
        descendant nodes of qualifying nodes and returns a new graphframe
        with qualified dataframe rows and original graph.

        Args:
            is_row_qualified (:obj:`function`): Function that returns True or
                False if a pandas.Series qualifies.
            has_descendants (bool): Whether the filter keeps descendants of
                matched rows.

        Returns:
            A new graphframe that is the result of filtering self.

        Raises:
            ValueError: When an argument is invalid.
        """
        if not callable(is_row_qualified):
            raise ValueError('is_row_qualified is not a function.')

        if not isinstance(has_descendants, bool):
            raise ValueError('has_descendants is not a bool.')

        # get boolean series for is_qualified rows
        apply_series = self.dataframe.apply(is_row_qualified, axis=1)

        # get indices for True/qualified rows
        indices = set(self.dataframe.loc[apply_series, self.node_column_name])

        # add indices of descendants if has_descendants is True
        if has_descendants is True:
            for node in indices.copy():
                for descendant in node.traverse():
                    indices.add(descendant)

        # construct filtered dataframe
        filtered_dataframe = self.dataframe.loc[list(indices)].copy()
        filtered_dataframe.reset_index(drop=True, inplace=True)
        filtered_dataframe.set_index([self.node_column_name,
                                      self.rank_column_name],
                                     drop=False, inplace=True)

        # return new graphframe with copy of filtered dataframe and graph
        filtered_graphframe = GraphFrame()
        filtered_graphframe.dataframe = filtered_dataframe
        filtered_graphframe.graph = self.graph
        return filtered_graphframe
