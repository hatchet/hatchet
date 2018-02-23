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

from functools import total_ordering


class CCNode:
    """ A node in the tree.
    """

    def __init__(self, callpath, parent):
        self.callpath = callpath
        self.handle = CCNodeHandle(callpath)
        self.parent = parent
        self.children = []

    def add_child(self, node):
        """ Adds a child to this node.
        """
        assert isinstance(node, CCNode)
        self.children.append(node)

    def __iter__(self):
        """Traverse the tree depth-first and yield each node.
        """
        for child in self.children:
            for item in child:
                yield item

        yield self


@total_ordering
class CCNodeHandle:
    """The handle of any node is the hash of its callpath."""

    def __init__(self, callpath):
        self.callpath = callpath
        self.handle = hash(callpath)

    def __hash__(self):
        return self.handle

    def __eq__(self, other):
        return self.handle == other.handle

    def __lt__(self, other):
        return self.callpath < other.callpath
