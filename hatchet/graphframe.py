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

from hpctoolkit_reader import HPCToolkitReader
from caliper_reader import CaliperReader
import pandas as pd

class GraphFrame:
    """ This class associates the graph with a dataframe.
    """

    def __init__(self):
        self.num_pes = 0
        self.num_nodes = 0
        self.num_metrics = 0

        self.graph = None

    def from_hpctoolkit(self, dirname):
        reader = HPCToolkitReader(dirname)
        self.num_pes = reader.num_pes
        self.num_nodes = reader.num_nodes
        self.num_metrics = reader.num_metrics

        (self.graph, self.dataframe) = reader.create_graph()

    def from_caliper(self, filename):
        reader = CaliperReader(filename)

        (self.graph, self.dataframe) = reader.create_graph()

    def graft(self):
        """Constructs a new graphframe from self's dataframe.

        Self's dataframe contains rows associated with nodes in self's graph.
        This function makes a copy of the dataframe and subset of graph with
        only nodes that are in the dataframe while attemping to maintain the
        original graph's structure.

        Returns:
            A graphframe constructed from self's dataframe.
        """
        def construct_clone(root, clone_parent, node_column, old_to_new,
                            new_to_old, new_roots_dict):
            if root in node_column.values:
                clone_parent_callpath = ()
                if clone_parent is not None:
                    clone_parent_callpath = clone_parent.callpath
                clone_callpath = clone_parent_callpath + (root.callpath[-1],)
                clone = Node(clone_callpath, clone_parent)
                old_to_new[root] = clone
                new_to_old[clone] = root
                if clone_parent is not None:
                    clone_parent.add_child(clone)
                else:
                    if new_roots_dict.get(clone) is None:
                        new_roots_dict[clone] = []
                    new_roots_dict[clone].append(clone)
            else:
                clone = clone_parent
            for child in root.children:
                construct_clone(child, clone, node_column, old_to_new,
                                new_to_old, new_roots_dict)

        def merge_trees(into, using, old_to_new, new_to_old):
            # we know into and using have the same callpath, but the dataframe
            # should only use one of these as its reference node, use into
            old_to_new[new_to_old[using]] = into

            # review all using's children
            for using_child in using.children:
                if using_child in into.children:
                    into_child = into.children[into.children.index(using_child)]
                    merge_trees(into_child, using_child, old_to_new, new_to_old)
                else:
                    into.add_child(using_child)
                    using_child.parent = into

        # clone graph and filter
        node_column = self.dataframe[self.node_column_name]
        old_to_new, new_to_old = {}, {}
        new_roots_dict = {}
        for root in self.graph.roots:
            construct_clone(root, None, node_column, old_to_new, new_to_old,
                            new_roots_dict)

        # merge common prefixes
        new_roots = []
        for common_prefix_roots in new_roots_dict.itervalues():
            # merge all roots with common prefix into first
            first = common_prefix_roots[0]
            new_roots.append(first)
            for other_root in common_prefix_roots[1:]:
                merge_trees(first, other_root, old_to_new, new_to_old)

        # copy old dataframe, map old nodes to new nodes, reset indices
        old_to_new_map = lambda x: old_to_new[x]
        new_node_column = node_column.map(old_to_new_map)
        new_dataframe = self.dataframe.copy()
        new_dataframe[self.node_column_name] = new_node_column
        new_dataframe.reset_index(drop=True, inplace=True)
        indices = [self.node_column_name, self.rank_column_name]
        new_dataframe.set_index(indices, drop=False, inplace=True)

        # construct new graphframe out of new dataframe and graph
        new_graphframe = GraphFrame()
        new_graphframe.dataframe = new_dataframe
        new_graphframe.graph = Graph(roots=new_roots)
        return new_graphframe
