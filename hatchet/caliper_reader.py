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
from ccnode import CCNode, CallPath


class CaliperReader:
    """ Reads in the various sections of a Caliper json file. Builds a calling
        context tree and a pandas DataFrame with values for various metrics
        for each 'record' that Caliper produces and puts in the json file
    """

    # application/app context: a function, loop, statement, or annotated region
    # (some arbitrary section of code initiated by a caliper call and ended by
    # another caliper call), that can all be nested in one another in order to
    # build a callpath and subsequently a calling context tree

    # key for columns names section of json
    json_columns_key = 'columns'

    # key for data.json_data/samples section of json
    json_data_key = 'data'

    # key for nodes section of json
    json_nodes_key = 'nodes'

    # this is a list containing all of the possible positional column names that
    # give the node position in each record
    cali_name_column_names = ['source.function#callpath.address', 'path']

    # column name of file for each record in pandas DataFrame
    cali_file_column_names = ['source.file#cali.sampler.pc']

    # column name of file for each record in pandas DataFrame
    cali_line_column_names = ['source.line#cali.sampler.pc']

    # column name of callpath for each record in pandas DataFrame
    name_column_name = 'name'

    # column name of callpath for each record in pandas DataFrame
    file_column_name = 'file'

    # column name of callpath for each record in pandas DataFrame
    line_column_name = 'line'

    # column name of callpath for each record in pandas DataFrame
    callpath_column_name = 'callpath'

    # column name of process for each record in pandas DataFrame
    process_column_name = 'mpi.rank'

    # this is the key that is used to get the app context name from a json
    # ccnode dictionary in the json_nodes list of dictionaries
    node_label_key = 'label'

    # this is the key that is used to get the parent index from a json ccnode
    # dictionary in the json_nodes list of dictionaries
    node_parent_key = 'parent'

    def __init__(self, file_name):
        # column names, column metadata,.json_data, and calling tree are stored
        # in the json file file_name
        with open(file_name) as fp:
            self.json_obj = json.load(fp)

        # treeframe is a pandas DataFrame where each row represents one record
        # from the.json_data section of the json, and each column is a metrical
        # or positional value, with the names of such given in the column names
        # section of the json
        self.json_data = self.json_obj[self.json_data_key]
        self.json_columns = self.json_obj[self.json_columns_key]
        self.json_nodes = self.json_obj[self.json_nodes_key]

    def create_cctree(self):
        """Creates the CCTree."""
        # columns may come up under multiple names; find right one for this json
        cali_name_column_name = self.get_column_name(
            self.cali_name_column_names, self.json_columns)
        cali_file_column_name = self.get_column_name(
            self.cali_file_column_names, self.json_columns)
        cali_line_column_name = self.get_column_name(
            self.cali_line_column_names, self.json_columns)

        # we want to normalize the column names to much simpler names
        column_name_map = {cali_name_column_name: self.name_column_name,
                           cali_file_column_name: self.file_column_name,
                           cali_line_column_name: self.line_column_name}

        # now we can build the pandas DataFrame and rename columns
        self.treeframe = pd.DataFrame(self.json_data, columns=self.json_columns)
        self.treeframe = self.treeframe.rename(columns=column_name_map)

        # initialize mapping from json ccnode index to calling context tree node
        self.idx_to_ccnode = {}

        # build tree out of each record's associated calling context tree node
        self.root = None
        self.treeframe[self.name_column_name].apply(self.create_lineage)
        if self.root is None:
            raise CaliperFormatError('Missing root ccnode in file.')

        # create callpaths for each node
        self.dfs_assign_callpaths(self.root)

        # add callpaths as column for each record
        ccnode_idx_to_callpath = lambda x: self.idx_to_ccnode[x].callpath
        name_column = self.treeframe[self.name_column_name]
        callpath_column = name_column.map(ccnode_idx_to_callpath)
        self.treeframe[self.callpath_column_name] = callpath_column

        # some columns need to be converted from their nodes-section index to
        # the label in that node (e.g. file is 5 but really is foo.py)
        idx_to_label = lambda x: self.json_nodes[x][self.node_label_key]
        changed_column_names = [self.name_column_name, self.file_column_name,
                                self.line_column_name]
        old_columns = self.treeframe[changed_column_names]
        new_columns = old_columns.applymap(idx_to_label)
        self.treeframe[changed_column_names] = new_columns
        self.treeframe.set_index([self.callpath_column_name,
                                  self.process_column_name], drop=False,
                                 inplace=True)

        return (self.root, self.treeframe)

    def get_column_name(self, possible_column_names, actual_column_names):
        # one of the columns holds the node positional value for each record;
        # we want to find the column name for that column
        for column_name in possible_column_names:
            if column_name in actual_column_names:
                return column_name
        raise CaliperFormatError('Missing valid tree column in file.')

    def create_lineage(self, json_nodes_idx):
        # get the corresponding ccnode if it exists
        current_json_nodes_idx = json_nodes_idx
        current_ccnode = self.idx_to_ccnode.get(current_json_nodes_idx)

        # if current already existed, then so do its parents in the cctree
        if current_ccnode is not None:
            return

        # otherwise, create ccnode for current and add to map so we don't
        # potentially recreate it later
        current_json_ccnode = self.json_nodes[current_json_nodes_idx]
        current_name = current_json_ccnode[self.node_label_key]
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
            child_json_ccnode = current_json_ccnode
            child_ccnode = current_ccnode
            current_json_nodes_idx = child_json_ccnode.get(
                self.node_parent_key)

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
            current_json_ccnode = self.json_nodes[current_json_nodes_idx]
            current_name = current_json_ccnode[self.node_label_key]
            current_ccnode = CCNode((current_name,), None)
            child_ccnode.parent = current_ccnode
            current_ccnode.add_child(child_ccnode)
            self.idx_to_ccnode[current_json_nodes_idx] = current_ccnode

    def dfs_assign_callpaths(self, root):
        if root.parent is None:
            parent_callpath = ()
        else:
            parent_callpath = root.parent.callpath.callpath
        root.callpath = CallPath(parent_callpath + (root.callpath.callpath[0],))
        for child in root.children:
            self.dfs_assign_callpaths(child)


class CaliperFormatError(Exception):
    """ Custom exception class.
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
