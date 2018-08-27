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

import matplotlib.cm
import matplotlib.colors

def trees_as_dot(roots, dataframe, metric, name, rank, threshold):
    """ Calls to_dot in turn for each tree in the graph/forest
    """
    text = 'strict digraph {\n' \
           'graph [bgcolor=transparent];\n' \
           'node [penwidth=4, shape=circle];\n' \
           'edge [penwidth=2];\n\n'

    all_nodes = ''
    all_edges = ''

    for root in roots:
        (nodes, edges) = to_dot(root, dataframe, metric, name, rank, threshold)
        all_nodes += nodes
        all_edges += edges

    text += (nodes + '\n' + edges + '\n}\n')
    return text


def to_dot(hnode, dataframe, metric, name, rank, threshold):
    """ Write to graphviz dot format """
    colormap = matplotlib.cm.RdYlBu
    min_time = dataframe[metric].min()
    max_time = dataframe[metric].max()

    def add_nodes_and_edges(hnode):
        weight = (dataframe.loc[(hnode, rank), metric] - min_time) / (max_time - min_time)
        color = matplotlib.colors.rgb2hex(colormap(1-weight))
        node_name = dataframe.loc[(hnode, rank), name]

        node_string = '"{0}" [color="{1}"];\n'.format(node_name, color)
        edge_string = ''

        if hnode.children is not None:
            for child in hnode.children:
                # add edges
                child_name = dataframe.loc[(child, rank), name]
                edge_string += '"{0}" -> "{1}";\n'.format(node_name, child_name)

                (nodes, edges) = add_nodes_and_edges(child)
                node_string += nodes
                edge_string += edges

        return (node_string, edge_string)

    return add_nodes_and_edges(hnode)

