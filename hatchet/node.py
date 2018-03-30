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

from functools import total_ordering

@total_ordering
class Node:
    """ A node in the graph.
    """

    def __init__(self, callpath_tuple, parent):
        self.callpath = callpath_tuple
        self.tf_index = hash(callpath_tuple)

        self.parent = parent
        self.children = []

    def add_child(self, node):
        """ Adds a child to this node.
        """
        assert isinstance(node, Node)
        self.children.append(node)

    def clone(self, clone_parent, old_to_new, callpaths, roots):
        # construct clone from clone_parent
        clone_parent_callpath = ()
        if clone_parent is not None:
            clone_parent_callpath = clone_parent.callpath
        clone_callpath = clone_parent_callpath + (self.callpath[-1],)

        # if clone was already made, get it, else make it
        if clone_callpath in callpaths:
            clone = callpaths[clone_callpath]
        else:
            clone = Node(clone_callpath, clone_parent)
            callpaths[clone_callpath] = clone
            # handle the case where clone is a root
            if clone_parent is None:
                roots.add(clone)
            else:
                # clone isn't a root, update parent's children list
                clone_parent.add_child(clone)

        # update mapping from old to new
        old_to_new[self] = clone

        return clone

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

    def __eq__(self, other):
        return (self.callpath == other.callpath)

    def __lt__(self, other):
        return (self.callpath < other.callpath)
