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


class CDBReader:
    """ Read in the various sections of a Caliper json file.
    """

    def __init__(self, file_name):
        json_obj = json.load(fp=open(name=file_name))
        self.file_name = file_name
        self.data = json_obj['data']
        self.columns = json_obj['columns']
        self.nodes = json_obj['nodes']
        self.num_pes = 0
        self.num_nodes = 0
        self.num_metrics = 0

    def create_cctree(self):
        """ Generates the calling context tree.
        """
        cct_root = None
        treeframe = None

        # NOTE: there are multiple data entries (samples) that
        #         reference the same node in the nodes array (what does this mean?)
        #         specifically 139, 170, and 188, all have the label
        #         'cali::Caliper::pull_snapshot' and each show up twice in data

        # get root node index for cctree creation
        if 'source.function#callpath.address' in self.columns:
            node_idx = self.columns.index('source.function#callpath.address')
        else:
            node_idx = self.columns.index('path')
        root_idx = self.data[0][node_idx]
        while self.nodes[root_idx].get('parent') != None:
            root_idx = self.nodes[root_idx].get('parent')

        idx_to_ccnode = {}
        ccnode_to_metric = {}
        callpath_to_metrics = {}
        list_metrics = []
        list_indices = []
        pes = set()
        num_columns = len(self.columns)

        # loop through each data, potentially making node, and then crawling up
        # each node's parents and potentially making nodes for each parent
        for data in self.data:

            # get parent of child node indices
            child = data[node_idx]
            parent = self.nodes[child].get('parent')

            # count number of processes
            pes.add(data[self.columns.index('mpi.rank')])

            # skip if this is root
            if parent == None: continue

            ccchild = idx_to_ccnode.get(child)
            ccparent = idx_to_ccnode.get(parent)

            if ccparent == None:
                if ccchild == None:
                    ccchild = CCNode(_callpath_tuple=None, _parent=None)
                ccparent = CCNode(_callpath_tuple=None, _parent=None)
                ccchild.parent = ccparent
                ccparent.add_child(node=ccchild)
                ccnode_to_metric[ccparent] = ([self.nodes[parent]['label'], ''] +
                                              [None] * num_columns)
            else:
                if ccchild == None:
                    ccchild = CCNode(_callpath_tuple=None, _parent=None)
                ccchild.parent = ccparent
                if ccchild not in ccparent.children:
                    ccparent.add_child(node=ccchild)

            # add to mapping for future retrieval
            idx_to_ccnode[child] = ccchild
            idx_to_ccnode[parent] = ccparent

            # map metric for child node
            ccnode_to_metric[ccchild] = [self.nodes[child]['label'], ''] + data

            # walk up parents
            child = parent
            parent = self.nodes[parent].get('parent')
            while 1:
                # child is the root node, no more ties to be created
                if parent == None: break

                # retrieve possible child and parent
                ccchild = idx_to_ccnode.get(child)
                ccparent = idx_to_ccnode.get(parent)

                # if parent existed, update links and end loop
                if ccparent != None:
                    ccchild.parent = ccparent
                    ccparent.add_child(node=ccchild)
                    break

                # create parent and update links between child and parent
                ccparent = CCNode(_callpath_tuple=None, _parent=None)
                ccchild.parent = ccparent
                ccparent.add_child(node=ccchild)

                # update mappings for indices and metrics
                idx_to_ccnode[parent] = ccparent
                ccnode_to_metric[ccparent] = ([self.nodes[parent]['label'], ''] +
                                              [None] * num_columns)

                # traverse to next parent
                child = parent
                parent = self.nodes[parent].get('parent')

        # must call the 'sole' metric 'CPUTIME (usec) (I)' as opposed to
        # 'count' or something else because printtree.py relies on this name
        self.columns[0] = 'CPUTIME (usec) (I)'

        self.dfs_build_callpaths(root=idx_to_ccnode[root_idx],
                                 list_metrics=list_metrics,
                                 list_indices=list_indices,
                                 ccnode_to_metric=ccnode_to_metric,
                                 node_idx=node_idx)

        # root ccnode is in map from nodes idx to ccnode at root_idx
        cct_root = idx_to_ccnode[root_idx]

        treeframe = pd.DataFrame(data=list_metrics, index=list_indices)
        columns = list(treeframe.columns.values)
        columns.insert(0, columns.pop(columns.index('CPUTIME (usec) (I)')))
        columns.insert(0, columns.pop(columns.index('file')))
        columns.insert(0, columns.pop(columns.index('name')))
        treeframe = treeframe[columns]
        treeframe['CPUTIME (usec) (I)'] = treeframe['CPUTIME (usec) (I)'].apply(func=lambda x: 0 if x != x else x)
        self.num_pes = len(pes)
        self.num_nodes = len(idx_to_ccnode)
        self.num_metrics = len(self.columns) - 1

        return cct_root, treeframe

    def dfs_build_callpaths(self, root, list_metrics, list_indices,
                            ccnode_to_metric, node_idx):
        """ Builds callpaths and dict for mapping callpath to metrics.
        """
        # get callpath for current node
        _callpath = (ccnode_to_metric[root][0],)
        if root.parent != None:
            _callpath = root.parent.callpath.callpath + _callpath
        root.callpath = CallPath(_callpath=_callpath)

        # create mapping from callpath to metrics
        list_indices.append(root.callpath)
        metric_list = ccnode_to_metric[root]
        metric_dict = {'name': metric_list[0], 'file': metric_list[1]}
        for idx, metric in enumerate(sequence=metric_list[2:]):
            if idx != node_idx:
                metric_dict[self.columns[idx]] = metric_list[idx + 2]
        list_metrics.append(metric_dict)

        # build callpaths for children
        for child in root.children:
            self.dfs_build_callpaths(root=child, list_metrics=list_metrics,
                                     list_indices=list_indices,
                                     ccnode_to_metric=ccnode_to_metric,
                                     node_idx=node_idx)
