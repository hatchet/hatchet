# Copyright 2021-2022 University of Maryland and other Hatchet Project
# Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import pandas as pd
import numpy as np


class Chopper:
    """High-level API for performance analysis."""

    def flat_profile(self, graphframe, groupby_column=None, as_index=True):
        """Generates flat profile for a given graphframe.
        Returns a new dataframe."""
        graphframe2 = graphframe.deepcopy()

        if groupby_column is None:
            groupby_column = "name"

        # TODO: change drop_index_levels(). Drop only ranks or threads.
        graphframe2.drop_index_levels()

        result_dataframe = graphframe2.dataframe.groupby(
            groupby_column, as_index=as_index
        ).sum()
        result_dataframe = result_dataframe.sort_values(
            by=[graphframe.default_metric], ascending=False
        )

        return result_dataframe

    def flatten(self, graphframe, groupby_column="name"):
        """
        Flattens the graphframe by changing its graph structure and the dataframe.
        Returns a new graphframe.
        """
        result_graphframe = graphframe.groupby_aggregate(groupby_column, "sum")

        return result_graphframe

    def to_callgraph(self, graphframe):
        """
        Converts a CCT to a callgraph.
        Returns a new graphframe.
        """

        # TODO: provide hierarchy information in the graphframe metadata to access the
        #       hierarchy of the input nodes - currently using function name
        result_graphframe = graphframe.groupby_aggregate("name", "sum")

        return result_graphframe

    def load_imbalance(self, graphframe, metric_columns=None, threshold=None):
        """Calculates load imbalance for given the metric column(s).
        Takes a graphframe and a list of metric column(s) to calculate
        load imbalance.
        It takes a threshold value to filter out the insignificant nodes
        from the graphframe. The threshold parameter takes a percentage.
        For example, threshold=0.01 on time metric filters out the nodes
        that the program spends less than 1% of the total execution time.
        Returns a new graphframe with corresponding metric.imbalance column(s).
        """

        def _update_and_add_columns(dataframe, old_column_name, new_column):
            """Rename some existing columns and create new ones."""
            # rename columns: '<metric>.mean'
            dataframe.rename(
                columns={old_column_name: old_column_name + ".mean"}, inplace=True
            )
            # create columns: '<metric>.max'
            dataframe[old_column_name + ".max"] = new_column

        def _update_metric_lists(metric_types, metric):
            """Update graphframe.inc_metrics and graphframe.exc_metrics
            lists after renaming/creating columns"""
            metric_types.append(metric + ".mean")
            metric_types.append(metric + ".max")

        # Create a copy of the GraphFrame. 'graphframe2' and 'graphframe3' should
        # have the same graph (with the same node references) for div() function to
        # work properly. For that, 'graphframe3' should be the 'shallow' copy of
        # graphframe2.
        graphframe2 = graphframe.deepcopy()
        graphframe3 = graphframe2.copy()

        # Drop all index levels in gf2's DataFrame except 'node', computing the
        # average time spent in each node.
        graphframe2.drop_index_levels(function=np.mean)

        # Drop all index levels in a copy of gf3's DataFrame except 'node',
        # computing the max time spent in each node.
        graphframe3.drop_index_levels(function=np.max)

        # Use default_metric if not given.
        if metric_columns is None:
            metric_columns = [graphframe.default_metric]
        # Convert to a list if the metrics are not given as a list.
        elif not isinstance(metric_columns, list):
            metric_columns = [metric_columns]

        # Filter the nodes whose metric
        # value is less than <threshold> percent
        # of the root node.
        metric_threshold = {}
        if threshold is not None:
            for metric in metric_columns:
                # find the inc metric to calculate the
                # total value of the metric.
                if metric not in graphframe3.inc_metrics:
                    metric_inc = (
                        metric + graphframe3.metadata["hatchet_inclusive_suffix"]
                    )
                else:
                    metric_inc = metric

                root_metrics = []

                # find the largest value if there are multiple roots.
                for root in graphframe3.graph.roots:
                    root_metrics.append(graphframe3.dataframe.loc[root, metric_inc])

                # in-place ascending sort.
                root_metrics.sort()
                total = root_metrics[-1]
                metric_threshold[metric] = total * threshold

        graphframe2.inc_metrics = []
        graphframe2.exc_metrics = []
        # For each column/metric for which we want to
        # calculate load imbalance
        for metric in metric_columns:
            # Update/rename existing columns on graphframe2.dataframe
            # by adding .mean for already existing columns and create
            # new columns by adding .max to the corresponding
            # columns on graphframe3.
            _update_and_add_columns(
                graphframe2.dataframe, metric, graphframe3.dataframe[metric]
            )

            # Add new columns to .inc_metrics or .exc_metrics.
            if metric in graphframe3.inc_metrics:
                _update_metric_lists(graphframe2.inc_metrics, metric)
            elif metric in graphframe3.exc_metrics:
                _update_metric_lists(graphframe2.exc_metrics, metric)

            # filter out the nodes if their max metric value across
            # processes/threads is less than threshold% of the total
            # execution time.
            if threshold is not None:
                graphframe2 = graphframe2.filter(
                    lambda x: x[metric + ".max"] > metric_threshold[metric]
                )

            # Calculate load imbalance for every given metric
            # by calculating max-to-mean ratio.
            graphframe2.dataframe[metric + ".imbalance"] = graphframe2.dataframe[
                metric + ".max"
            ].div(graphframe2.dataframe[metric + ".mean"])

        # default metric will be imbalance when user print the tree
        graphframe2.default_metric = metric_columns[0] + ".imbalance"
        # sort by default_metric's load imbalance
        graphframe2.dataframe = graphframe2.dataframe.sort_values(
            by=[graphframe2.default_metric], ascending=False
        )
        return graphframe2

    def hot_path(
        self, graphframe, start_node=None, metric=None, threshold=0.5, callpath=[]
    ):
        """Returns the hot_path function.
        Inputs:
         - start_node (optional): Start node of the hot path can be given.
         Default: the root node that has the largest metric value.
         - metric: A numerical metric on the dataframe.
         Default: graphframe.default_metric
         - threshold: Threshold for parent-child comparison (parent <= child/2).
         Default: 0.5
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
                    # return hotpath since child's metric value is
                    # not greater than threshold * parent's metric.
                    callpath.append(child)
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

    @staticmethod
    def multirun_analysis(
        graphframes=[],
        pivot_index="num_processes",
        columns=["name"],
        metric="time",
        threshold=None,
    ):
        """Creates a pivot table.
        Inputs:
         - graphframes: A list of graphframes.
         - pivot_index: The metric in each graphframe's metadata used to index the pivot table.
         Default: num_processes
         - columns: The non-numerical metric over which the pivot table's column values are aggregated.
         Default: name
         - metric: The numerical metric which is aggregated to form the pivot table's column values.
         Default: time
         - threshold: The threshold for filtering metric rows of the graphframes.
        Output:
         - a pivot table
        """

        assert (
            graphframes is not None and len(graphframes) >= 2
        ), "function param 'graphframes' requires at least two graphframe objects"

        if not isinstance(columns, list):
            columns = [columns]

        for gf in graphframes:
            assert (
                pivot_index in gf.metadata.keys()
            ), "{} missing from GraphFrame metadata: use update_metadata() to specify.".format(
                pivot_index
            )
            assert (
                metric in gf.dataframe.columns
            ), "{} metric not present in all graphframes".format(metric)
            for column in columns:
                assert (
                    column in gf.dataframe.columns
                ), "{} column not present in all graphframes".format(column)

        dataframes = []
        for gf in graphframes:
            gf_copy = gf.deepcopy()
            gf_copy.drop_index_levels()

            # Grab the pivot_index from the metadata, store this as a new
            # column in the DataFrame.
            pivot_val = gf.metadata[pivot_index]
            gf_copy.dataframe[pivot_index] = pivot_val

            # Filter the dataframe, keeping only the rows that are above the threshold
            if threshold is not None:
                filtered_rows = gf_copy.dataframe.apply(
                    lambda x: x[metric] > threshold, axis=1
                )
                gf_copy.dataframe = gf_copy.dataframe[filtered_rows]

            # Insert the graphframe's dataframe into a list.
            dataframes.append(gf_copy.dataframe)

        # Concatenate all DataFrames into a single DataFrame called result.
        result = pd.concat(dataframes)

        pivot_df = result.pivot_table(index=pivot_index, columns=columns, values=metric)

        return pivot_df
