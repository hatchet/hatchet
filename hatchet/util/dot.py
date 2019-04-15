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

import matplotlib.cm
import matplotlib.colors

def trees_to_dot(roots, dataframe, metric, name, rank, threshold):
    """ Calls to_dot in turn for each tree in the graph/forest
    """
    text = 'strict digraph {\n' \
           'graph [bgcolor=transparent];\n' \
           'node [penwidth=4, shape=circle];\n' \
           'edge [penwidth=2];\n\n'

    all_nodes = ''
    all_edges = ''

    # call to_dot for each root in the graph
    for root in roots:
        (nodes, edges) = to_dot(root, dataframe, metric, name, rank, threshold)
        all_nodes += nodes
        all_edges += edges

    text += (all_nodes + '\n' + all_edges + '\n}\n')
    return text


def to_dot(hnode, dataframe, metric, name, rank, threshold):
    """ Write to graphviz dot format """
    colormap = matplotlib.cm.Reds
    min_time = dataframe[metric].min()
    max_time = dataframe[metric].max()

    def add_nodes_and_edges(hnode):
        # set dataframe index based on if rank is a part of the index
        if 'rank' in dataframe.index.names:
            df_index = (hnode, rank)
        else:
            df_index = hnode
        node_time = dataframe.loc[df_index, metric]
        node_name = dataframe.loc[df_index, name]
        node_id = dataframe.loc[df_index, 'nid']
        # shorten names longer than 15 characters
        # if len(node_name) > 15:
        #     node_name = node_name[:6] + '...' + node_name[len(node_name)-6:]

        weight = (node_time - min_time) / (max_time - min_time)
        color = matplotlib.colors.rgb2hex(colormap(weight))

        # only display nodes whose metric is greater than some threshold
        if node_time >= threshold * max_time:
            node_string = '"{0}" [color="{1}", label="{2}" shape=oval];\n'.format(node_id, color, node_name)
            edge_string = ''

            # only display those edges where child's metric is greater than
            # threshold
            children = []
            for child in hnode.children:
                if 'rank' in dataframe.index.names:
                    df_index = (child, rank)
                else:
                    df_index = hnode
                child_time = dataframe.loc[df_index, metric]
                if child_time >= threshold * max_time:
                    children.append(child)

            for child in children:
                # add edges
                if 'rank' in dataframe.index.names:
                    child_id = dataframe.loc[(child, rank), 'nid']
                else:
                    child_id = dataframe.loc[child, 'nid']

                edge_string += '"{0}" -> "{1}";\n'.format(node_id, child_id)

                (nodes, edges) = add_nodes_and_edges(child)
                node_string += nodes
                edge_string += edges
        else:
            node_string = ''
            edge_string = ''

        return (node_string, edge_string)

    # call add_nodes_and_edges on the root
    return add_nodes_and_edges(hnode)

