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

    # key for column names section of json
    column_names_key = 'columns'

    # key for records/samples section of json
    records_key = 'data'

    # key for ccnodes section of json
    json_ccnodes_key = 'nodes'

    # this is a list containing all of the possible positional column names that
    # give the node position in each record
    positional_names_node = ['source.function#callpath.address', 'path']

    # this is the key that is used to get the app context name from a json
    # ccnode dictionary in the json_ccnodes list of dictionaries
    app_context_name_key = 'label'

    # this is the key that is used to get the parent index from a json ccnode
    # dictionary in the json_ccnodes list of dictionaries
    parent_key = 'parent'

    # comment
    callpath_column_name = 'callpath'

    def __init__(self, file_name):

        # column names, column metadata, records, and calling tree are stored in
        # the json file file_name
        with open(file_name) as fp:
            json_obj = json.load(fp)

        # this holds the names of each column of a record; some columns refer
        # to the position of a record, others refer to the metrics of a record
        self.column_names = json_obj[self.column_names_key]

        # records is a list of lists, each inner list is a record
        # containing both positional values and metrical values pertaining
        # to one caliper sample (i.e. one time caliper iterrupted and recorded)
        self.records = json_obj[self.records_key]

        # json_ccnodes is a list of dictionaries, each dictionary representing
        # one call context tree node (ccnode), containing the name of the app
        # context, and the parent app context index
        #
        # the parent is represented as an integer, which is an index into
        # json_ccnodes for the dictionary containing the name of the parent
        # app context and that parent's parent index, and so on, all the way up
        # until the root json ccnode dictionary has been reached
        self.json_ccnodes = json_obj[self.json_ccnodes_key]

    def create_cctree(self):
        """ Generates the calling context tree.
        """
        # initialize deliverables
        cct_root = None
        treeframe = None

        # each record (inner list in json_records) contains a reference to its
        # corresponding json ccnode (index into json_ccnodes); the json ccnode
        # is just a dictionary with the name of the app context and index to
        # that app context's parent within json_ccnodes; we are determining
        # where the callpath metric (json_ccnodes index) is within any record
        positional_idx_node = None
        for idx, column_name in enumerate(self.column_names):
            if column_name in self.positional_names_node:
                positional_idx_node = idx
                break
        if positional_idx_node == None:
            raise CaliperFormatError('Missing valid tree column in file.')

        # df_rows will be a list of lists, one inner list for each row of the
        # data frame, each row holds values of various metrics of one ccnode in
        # the calling context tree
        df_rows = []

        # idx_to_ccnode provides a mapping from json_ccnodes indices to ccnodes
        # in the calling context tree; necessary for creating a tree without
        # making any ccnode twice
        idx_to_ccnode = {}

        # loop through all records in records and build call tree;
        #
        # a record represents some ccnode in the calling context tree that has
        # performance data recorded for it;
        #
        # some ccnodes in the calling context tree may not have a record
        for record in self.records:

            # add current record to df data
            df_rows.append(record)

            # get the 'callpath metric'/app context (json_ccnodes index) for the
            # current record
            current_json_ccnodes_idx = record[positional_idx_node]

            # get the corresponding ccnode if it exists
            current_ccnode = idx_to_ccnode.get(current_json_ccnodes_idx)

            # if current already existed, then so do its parents in the cctree;
            # just add current's index in the df and continue
            if current_ccnode != None:
                continue

            # otherwise, create ccnode for current and add to map so we don't
            # potentially recreate it later
            current_json_ccnode = self.json_ccnodes[current_json_ccnodes_idx]
            current_name = current_json_ccnode[self.app_context_name_key]
            current_ccnode = CCNode(current_name, None)
            idx_to_ccnode[current_json_ccnodes_idx] = current_ccnode

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
                current_json_ccnodes_idx = child_json_ccnode.get(
                    self.parent_key)

                # current json ccnodes index is None which means child is root
                # ccnode; no more ccnodes to be created so break
                if current_json_ccnodes_idx == None:
                    # save calling context tree root
                    cct_root = child_ccnode
                    break

                # check if ccnode has already been created for current
                current_ccnode = idx_to_ccnode.get(current_json_ccnodes_idx)

                # current ccnode already existed; child ccnode has not had its
                # parent set yet because it was created in one of two areas:
                #   1) above when its record was read in (no linked parent)
                #   2) below when we create 'current' (future child; no linked
                #      parent)
                # because child is new, parent does not have child in children
                if current_ccnode != None:
                    # update links between child and current
                    child_ccnode.parent = current_ccnode
                    current_ccnode.add_child(child_ccnode)
                    break

                # otherwise, we build a new ccnode, link it with child, and
                # update mapping so we don't potentially recreate current later
                current_idx = current_json_ccnodes_idx
                current_json_ccnode = self.json_ccnodes[current_idx]
                current_name = current_json_ccnode[self.app_context_name_key]
                current_ccnode = CCNode(current_name, None)
                child_ccnode.parent = current_ccnode
                current_ccnode.add_child(child_ccnode)
                idx_to_ccnode[current_json_ccnodes_idx] = current_ccnode

        # calculate callpath for each calling context tree node
        self.dfs_assign_callpaths(cct_root)

        # each row contains an index to the json ccnode associated with the
        # record; we want to convert that index into the callpath of the
        # associated ccnode; that is how the treeframe will be linked to the cct
        for df_row in df_rows:
            json_ccnodes_idx = df_row[positional_idx_node]
            callpath = idx_to_ccnode[json_ccnodes_idx].callpath
            df_row[positional_idx_node] = callpath

        # the column names for the df
        df_columns = (self.column_names[0:positional_idx_node] +
                      [self.callpath_column_name] +
                      self.column_names[positional_idx_node + 1:])

        # create the pandas DataFrame using rows and column names
        treeframe = pd.DataFrame(df_rows, columns=df_columns)

        return cct_root, treeframe

    def dfs_assign_callpaths(self, root):
        if root.parent == None:
            parent_callpath = ()
        else:
            parent_callpath = root.parent.callpath.callpath
        root.callpath = CallPath(parent_callpath + (root.callpath.callpath,))
        for child in root.children:
            self.dfs_assign_callpaths(child)


class CaliperFormatError(Exception):
    """ Custom exception class.
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
