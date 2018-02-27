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


class CCNode:
    """ A node in the tree.
    """

    def __init__(self, callpath_tuple, parent):
        self.callpath = callpath_tuple
        self.tf_index = hash(callpath_tuple)

        self.parent = parent
        self.children = []

    def add_child(self, node):
        """ Adds a child to this node.
        """
        assert isinstance(node, CCNode)
        self.children.append(node)

    def traverse(self, order='pre'):
        """Traverse the tree depth-first and yield each node.
        """
        if(order == 'pre'):
            yield self

        for child in self.children:
            for item in child.traverse():
                yield item

        if(order == 'post'):
            yield self

    def __hash__(self):
        return self.tf_index
