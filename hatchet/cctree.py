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

            (self.load_modules,
             self.files, self.procedures) = dbr.fill_tables()

            self.metrics = dbr.read_metricdb()

            # create_cctree assumes read_metricdb has been called
            self.root = dbr.create_cctree()
            print "Tree created from HPCToolkit database"

    def get_node_name(self, ccnode):
        """ Returns a string to be displayed in the ETE tree.
        """
        if ccnode.node_type == 'PF' or ccnode.node_type == 'Pr':
            return self.procedures[ccnode.name]
        elif ccnode.node_type == 'L':
            return ("Loop@" + (self.files[ccnode.src_file]).rpartition('/')[2]
                    + ":" + ccnode.line)
        elif ccnode.node_type == 'S':
            return ((self.files[ccnode.src_file]).rpartition('/')[2]
                    + ":" + ccnode.line)

    def traverse(self, root=None):
        """Traverse the tree depth-first and yield each node."""
        if root is None:
            root = self.root

        return list(iter(root))
