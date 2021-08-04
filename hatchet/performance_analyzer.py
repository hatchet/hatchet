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
