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

        # TODO: optional (drop on ranks or threads)
        graphframe2.drop_index_levels()

        grouped_dataframe = graphframe2.dataframe.groupby(groupby_column).agg(
            agg_function
        )

        return grouped_dataframe

    # Outputs the max to avg values for user specified column
    # TODO: drop other metric columns and inplace?
    def find_load_imbalance(self, graphframe, metric_column="time", inplace=False):
        # Create a copy of the GraphFrame.
        graphframe2 = graphframe.deepcopy()
        graphframe3 = graphframe.deepcopy()

        # Drop all index levels in gf2's DataFrame except 'node', computing the
        # average time spent in each node.
        graphframe2.drop_index_levels(function=np.mean)

        # Drop all index levels in a copy of gf3's DataFrame except 'node', this
        # time computing the max time spent in each node.
        graphframe3.drop_index_levels(function=np.max)

        # Compute the imbalance by dividing the 'time' column in the max DataFrame
        # (i.e., gf3) by the average DataFrame (i.e., gf2). This creates a new column
        # called 'imbalance' in gf2's DataFrame.
        graphframe2.dataframe["imbalance"] = graphframe3.dataframe[metric_column].div(
            graphframe2.dataframe[metric_column]
        )
        graphframe2.default_metric = "imbalance"

        return graphframe2

    def find_hot_paths(
        self,
        graphframe,
        drop_ranks=False,
        drop_threads=False,
        rank=None,
        thread=None,
        metric_column="time (inc)",
        threshold=0.5,
    ):
        """Identifies hot paths for a given metric and a threshold."""

        def _check_hot_nodes(dataframe, node, hot_nodes, callpath):
            if node.children:
                for child in node.children:
                    if rank is None and thread is None:
                        parent_value = dataframe.at[(node), metric_column]
                        child_value = dataframe.at[(child), metric_column]
                    elif rank is None:
                        parent_value = dataframe.at[(node, thread), metric_column]
                        child_value = dataframe.at[(child, thread), metric_column]
                    elif thread is None:
                        parent_value = dataframe.at[(node, rank), metric_column]
                        child_value = dataframe.at[(child, rank), metric_column]
                    else:
                        parent_value = dataframe.at[(node, rank, thread), metric_column]
                        child_value = dataframe.at[(child, rank, thread), metric_column]
                    callpath.append(child)
                    if child_value < (threshold * parent_value):
                        _check_hot_nodes(dataframe, child, hot_nodes, callpath)
                    else:
                        hot_nodes.append((child, [node for node in callpath]))
                        callpath.pop()
            callpath.pop()

        if "inc" not in metric_column:
            raise ValueError("Only inclusive metrics can be used.")

        hot_nodes_paths = []
        # TODO: drop only ranks or thread
        """if drop_ranks or drop_threads:
            graphframe2 = graphframe.deepcopy()
            if drop_ranks:
                drop_ranks
            if drop_threads:
                drop_threads"""

        for root in graphframe.graph.roots:
            _check_hot_nodes(
                graphframe.dataframe, root, hot_nodes_paths, callpath=[root]
            )

        return hot_nodes_paths

    def calculate_speedup_efficiency(
        self, graphframes_pes=[], metric_columns=["time", "time (inc)"], inplace=False
    ):
        def _calculate(graphframe1, graphframe2, pe1, pe2):
            """Calculates speedup and efficiency.
            Creates a new graphframe and adds <metric>-<spdup/efc>(pe1xpe2)
            columns to its dataframe.
            """
            graphframe_spdup_efc = graphframe1 / graphframe2

            for metric in metric_columns:
                graphframe_spdup_efc.dataframe[
                    "{}-{}({}x{})".format(metric, "efc", pe1, pe2)
                ] = (graphframe_spdup_efc.dataframe[metric] / pe2)

                graphframe_spdup_efc.dataframe = graphframe_spdup_efc.dataframe.rename(
                    columns={metric: "{}-{}({}x{})".format(metric, "spdup", pe1, pe2)}
                )
            return graphframe_spdup_efc

        def _merge_columns(graphframe_from, graphframes_to, columns):
            """Merge two dataframes. This function is used only if
            inplace=True. Adds speedup and efficiency columns to the original
            graphframe without ading/removing any index (how=left).
            """
            for graphframe in graphframes_to:
                graphframe.dataframe = graphframe.dataframe.join(
                    graphframe_from.dataframe[columns], how="left"
                )

        if graphframes_pes:
            # Sort the graphframes by their pes before the division operation
            graphframes_pes = sorted(graphframes_pes, key=lambda x: x[1])
            graphframe1 = graphframes_pes[0][0].deepcopy()
            graphframe2 = graphframes_pes[1][0].deepcopy()
            graphframe1_pe = graphframes_pes[0][1]
            graphframe2_pe = graphframes_pes[1][1]

            # Original graph structures won't be changed even when inplace=True.
            graphframe_spdup_efc = _calculate(
                graphframe1,
                graphframe2,
                graphframe1_pe,
                graphframe2_pe,
            )

            # add speedup and efficiency columns to original graphframes.
            # we don't change the graph structure, just adding columns to the
            # dataframe.
            if inplace:
                merge_metric_columns = []
                for metric_column in graphframe_spdup_efc.dataframe.columns:
                    if "spdup" in metric_column or "efc" in metric_column:
                        merge_metric_columns.append(metric_column)

                _merge_columns(
                    graphframe_spdup_efc,
                    [graphframes_pes[0][0], graphframes_pes[1][0]],
                    merge_metric_columns,
                )

            return graphframe_spdup_efc
