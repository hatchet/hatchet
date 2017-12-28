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

from hpctdb_reader import HPCTDBReader
from hatchet.external.printtree import as_text
import pandas as pd

class CCTree:
    """ A single tree that includes the root node and other performance data
        associated with this tree.
    """

    def __init__(self, dirname, srcformat):
        self.num_pes = 0
        self.num_nodes = 0
        self.num_metrics = 0

        if srcformat == 'hpctoolkit':
            dbr = HPCTDBReader(dirname)
            self.num_pes = dbr.num_pes
            self.num_nodes = dbr.num_nodes
            self.num_metrics = dbr.num_metrics

            (self.load_modules, self.src_files,
             self.procedure_names) = dbr.fill_tables()

            self.metrics = dbr.read_metricdb()

            self.root = dbr.create_cctree()
            print "Tree created from HPCToolkit database"

            list_index = []
            list_dict = []

            for node in self.traverse():
                list_index.append(hash(''.join(node.callpath)))
                list_dict.append(dict({'name': node.name, 'module': node.load_module, 'file': node.src_file, 'inc': node.metrics[0][1], 'exc': node.metrics[1][1]}))
            self.treeframe = pd.DataFrame(data=list_dict, index=list_index)

    def traverse(self, root=None):
        """Traverse the tree depth-first and yield each node."""
        if root is None:
            root = self.root

        return list(iter(root))

    def tree_as_text(self, root=None, _metric='inclusive', _threshold=0.01,
                   _unicode=True, _color=True):
        if root is None:
            root = self.root

        result = as_text(root, root, self.src_files, metric=_metric,
                         threshold=_threshold, unicode=_unicode, color=_color)

        return result

    def __str__(self):
        return self.tree_as_text(self.root).encode('utf-8')
