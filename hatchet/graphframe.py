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
import pandas as pd

from .hpctoolkit_reader import HPCToolkitReader
from .caliper_reader import CaliperReader



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

        (self.graph, self.dataframe) = reader.create_graph()

    def from_caliper(self, filename):
        """ Read in a Caliper Json-split file.
        """
        reader = CaliperReader(filename)

        (self.graph, self.dataframe) = reader.create_graph()

    def filter(self, filter_function):
        """ Filter the dataframe using a user supplied function.
        """
        filtered_rows = self.dataframe.apply(filter_function, axis=1)
        filtered_df = self.dataframe[filtered_rows]

        filtered_gf = GraphFrame()
        filtered_gf.dataframe = filtered_df
        filtered_gf.graph = self.graph
        return filtered_gf
