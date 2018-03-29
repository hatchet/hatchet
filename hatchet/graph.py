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
        # check for invalid arguments
        if not isinstance(other, Graph):
            raise ValueError('other is not a Graph.')
        if (not isinstance(old_to_new, dict) or
            not all(isinstance(x, Node) for x in old_to_new.keys()) or
            not all(isinstance(x, Node) for x in old_to_new.values())):
            raise ValueError('old_to_new is not a dict of Node to Node.')

        # function used to clone and merge trees in graph
        def construct_union(root, clone_parent, old_to_new, unioned_roots):
            # construct clone from clone_parent
            clone_parent_callpath = ()
            if clone_parent is not None:
                clone_parent_callpath = clone_parent.callpath
            clone_callpath = clone_parent_callpath + (root.callpath[-1],)
            clone = Node(clone_callpath, clone_parent)

            # handle the case where clone is a root
            if clone_parent is None:
                if clone in unioned_roots:
                    # duplicate root, get original to update mapping later
                    clone = unioned_roots[clone]
                else:
                    # clone root is the original, set as new root
                    unioned_roots[clone] = clone
            else:
                # clone isn't a root, update parent's children list
                clone_parent.add_child(clone)

            # update mapping from old to new
            old_to_new[root] = clone

            # clone and union all children
            for child in root.children:
                construct_union(child, clone, old_to_new, unioned_roots)

        # clone, filter, and merge graphs
        unioned_roots = {}
        for root in self.roots + other.roots:
            construct_union(root, None, old_to_new, unioned_roots)
        unioned_roots = unioned_roots.keys()

        return Graph(roots=unioned_roots)

    def __str__(self):
        """ Returns a string representation of the graph.
        """
        return self.graph_as_text().encode('utf-8')
