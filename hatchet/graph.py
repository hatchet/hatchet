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

from hatchet.external.printtree import trees_as_text
from node import Node


class Graph:
    """ Class representing a forest of trees from one dataset.
    """

    def __init__(self, roots):
        if roots is not None:
            self.roots = roots

    def to_string(self, roots=None, dataframe=None,
            metric='CPUTIME (usec) (I)', name='name', context='file', rank=0,
            threshold=0.01, unicode=True, color=True):
        """ Function to print all trees in a graph with or without some
            metric attached to each node.
        """
        if roots is None:
            roots = self.roots

        result = trees_as_text(roots, dataframe, metric, name, context, rank,
                               threshold, unicode=unicode, color=color)

        return result

    def clone_tree(self, root, clone_parent, old_to_new, new_to_old):
        clone_parent_callpath = ()
        if clone_parent is not None:
            clone_parent_callpath = clone_parent.callpath
        clone_callpath = clone_parent_callpath + (root.callpath[-1],)
        clone = Node(clone_callpath, clone_parent)
        old_to_new[root] = clone
        new_to_old[clone] = root
        if clone_parent is not None:
            clone_parent.add_child(clone)
        for child in root.children:
            self.clone_tree(child, clone, old_to_new, new_to_old)
        return clone

    def merge_trees(self, into, using, old_to_new, new_to_old):
        # we know into and using have the same callpath, so the mapping of old
        # nodes to new nodes should have all old nodes of the same callpath
        # point to only one new node to uniquify new nodes
        old_to_new[new_to_old[using]] = into

        # review all of using's children
        for using_child in using.children:
            if using_child in into.children:
                into_child = into.children[into.children.index(using_child)]
                self.merge_trees(into_child, using_child, old_to_new,
                                 new_to_old)
            else:
                into.add_child(using_child)
                using_child.parent = into

    def union(self, other, old_to_new):
        """Constructs a new graphframe from self and other.

        Longer description.

        Args:
            other (:obj:`GraphFrame`): The other graphframe to union with.

        Returns:
            A graphframe constructed from unioning self with other.

        Raises:
            ValueError: When an argument is invalid.
        """
        common_prefix_dict, new_to_old = {}, {}
        for root in self.roots + other.roots:
            new_root = self.clone_tree(root, None, old_to_new, new_to_old)
            if common_prefix_dict.get(new_root) is None:
                common_prefix_dict[new_root] = []
            common_prefix_dict[new_root].append(new_root)

        # merge common prefixes
        new_roots = []
        for common_prefix_roots in common_prefix_dict.itervalues():
            # merge other roots with common prefix into first root
            first_root = common_prefix_roots[0]
            new_roots.append(first_root)
            for other_root in common_prefix_roots[1:]:
                self.merge_trees(first_root, other_root, old_to_new, new_to_old)

        return Graph(roots=new_roots)

    def __str__(self):
        """ Returns a string representation of the graph.
        """
        return self.graph_as_text().encode('utf-8')
