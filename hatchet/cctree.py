##############################################################################
# Copyright (c) 2017, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# Written by Abhinav Bhatele <bhatele@llnl.gov>.
# LLNL-CODE-741008. All rights reserved.
#
# This file is part of Hatchet. For details, see:
# https://github.com/LLNL/hatchet
# Please also read the LICENSE file for the MIT License notice.
##############################################################################

from hpctoolkit_reader import HPCToolkitReader
from caliper_reader import CaliperReader
from hatchet.external.printtree import as_text
import pandas as pd

class CCTree:
    """ A single tree that includes the root node and other performance data
        associated with this tree.
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

        (self.root, self.treeframe) = reader.create_cctree()

    def from_caliper(self, filename):
        reader = CaliperReader(filename)

        (self.root, self.treeframe) = reader.create_cctree()

    def traverse(self, root=None):
        """Traverse the tree depth-first and yield each node."""
        if root is None:
            root = self.root

        return list(iter(root))

    def tree_as_text(self, root=None, metric='CPUTIME (usec) (I)',
                     threshold=0.01, unicode=True, color=True):
        if root is None:
            root = self.root

        result = as_text(root, root, self.treeframe, metric=metric,
                         threshold=threshold, unicode=unicode, color=color)

        return result

    def __str__(self):
        return self.tree_as_text(self.root).encode('utf-8')
