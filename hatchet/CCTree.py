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

from HPCTDBReader import *


class CCTree:
    """ A single tree that includes the root node and other performance data
        associated with this tree.
    """

    def __init__(self, dirname, srcformat):
        self.numPes = 0
        self.numNodes = 0
        self.numMetrics = 0

        if srcformat == 'hpctoolkit':
            dbr = HPCTDBReader(dirname)
            self.numPes = dbr.numPes
            self.numNodes = dbr.numNodes
            self.numMetrics = dbr.numMetrics

            (self.loadModules, self.files, self.procedures) = dbr.fillTables()

            self.metrics = dbr.readMetricDBFiles()

            # createCCTree assumes readMetricDBFiles has been called
            self.root = dbr.createCCTree()
            print "Tree created from HPCToolkit database"

    def getNodeName(self, ccNode):
        """ Returns a string to be displayed in the ETE tree.
        """
        if ccNode.node_type == 'PF' or ccNode.node_type == 'Pr':
            return self.procedures[ccNode.name]
        elif ccNode.node_type == 'L':
            return "Loop@" + (self.files[ccNode.src_file]).rpartition('/')[2] + ":" + ccNode.line
        elif ccNode.node_type == 'S':
            return (self.files[ccNode.src_file]).rpartition('/')[2] + ":" + ccNode.line

    def traverse(self, root=None):
        """Traverse the tree depth-first and yield each node."""
        if root == None:
            root = self.root

        return list(iter(root))
