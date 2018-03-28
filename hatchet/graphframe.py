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
        """Constructs new graph using only nodes in self's dataframe.

        Self's dataframe contains rows associated with nodes in self's graph.
        This function makes a copy of the dataframe and subset of graph with
        only nodes that are in the dataframe while attemping to maintain the
        original graph's structure.

        Returns:
            A graphframe constructed from self's dataframe.
        """
        # currently necessary hard-coded values
        self.node_column_name = 'node'

        # function used to clone, filter, and merge trees in graph
        def construct_rewiring(root, clone_parent, nodes_to_be_grafted,
                               old_to_new, grafted_roots):
            # only clone root if it's included in dataframe
            if root in nodes_to_be_grafted:
                # construct clone from clone_parent
                clone_parent_callpath = ()
                if clone_parent is not None:
                    clone_parent_callpath = clone_parent.callpath
                clone_callpath = clone_parent_callpath + (root.callpath[-1],)
                clone = Node(clone_callpath, clone_parent)

                # handle the case where clone is a root
                if clone_parent is None:
                    if clone in grafted_roots:
                        # duplicate root, get original to update mapping later
                        clone = grafted_roots[clone]
                    else:
                        # clone root is the original, set as new root
                        grafted_roots[clone] = clone
                else:
                    # clone isn't a root, update parent's children list
                    clone_parent.add_child(clone)

                # update mapping from old to new
                old_to_new[root] = clone
            else:
                clone = clone_parent
            for child in root.children:
                construct_rewiring(child, clone, nodes_to_be_grafted,
                                   old_to_new, grafted_roots)

        # clone, filter, and merge graph
        nodes_to_be_grafted = self.dataframe.index.levels[0]
        grafted_roots, old_to_new = {}, {}
        for root in self.graph.roots:
            construct_rewiring(root, None, nodes_to_be_grafted, old_to_new,
                               grafted_roots)
        grafted_roots = grafted_roots.keys()

        # copy old dataframe, map old nodes to new nodes, reset indices
        remapped_dataframe = self.dataframe.copy()
        old_node_column = remapped_dataframe[self.node_column_name]
        node_column_map = lambda x: old_to_new[x]
        new_node_column = old_node_column.map(node_column_map)
        remapped_dataframe[self.node_column_name] = new_node_column
        remapped_dataframe.reset_index(drop=True, inplace=True)
        indices = list(self.dataframe.index.names)
        if self.node_column_name in indices:
            indices.insert(0, indices.pop(indices.index(self.node_column_name)))
        remapped_dataframe.set_index(indices, drop=False, inplace=True)

        # construct grafted graphframe from remapped dataframe and grafted graph
        grafted_graphframe = GraphFrame()
        grafted_graphframe.dataframe = remapped_dataframe
        grafted_graphframe.graph = Graph(roots=list(grafted_roots))
        return grafted_graphframe
