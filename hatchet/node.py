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
    """A node in the graph. The node only stores its frame."""

    def __init__(self, frame_obj, parent):
        self.frame = frame_obj

        self.parents = []
        if parent is not None:
            self.add_parent(parent)
        self.children = []

    def add_parent(self, node):
        """Adds a parent to this node's list of parents."""
        assert isinstance(node, Node)
        self.parents.append(node)

    def add_child(self, node):
        """Adds a child to this node's list of children."""
        assert isinstance(node, Node)
        self.children.append(node)

    def check_dag_equal(self, other, vs=None, vo=None):
        """Check if DAG rooted at self has the same structure as that rooted at
        other.
        """
        if vs is None:
            vs = set()
        if vo is None:
            vo = set()

        vs.add(id(self))
        vo.add(id(other))

        # if number of children do not match, then nodes are not equal
        if len(self.children) != len(other.children):
            return False

        # sort children of each node by its frame
        ssorted = sorted(self.children, key=lambda x: x.frame)
        osorted = sorted(other.children, key=lambda x: x.frame)

        for self_child, other_child in zip(ssorted, osorted):
            # if frames do not match, then nodes are not equal
            if self_child.frame != other_child.frame:
                return False

            visited_s = id(self_child) in vs
            visited_o = id(other_child) in vo

            # check for duplicate nodes
            if visited_s != visited_o:
                return False

            # skip visited nodes
            if visited_s or visited_o:
                continue

            # recursive check for node equality
            if not self_child.check_dag_equal(other_child, vs, vo):
                return False

        return True

    def traverse(self, order="pre"):
        """Traverse the tree depth-first and yield each node."""
        if order == "pre":
            yield self

        for child in self.children:
            for item in child.traverse(order):
                yield item

        if order == "post":
            yield self

    def traverse_bf(self):
        """Traverse the tree breadth-first and yield each node."""
        yield self
        last = self

        for node in self.traverse_bf():
            for child in node.children:
                yield child
                last = child
            if last == node:
                return

    def __hash__(self):
        return hash(id(self))

    def __eq__(self, other):
        return id(self) == id(other)

    def __lt__(self, other):
        return id(self) < id(other)

    def __str__(self):
        """Returns a string representation of the node."""
        return str(self.frame)
