# Copyright 2021 University of Maryland and other Hatchet Project
# Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import numpy as np


class PerformanceAnalyzer:
    """High-level API for performance analysis."""

    # Converts a tree/graph to a flat profile on any column.
    def flat_profile(
        self,
        graphframe,
        groupby_column="time",
        drop_ranks=True,
        drop_threads=True,
        agg_function=np.mean,
    ):
        graphframe2 = graphframe.deepcopy()

        # TODO: change drop_index_levels(). Drop only ranks or threads.
        graphframe2.drop_index_levels()

        grouped_dataframe = graphframe2.dataframe.groupby(groupby_column).agg(
            agg_function
        )

        return grouped_dataframe

    # Outputs the max to avg values for user specified column.
    def find_load_imbalance(self, graphframe, metric_columns=["time"]):
        # Create a copy of the GraphFrame.
        graphframe2 = graphframe.deepcopy()
        graphframe3 = graphframe.deepcopy()

        # Drop all index levels in gf2's DataFrame except 'node', computing the
        # average time spent in each node.
        graphframe2.drop_index_levels(function=np.mean)

        # Drop all index levels in a copy of gf3's DataFrame except 'node', this
        # time computing the max time spent in each node.
        graphframe3.drop_index_levels(function=np.max)

        for column in graphframe3.dataframe.columns:
            # don't rename or create if column is not in inc/exc metrics.
            if column in graphframe3.inc_metrics or column in graphframe3.exc_metrics:
                # rename columns: '<metric>.mean'
                graphframe2.dataframe.rename(
                    columns={column: column + ".mean"}, inplace=True
                )
                # create columns: '<metric>.max'
                graphframe2.dataframe[column + ".max"] = graphframe3.dataframe[column]

            if column in metric_columns:
                # divide metric columns: max/min
                graphframe2.dataframe[column + ".imbalance"] = graphframe2.dataframe[
                    column + ".max"
                ].div(graphframe2.dataframe[column + ".mean"])

        # default metric will be imbalance when user print the tree
        graphframe2.default_metric = metric_columns[0] + ".imbalance"
        return graphframe2

    # The starting node can be specified using the 'parent' parameter.
    # Returns the hot node.
    # Exp: analyzer.find_hot_node(graphframe, root_node)
    def find_hot_node(self, graphframe, parent, metric="time (inc)", threshold=0.5):

        parent_metric = graphframe.dataframe.loc[parent, metric]
        sorted_child_metric = []
        # Get all children nodes with their metric values and append
        # them to a list.
        for child in parent.children:
            child_metric = graphframe.dataframe.loc[child, metric]
            sorted_child_metric.append((child, child_metric))

        if sorted_child_metric:
            # sort children by their metric values.
            sorted_child_metric.sort(key=lambda x: x[1], reverse=True)
            child = sorted_child_metric[0][0]
            child_metric = sorted_child_metric[0][1]
            if child_metric < (threshold * parent_metric):
                # return parent if its metric * threshold is
                # greater than child metric.
                return parent
            else:
                # continue from child if its metric is greater than
                # threshold * parent's metric.
                # For example, child_metric >= parent_metric/2
                return self.find_hot_node(graphframe, child, metric)

        return parent

    # Returns a call path from given start node to end node.
    # For example, this function can be used after getting the hot node.
    # Exp: analyzer.get_call_path(graphframe, root_node, hot_node, callpath=[])
    def get_call_path(self, graphframe, start_node, end_node, callpath=[]):
        callpath.append(start_node)

        # stop recursive calls if start_node == end_node
        if start_node == end_node:
            if len(callpath) == 1:
                return callpath
            else:
                return True

        # iteratively look at each child starting from the
        # start node.
        for child in start_node.children:
            found = self.get_call_path(graphframe, child, end_node, callpath)
            if found:
                # create a graphframe that includes only the nodes
                # from the call path.
                hot_graphframe = graphframe.filter(
                    lambda x: x.node in callpath, squash=True
                )
                return (callpath, hot_graphframe)
            else:
                callpath.pop()
