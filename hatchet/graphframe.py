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

    def fill(self, fill_maps=None):
        """Fills missing rows in dataframe.

        Loops through each row of self's dataframe. For each 'current' row,
        checks to see if 'parent' row exists, if not, creates one, assigning
        values to each column as a function of the child row's values. Continue
        this 'climb' towards the 'root row', adding in a potentially 'filled'
        ancestor row based on the values of the most recent descendant at each
        ascension.

        Args:
            fill_maps (:obj:`dict`): A dictionary of str to function that maps
                child row's column value to parent row's filled column value.

        Returns:
            A graphframe constructed from filling self.

        Raises:
            ValueError: When an argument is invalid.
        """
        # fill expects fill_maps to be a dict
        if fill_maps is None:
            fill_maps = {}

        if (not isinstance(fill_maps, dict) or
            any([not isinstance(x, basestring) for x in fill_maps.keys()]) or
            any([not callable(x) for x in fill_maps.values()])):
            raise ValueError('fill_maps is not a dict of basestring to '
                             'function.')

        # for each row in the dataframe, if necessary, create a row for each
        # 'ancestor' of that row, thus 'filling' the dataframe
        filled_rows = []
        filled_rows_indices = set()
        self.node_column_name = 'node'
        for row in self.dataframe.iterrows():
            # get current row and parent node
            current_row = row[1]
            parent_node = current_row.loc[self.node_column_name].parent

            # while parent node exists:
            while parent_node is not None:

                # build parent row index
                parent_index = []
                for index_name in self.dataframe.index.names:
                    fill_map = lambda x: None
                    if index_name in fill_maps:
                        fill_map = fill_maps[index_name]
                    parent_index.append(fill_map(current_row))
                parent_index = tuple(parent_index)

                # if parent row in table or filled rows use that, else make it
                if parent_index in self.dataframe.index:
                    parent_row = self.dataframe.loc[parent_index]
                elif parent_index in filled_rows_indices:
                    # because parent is in filled_rows, that means all of its
                    # ancestors are also filled, continue to next row
                    break
                else:
                    # parent row didn't exist already, so we make it
                    parent_row = pd.Series(name=parent_index)

                    # map all column values from current to parent
                    for column_name in self.dataframe.columns.values:
                        fill_map = lambda x: None
                        if column_name in fill_maps:
                            fill_map = fill_maps[column_name]
                        parent_row.loc[column_name] = fill_map(current_row)

                    # add parent row to filled_rows
                    filled_rows_indices.add(parent_index)
                    filled_rows.append(parent_row)

                # iterate current row and parent node
                current_row = parent_row
                parent_node = parent_node.parent

        # add filled rows to dataframe and make copy
        filled_dataframe = self.dataframe.append(filled_rows)

        # construct and return filled graphframe
        filled_graphframe = GraphFrame()
        filled_graphframe.dataframe = filled_dataframe
        filled_graphframe.graph = self.graph
        return filled_graphframe
