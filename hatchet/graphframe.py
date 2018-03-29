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

    def reduce(self, reduction_operators):
        """Reduces rows in self's dataframe.

        Reduces according to operator each set of rows with the same indices.

        Args:
            operator (:obj:`function`): A function that takes a pandas.DataFrame
                and returns a reduced pandas.DataFrame.

        Returns:
            A graphframe constructed by reducing self.

        Raises:
            ValueError: When an argument is invalid.
        """
        # check for invalid arguments
        if reduction_operators is not None:
            if (not isinstance(reduction_operators, dict) or
                any([not isinstance(x, basestring)
                     for x in reduction_operators.keys()]) or
                any([not callable(x) for x in reduction_operators.values()])):
                raise ValueError('reduction_operators is not a dict of '
                                 'basestring to function.')
        else:
            reduction_operators = {}

        # reduce rows of self's dataframe with identical indices
        reduced_rows = []
        for index in self.dataframe.index.unique().values:
            reducible_rows = self.dataframe.loc[[index]]
            reduced_row = pd.Series(index=self.dataframe.columns, dtype=object)
            for column_name in reducible_rows:
                reduction_operator = lambda x: None
                if column_name in reduction_operators:
                    reduction_operator = reduction_operators[column_name]
                reduced_column = reduction_operator(reducible_rows[column_name])
                reduced_row.loc[column_name] = reduced_column
            reduced_rows.append(reduced_row)
        reduced_dataframe = pd.DataFrame(data=reduced_rows)
        indices = self.dataframe.index.names
        reduced_dataframe.set_index(indices, drop=False, inplace=True)

        # construct reduced graphframe from reduced dataframe and original graph
        reduced_graphframe = GraphFrame()
        reduced_graphframe.dataframe = reduced_dataframe
        reduced_graphframe.graph = self.graph
        return reduced_graphframe
