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
from hatchet.external.printtree import as_text
import pandas as pd

class GraphFrame:
    """ This class associates the graph with a dataframe.
    """

    def __init__(self):
        self.num_pes = 0
        self.num_nodes = 0
        self.num_metrics = 0

        self.root = None

    def from_hpctoolkit(self, dirname):
        reader = HPCToolkitReader(dirname)
        self.num_pes = reader.num_pes
        self.num_nodes = reader.num_nodes
        self.num_metrics = reader.num_metrics

        (self.root, self.dataframe) = reader.create_graph()

    def from_caliper(self, filename):
        reader = CaliperReader(filename)

        (self.root, self.dataframe) = reader.create_graph()

    def tree_as_text(self, root=None, metric='CPUTIME (usec) (I)', name='name',
            context='file', rank=0, threshold=0.01, unicode=True, color=True):
        if root is None:
            root = self.root

        result = as_text(root, root, self.dataframe, metric, name, context,
                         rank, threshold, unicode=unicode, color=color)

        return result

    def __str__(self):
        return self.tree_as_text(self.root).encode('utf-8')
