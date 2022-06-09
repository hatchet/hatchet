# Copyright 2021 University of Maryland and other Hatchet Project
# Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import numpy as np


class Chopper:
    """High-level API for performance analysis."""

    def flat_profile(
        self,
        graphframe,
        groupby_column=None,
    ):
        """Generates flat profile for a given graphframe.
        Returns a new dataframe."""
        graphframe2 = graphframe.deepcopy()

        if groupby_column is None:
            groupby_column = "name"

        # TODO: change drop_index_levels(). Drop only ranks or threads.
        graphframe2.drop_index_levels()

        grouped_dataframe = graphframe2.dataframe.groupby(groupby_column).sum()

        return grouped_dataframe

    def calculate_load_imbalance(self, graphframe, metric_columns=None):
        """Calculates load imbalance for given metric column(s)
        Takes a graphframe and a list of metric column(s), and
        returns a new graphframe with metric.imbalance column(s).
        """

        def _update_columns(dataframe, old_column_name, new_column):
            """Rename some existing columns and create new ones."""
            # rename columns: '<metric>.mean'
            dataframe.rename(columns={column: old_column_name + ".mean"}, inplace=True)
            # create columns: '<metric>.max'
            dataframe[old_column_name + ".max"] = new_column

        def _update_metric_lists(metric_types):
            """Update graphframe.inc_metrics and graphframe.exc_metrics
            lists after renaming/creating columns"""
            metric_types.append(column + ".mean")
            metric_types.append(column + ".max")

        # Create a copy of the GraphFrame.
        graphframe2 = graphframe.deepcopy()
        graphframe3 = graphframe.deepcopy()

        # Drop all index levels in gf2's DataFrame except 'node', computing the
        # average time spent in each node.
        graphframe2.drop_index_levels(function=np.mean)

        # Drop all index levels in a copy of gf3's DataFrame except 'node',
        # computing the max time spent in each node.
        graphframe3.drop_index_levels(function=np.max)

        if metric_columns is None:
            metric_columns = [graphframe.default_metric]

        graphframe2.inc_metrics = []
        graphframe2.exc_metrics = []

        for column in graphframe3.inc_metrics:
            _update_columns(
                graphframe2.dataframe, column, graphframe3.dataframe[column]
            )
            _update_metric_lists(graphframe2.inc_metrics)

        for column in graphframe3.exc_metrics:
            _update_columns(
                graphframe2.dataframe, column, graphframe3.dataframe[column]
            )
            _update_metric_lists(graphframe2.exc_metrics)

        for column in metric_columns:
            # divide metric columns: max/mean
            graphframe2.dataframe[column + ".imbalance"] = graphframe2.dataframe[
                column + ".max"
            ].div(graphframe2.dataframe[column + ".mean"])

        # default metric will be imbalance when user print the tree
        graphframe2.default_metric = metric_columns[0] + ".imbalance"
        return graphframe2

    def hot_path(
        self, graphframe, start_node=None, metric=None, threshold=0.5, callpath=[]
    ):
        """Returns the hot_path function.
        Inputs:
         - start_node: Start node of the hot path should be given.
         - metric: A numerical metric on the dataframe
         - threshold: Threshold for parent-child comparison (parent <= child/2).
        Output:
         - hot_path: list of nodes, starting from the start node to the hot node.

        Example:
        root_node = graphframe.graph.roots[0]
        graphframe.hot_path(root_node)
        """

        def find_hot_path(graphframe, parent, metric, threshold, callpath):
            parent_metric = graphframe.dataframe.loc[parent, metric]
            sorted_child_metric = []
            # Get all children nodes with their metric values and append
            # them to a list.
            for child in parent.children:
                child_metric = graphframe.dataframe.loc[child, metric]
                sorted_child_metric.append((child, child_metric))

            if sorted_child_metric:
                # in-place sort children by their metric values.
                sorted_child_metric.sort(key=lambda x: x[1], reverse=True)
                child = sorted_child_metric[0][0]
                child_metric = sorted_child_metric[0][1]
                if child_metric < (threshold * parent_metric):
                    # return parent if its metric * threshold is
                    # greater than child metric.
                    return callpath
                else:
                    # continue from child if its metric is greater than
                    # threshold * parent's metric.
                    # For example, child_metric >= parent_metric/2
                    callpath.append(child)
                    return find_hot_path(graphframe, child, metric, threshold, callpath)

            return callpath

        # copy the graphframe not to modify the original graph
        gf_copy = graphframe.deepcopy()
        gf_copy.drop_index_levels()

        # choose the default metric if metric has not set
        if metric is None:
            metric = graphframe.default_metric

        # choose the root node that has the greatest metric value
        # if a start node is not specified
        if start_node is None:
            roots_metrics = []
            for root in gf_copy.graph.roots:
                roots_metrics.append((root, gf_copy.dataframe.loc[root, metric]))

            # in-place sort
            roots_metrics.sort(key=lambda x: x[1], reverse=True)
            start_node = roots_metrics[0][0]

        return find_hot_path(
            gf_copy, start_node, metric, threshold, callpath=[start_node]
        )
