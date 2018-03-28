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

    def filter(self, is_row_qualified):
        """Filters self's dataframe.

        Creates and returns a new graphframe whose dataframe is a copied subset
        of self's dataframe and whose graph is self's graph.

        Args:
            is_row_qualified (:obj:`function`): Function that returns True or
                False if a pandas.Series qualifies.

        Returns:
            A new graphframe that is the result of filtering self.

        Raises:
            ValueError: When an argument is invalid.
        """
        # currently necessary hard-coded values
        self.node_column_name = 'node'

        # check for invalid arguments
        if not callable(is_row_qualified):
            raise ValueError('is_row_qualified is not a function.')

        # get qualified rows
        qualified_rows = self.dataframe.apply(is_row_qualified, axis=1)

        # construct copied subset dataframe
        copied_subset_dataframe = self.dataframe.loc[qualified_rows].copy()
        copied_subset_dataframe.reset_index(drop=True, inplace=True)
        indices = list(self.dataframe.index.names)
        if self.node_column_name in indices:
            indices.insert(0, indices.pop(indices.index(self.node_column_name)))
        copied_subset_dataframe.set_index(indices, drop=False, inplace=True)

        # construct filtered graphframe
        filtered_graphframe = GraphFrame()
        filtered_graphframe.dataframe = copied_subset_dataframe
        filtered_graphframe.graph = self.graph
        return filtered_graphframe
