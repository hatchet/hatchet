##############################################################################
# Copyright (c) 2017-2019, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# This file is part of Hatchet.
# Created by Abhinav Bhatele <bhatele@llnl.gov>.
# LLNL-CODE-741008. All rights reserved.
#
# For details, see: https://github.com/LLNL/hatchet
# Please also read the LICENSE file for the MIT License notice.
##############################################################################
from functools import total_ordering


@total_ordering
class Node:
    """ A node in the graph. The node only stores its callpath.
    """

    def __init__(self, callpath_tuple, parent):
        self.callpath = callpath_tuple
        self.df_index = hash(callpath_tuple)

        self.parents = []
        if parent is not None:
            self.add_parent(parent)
        self.children = []

    def add_parent(self, node):
        """ Adds a parent to this node's list of parents.
        """
        assert isinstance(node, Node)
        self.parents.append(node)

    def add_child(self, node):
        """ Adds a child to this node's list of children.
        """
        assert isinstance(node, Node)
        self.children.append(node)

    def traverse(self, order='pre'):
        """ Traverse the tree depth-first and yield each node.
        """
        if(order == 'pre'):
            yield self

        for child in self.children:
            for item in child.traverse():
                yield item

        if(order == 'post'):
            yield self

    def set_callpath(self, callpath):
        self.callpath = callpath
        self.df_index = hash(callpath)

    def __hash__(self):
        return self.df_index

    def __eq__(self, other):
        return (id(self) == id(other) and self.callpath == other.callpath)

    def __lt__(self, other):
        return (self.callpath < other.callpath)

    def __str__(self):
        """ Returns a string representation of the node.
        """
        return self.callpath[-1]
