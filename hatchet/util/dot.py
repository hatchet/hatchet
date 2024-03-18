# Copyright 2017-2023 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import matplotlib.cm
import matplotlib.colors

import numpy as np


def trees_to_dot(roots, dataframe, metric, meta_cb, name, rank, thread, threshold):
    """Calls to_dot in turn for each tree in the graph/forest."""
    text = (
        "strict digraph {\n"
        "graph [bgcolor=transparent];\n"
        "node [penwidth=4, shape=circle];\n"
        "edge [penwidth=2];\n\n"
    )

    all_nodes = ""
    all_edges = ""

    # call to_dot for each root in the graph
    visited = []
    for root in roots:
        (nodes, edges) = to_dot(
            root, dataframe, metric, meta_cb, name, rank, thread, threshold, visited
        )
        all_nodes += nodes
        all_edges += edges

    text += all_nodes + "\n" + all_edges + "\n}\n"

    return text


def to_dot(hnode, dataframe, metric, meta_cb, name, rank, thread, threshold, visited):
    """Write to graphviz dot format."""
    colormap = matplotlib.cm.Reds
    min_time = dataframe[metric].min()
    max_time = dataframe[metric].max()

    def add_nodes_and_edges(hnode):
        # set dataframe index based on if rank is a part of the index
        if "rank" in dataframe.index.names and "thread" in dataframe.index.names:
            df_index = (hnode, rank, thread)
        elif "rank" in dataframe.index.names:
            df_index = (hnode, rank)
        elif "thread" in dataframe.index.names:
            df_index = (hnode, thread)
        else:
            df_index = hnode

        node_meta = meta_cb(hnode)

        node_time = np.nan
        node_name = node_meta[name]

        try:
            node_time = dataframe.loc[df_index, metric]
        except KeyError:
            # In sparse format, it means this rank/thread didn't execute code
            # for this node
            pass

        node_id = hnode._hatchet_nid
        # only display those edges where child's metric is greater than
        # threshold
        children = []
        for child in hnode.children:
            if (
                "rank" in dataframe.index.names
                and "thread" in dataframe.index.names
            ):
                df_index = (child, rank, thread)
            elif "rank" in dataframe.index.names:
                df_index = (child, rank)
            elif "thread" in dataframe.index.names:
                df_index = (child, thread)
            else:
                df_index = child

            child_time = np.nan

            try:
                child_time = dataframe.loc[df_index, metric]
            except KeyError:
                pass

            if child_time >= threshold * max_time or np.isnan(child_time):
                (nodes, edges) = add_nodes_and_edges(child)
                if nodes != "" or edges != "":
                    # If both nodes/edges is empty string, that means all child nodes
                    # did not execute on the current rank/thread
                    children.append((child, nodes, edges))

        # only display nodes whose metric is greater than some threshold
        # or nodes with children whose metric is greater than some threshold
        if (node_time >= threshold * max_time or len(children) > 0) and (hnode not in visited):
            weight = (node_time - min_time) / (max_time - min_time)
            color = matplotlib.colors.rgb2hex(colormap(weight))

            node_string = '"{0}" [color="{1}", label="{2}" shape=oval];\n'.format(
                node_id, color, node_name
            )
            edge_string = ""
        else:
            node_string = ""
            edge_string = ""

        if hnode not in visited:
            visited.append(hnode)
            for child, child_nodes, child_edges in children:
                # add edges
                child_id = child._hatchet_nid

                edge_string += '"{0}" -> "{1}";\n'.format(node_id, child_id)
                node_string += child_nodes
                edge_string += child_edges

        return (node_string, edge_string)

    # call add_nodes_and_edges on the root
    return add_nodes_and_edges(hnode)
