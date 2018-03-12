##############################################################################
# Copyright (c) 2018, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# Written by Matthew Kotila <kotila1@llnl.gov>.
# LLNL-CODE-741008. All rights reserved.
#
# This file is part of Hatchet. For details, see:
# https://github.com/LLNL/hatchet
# Please also read the LICENSE file for the MIT License notice.
##############################################################################

import json
import pandas as pd
from node import Node
from graph import Graph


class CaliperReader:
    """ Reads in the various sections of a Caliper json file. Builds a graph
        and a dataframe with values for various metrics
        for each 'record' that Caliper produces and puts in the json file
    """

    # application/app context: a function, loop, statement, or annotated region
    # (some arbitrary section of code initiated by a caliper call and ended by
    # another caliper call), that can all be nested in one another in order to
    # build a path and subsequently a calling context tree

    # key for data/samples section of json
    json_data_key = 'data'

    # key for columns names section of json
    json_columns_key = 'columns'

    # key for column metadata section of json
    json_column_metadata_key = 'column_metadata'

    # key for nodes section of json
    json_nodes_key = 'nodes'

    # possible column names of name for each record in dataframe
    name_column_names = ['source.function#callpath.address', 'path']

    # column name of node for each record in dataframe
    node_column_name = 'node'

    # key used to get is_value boolean from json column metadata
    is_value_key = 'is_value'

    # key used to get label string from json node
    node_label_key = 'label'

    # key used to get parent integer from json node
    node_parent_key = 'parent'

    def __init__(self, file_name):
        # open and read json file
        with open(file_name) as fp:
            self.json_obj = json.load(fp)

        # get respective parts of json file
        self.json_data = self.json_obj[self.json_data_key]
        self.json_columns = self.json_obj[self.json_columns_key]
        self.json_column_metadata = self.json_obj[self.json_column_metadata_key]
        self.json_nodes = self.json_obj[self.json_nodes_key]

    def create_graph(self):
        """Creates the CCTree."""
        # some columns need their value mapped from index to label
        metadata_column_names = []
        for idx, column_metadata in enumerate(self.json_column_metadata):
            if column_metadata.get(self.is_value_key) is False:
                metadata_column_names.append(self.json_columns[idx])

        # the name column may come up under multiple names; find right one for
        # this json
        name_column_name = None
        for column_name in self.name_column_names:
            if column_name in self.json_columns:
                name_column_name = column_name
                break
        if name_column_name is None:
            raise CaliperFormatError('Missing valid tree column in file.')

        # now we can build the dataframe and rename columns
        self.dataframe = pd.DataFrame(self.json_data, columns=self.json_columns)

        # initialize mapping from json node index to calling context tree node
        self.idx_to_node = {}

        # build tree out of each record's associated calling context tree node
        self.graph_root = None
        self.dataframe[name_column_name].apply(self.create_lineage)
        if self.graph_root is None:
            raise CaliperFormatError('Missing root node in file.')

        # create paths for each node
        self.dfs_assign_paths(self.graph_root)

        # add node column to dataframe
        idx_to_node_map = lambda idx: self.idx_to_node[idx]
        node_idx_column = self.dataframe[name_column_name]
        node_column = node_idx_column.map(idx_to_node_map)
        self.dataframe[self.node_column_name] = node_column

        # some columns need to be converted from their nodes section index to
        # the label in that node (e.g. file is 5 but really is foo.c)
        idx_to_label = lambda idx: self.json_nodes[idx].get(self.node_label_key)
        old_columns = self.dataframe[metadata_column_names]
        new_columns = old_columns.applymap(idx_to_label)
        self.dataframe[metadata_column_names] = new_columns

        # assign indices for dataframe
        indices = [self.node_column_name, 'mpi.rank']
        self.dataframe.set_index(indices, drop=False, inplace=True)

        # add rows without metrics
        rows_not_in_dataframe = []
        for node in self.graph_root.traverse():
            if node not in self.dataframe.index:
                data = [None] * len(self.json_columns) + [node]
                index = self.json_columns + [self.node_column_name]
                row = pd.Series(data=data, index=index, name=(node, None))
                row.loc[name_column_name] = node.callpath[-1]
                rows_not_in_dataframe.append(row)
        self.dataframe = self.dataframe.append(rows_not_in_dataframe)

        graph = Graph([self.graph_root])
        return (graph, self.dataframe)

    def create_lineage(self, json_nodes_idx):
        """This function is applied to each row of the dataframe, and builds
           a node for that corresponding row, and all of its un-created parents.
        """
        # get the corresponding node if it exists
        current_json_nodes_idx = json_nodes_idx
        current_node = self.idx_to_node.get(current_json_nodes_idx)

        # if current already existed, then so do its parents in the graph
        if current_node is not None:
            return

        # otherwise, create node for current and add to map so we don't
        # potentially recreate it later
        current_json_node = self.json_nodes[current_json_nodes_idx]
        current_name = current_json_node[self.node_label_key]
        current_node = Node((current_name,), None)
        self.idx_to_node[current_json_nodes_idx] = current_node

        # this loop builds nodes for ancestry of current;
        # this loop breaks on either of two conditions:
        #   1) for the very first record, we will go all the way to the root
        #      and create the root node
        #   2) every other time, we will go up as long as the parent
        #      does not exist, if the parent exists, it means we've
        #      already traversed to the root during a previous iteration
        while True:

            # save current's value and increment it to be parent
            child_json_node = current_json_node
            child_node = current_node
            current_json_nodes_idx = child_json_node.get(self.node_parent_key)

            # current json nodes index is None which means child is root
            # node; no more nodes to be created so break
            if current_json_nodes_idx is None:
                # save calling context tree root
                self.graph_root = child_node
                break

            # check if node has already been created for current
            current_node = self.idx_to_node.get(current_json_nodes_idx)

            # current node already existed; child node has not had its
            # parent set yet because it was created in one of two areas:
            #   1) above when its record was read in (no linked parent)
            #   2) below when we create 'current' (future child; no linked
            #      parent)
            # because child is new, parent does not have child in children
            if current_node is not None:
                # update links between child and current
                child_node.parent = current_node
                current_node.add_child(child_node)
                break

            # otherwise, we build a new node, link it with child, and
            # update mapping so we don't potentially recreate current later
            current_json_node = self.json_nodes[current_json_nodes_idx]
            current_name = current_json_node[self.node_label_key]
            current_node = Node((current_name,), None)
            child_node.parent = current_node
            current_node.add_child(child_node)
            self.idx_to_node[current_json_nodes_idx] = current_node

    def dfs_assign_paths(self, root):
        parent_path = ()
        if root.parent is not None:
            parent_path = root.parent.callpath
        root.callpath = parent_path + (root.callpath[0],)
        for child in root.children:
            self.dfs_assign_paths(child)


class CaliperFormatError(Exception):
    """ Custom exception class.
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
