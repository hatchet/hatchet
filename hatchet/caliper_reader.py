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
from ccnode import CCNode


class CaliperReader:
    """ Reads in the various sections of a Caliper json file. Builds a calling
        context tree and a dataframe with values for various metrics
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

    # column name of path for each record in dataframe
    path_column_name = '_path'

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

    def create_cctree(self):
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
        self.treeframe = pd.DataFrame(self.json_data, columns=self.json_columns)

        # initialize mapping from json ccnode index to calling context tree node
        self.idx_to_ccnode = {}

        # build tree out of each record's associated calling context tree node
        self.root = None
        self.treeframe[name_column_name].apply(self.create_lineage)
        if self.root is None:
            raise CaliperFormatError('Missing root ccnode in file.')

        # create paths for each ccnode
        self.dfs_assign_paths(self.root)

        # add path column for each record/row
        ccnode_idx_to_path = lambda idx: self.idx_to_ccnode[idx].callpath
        ccnode_idx_column = self.treeframe[name_column_name]
        path_column = ccnode_idx_column.map(ccnode_idx_to_path)
        self.treeframe[self.path_column_name] = path_column

        # some columns need to be converted from their nodes section index to
        # the label in that node (e.g. file is 5 but really is foo.c)
        idx_to_label = lambda idx: self.json_nodes[idx].get(self.node_label_key)
        old_columns = self.treeframe[metadata_column_names]
        new_columns = old_columns.applymap(idx_to_label)
        self.treeframe[metadata_column_names] = new_columns

        # assign indices for dataframe
        indices = [self.path_column_name, 'mpi.rank']
        self.treeframe.set_index(indices, drop=False, inplace=True)

        return (self.root, self.treeframe)

    def create_lineage(self, json_nodes_idx):
        """This function is applied to each row of the dataframe, and builds
           a node for that corresponding row, and all of its un-created parents.
        """
        # get the corresponding ccnode if it exists
        current_json_nodes_idx = json_nodes_idx
        current_ccnode = self.idx_to_ccnode.get(current_json_nodes_idx)

        # if current already existed, then so do its parents in the cctree
        if current_ccnode is not None:
            return

        # otherwise, create ccnode for current and add to map so we don't
        # potentially recreate it later
        current_json_node = self.json_nodes[current_json_nodes_idx]
        current_name = current_json_node[self.node_label_key]
        current_ccnode = CCNode((current_name,), None)
        self.idx_to_ccnode[current_json_nodes_idx] = current_ccnode

        # this loop builds ccnodes for ancestry of current;
        # this loop breaks on either of two conditions:
        #   1) for the very first record, we will go all the way to the root
        #      and create the root ccnode
        #   2) every other time, we will go up as long as the parent
        #      does not exist, if the parent exists, it means we've
        #      already traversed to the root during a previous iteration
        while True:

            # save current's value and increment it to be parent
            child_json_node = current_json_node
            child_ccnode = current_ccnode
            current_json_nodes_idx = child_json_node.get(self.node_parent_key)

            # current json ccnodes index is None which means child is root
            # ccnode; no more ccnodes to be created so break
            if current_json_nodes_idx is None:
                # save calling context tree root
                self.root = child_ccnode
                break

            # check if ccnode has already been created for current
            current_ccnode = self.idx_to_ccnode.get(current_json_nodes_idx)

            # current ccnode already existed; child ccnode has not had its
            # parent set yet because it was created in one of two areas:
            #   1) above when its record was read in (no linked parent)
            #   2) below when we create 'current' (future child; no linked
            #      parent)
            # because child is new, parent does not have child in children
            if current_ccnode is not None:
                # update links between child and current
                child_ccnode.parent = current_ccnode
                current_ccnode.add_child(child_ccnode)
                break

            # otherwise, we build a new ccnode, link it with child, and
            # update mapping so we don't potentially recreate current later
            current_json_node = self.json_nodes[current_json_nodes_idx]
            current_name = current_json_node[self.node_label_key]
            current_ccnode = CCNode((current_name,), None)
            child_ccnode.parent = current_ccnode
            current_ccnode.add_child(child_ccnode)
            self.idx_to_ccnode[current_json_nodes_idx] = current_ccnode

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
