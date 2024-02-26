# Copyright 2021-2024 University of Maryland and other Hatchet Project
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

    def load_imbalance(
        self, graphframe, metric_column=None, threshold=None, verbose=False
    ):
        """Calculates load imbalance for the given metric column.
        Takes a graphframe and a metric column to calculate the
        load imbalance.
        It takes a threshold value to filter out the insignificant nodes
        from the graphframe. The threshold parameter takes a percentage.
        For example, threshold=0.01 on time metric filters out the nodes
        that the program spends less than 1% of the max value of time metric.
        Returns a new graphframe with corresponding <metric>.imbalance column.
        If the verbose parameter is True, it provides frequency histogram,
        the top five ranks that have the highest metric value, and percentile
        information.
        """

        def _update_metric_lists(metric_type, metric):
            """Update graphframe.inc_metrics and graphframe.exc_metrics
            lists after renaming/creating columns"""
            metric_type.append(metric + ".mean")
            metric_type.append(metric + ".max")

        def _calculate_statistics(dataframe, metric_column, func):
            """Calculate frequency histogram and percentiles. Find the
            ranks that have the highest metric values."""
            index_names = list(dataframe.index.names)
            index_names.remove("node")

            # create dict that stores aggregation function for each column.
            # fuc = [np.mean, np.max] for the metric_column.
            agg_dict = {}
            for col in dataframe.columns.tolist():
                if col == metric_column:
                    agg_dict[col] = func
                else:
                    agg_dict[col] = lambda x: x.iloc[0]

            # move node from index to column and group by node.
            dataframe.reset_index(level="node", inplace=True)
            grouped_df = dataframe.groupby("node")

            # if verbose, calculate statistics for the
            # frequency histogram, percentiles, and the top
            # five ranks that has the highest metric value.
            if verbose:
                statistics_dict = {}
                # for each group
                for node, item in grouped_df:
                    freqs = []
                    percentiles = []

                    group = grouped_df.get_group(node)
                    group.reset_index(inplace=True)
                    # sort by metric value. get rank and metric value
                    sorted_rank_metric = group[["rank", metric_column]].sort_values(
                        by=metric_column, ascending=False
                    )
                    # store sorted ranks and metrics
                    sorted_ranks = sorted_rank_metric["rank"].to_numpy()
                    sorted_metric = sorted_rank_metric[metric_column].to_numpy()
                    num_ranks = len(sorted_ranks)

                    # we have fixed number of bins = 10.
                    # Example: max=100, min=0, size=(100-0)/10=10
                    bins = 10
                    max = sorted_metric[0]
                    min = sorted_metric[-1]
                    size = (max - min) / bins
                    if size != 0:
                        for i in range(bins):
                            bin_start = min + i * size
                            bin_end = min + (i + 1) * size
                            # sometimes bin_end != end because of
                            # rounding. For example:
                            # bin_end=52.93999, max = 53.94.
                            if i == bins - 1:
                                bin_end = max
                            if i == 0:
                                bin_start = min

                            # count the number of ranks in a bin
                            count = len(
                                sorted_rank_metric[
                                    (sorted_rank_metric[metric_column] > bin_start)
                                    & (sorted_rank_metric[metric_column] <= bin_end)
                                ]["rank"].unique()
                            )
                            freqs.append(count)

                        # the first rank's value can be equal to min so
                        # we count them as well.
                        freqs[0] += len(
                            sorted_rank_metric[
                                (sorted_rank_metric[metric_column] == min)
                            ]["rank"].unique()
                        )
                    else:
                        # Example: if min=max=0 and num_ranks=2, freqs=[2, 2]
                        freqs = [num_ranks] * bins

                    # calculate percentiles.
                    for i in [0, 25, 50, 75, 100]:
                        percentiles.append(np.percentile(sorted_metric, i))

                    # find the top five ranks that have the
                    # highest metric value.
                    if len(sorted_ranks) > 5:
                        sorted_ranks = sorted_ranks[:5]

                    # create statistics_dict.
                    # add metric_column -> imbalance.ranks, time.hist, time.percentiles
                    statistics_dict[node] = {
                        "node": node,
                        "{}.ranks".format(metric_column): sorted_ranks,
                        "{}.hist".format(metric_column): freqs,
                        "{}.percentiles".format(metric_column): percentiles,
                    }

                # create statistics dataframe from the dict.
                statistics_df = pd.DataFrame.from_dict(statistics_dict.values())
                statistics_df.set_index("node", inplace=True)

            # aggregate grouped dataframe
            agg_df = grouped_df.agg(agg_dict)

            # pandas creates multiindex columns when we do .agg() using
            # multiple functions (np.mean and np.max).
            # We first flatten the columns to remove multiindex.
            # Example after to_flat_index():
            # [('time', 'mean'), ('time', 'max'), ('name', '<lambda>')]
            # Then remove rename metric_column by adding mean and max.
            # Remove <lambda> from others.
            agg_df.columns = agg_df.columns.to_flat_index()
            columns = agg_df.columns.values

            for idx in range(len(columns)):
                if columns[idx][0] == metric_column and columns[idx][1] == "mean":
                    columns[idx] = metric_column + ".mean"
                elif columns[idx][0] == metric_column and columns[idx][1] == "max":
                    columns[idx] = metric_column + ".max"
                else:
                    columns[idx] = columns[idx][0]

            # if verbose, join aggregate dataframe with
            # statistics dataframe.
            if verbose:
                agg_df = agg_df.join(statistics_df, how="outer")

            return agg_df

        # Create a copy of the GraphFrame.
        graphframe2 = graphframe.deepcopy()

        # Use default_metric if not given.
        if metric_column is None:
            metric_column = graphframe.default_metric

        assert (
            metric_column in graphframe2.dataframe.columns
        ), "{} column does not exist in the dataframe.".format(metric_column)

        if threshold is not None:
            # Get the max value of the given metric.
            max_val = graphframe2.dataframe.sort_values(by=metric_column).iloc[-1][
                metric_column
            ]
            # Calculate the threshold.
            thres_val = max_val * threshold

        # Similar to drop_index_levels() but it calculates
        # statistics if verbose == True.
        graphframe2.dataframe = _calculate_statistics(
            graphframe2.dataframe, metric_column, ["mean", "max"]
        )

        graphframe2.inc_metrics = []
        graphframe2.exc_metrics = []

        # Add new columns to .inc_metrics or .exc_metrics.
        if metric_column in graphframe2.inc_metrics:
            _update_metric_lists(graphframe2.inc_metrics, metric_column)
        elif metric_column in graphframe2.exc_metrics:
            _update_metric_lists(graphframe2.exc_metrics, metric_column)

        # filter out the nodes if their max metric value across
        # processes/threads is less than threshold% of the max value
        # of the given metric.
        if threshold is not None:
            graphframe2 = graphframe2.filter(
                lambda x: x[metric_column + ".max"] > thres_val
            )

        # Calculate load imbalance for the given metric
        # by calculating max-to-mean ratio.
        graphframe2.dataframe[metric_column + ".imbalance"] = graphframe2.dataframe[
            metric_column + ".max"
        ].div(graphframe2.dataframe[metric_column + ".mean"])

        # <metric_column>.max is already stored in <metric_column>.percentiles
        # column if verbose = True. We don't drop it if verbose = False.
        if verbose:
            graphframe2.dataframe.drop(metric_column + ".max", axis=1, inplace=True)

        # default metric will be imbalance when user print the tree
        graphframe2.default_metric = metric_column + ".imbalance"
        # sort by mean value
        graphframe2.dataframe = graphframe2.dataframe.sort_values(
            by=[metric_column + ".mean"], ascending=False
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
        groupby_function=None,
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

            # group by name if the user gives a function such as np.mean
            if groupby_function is not None:
                gf_copy.dataframe = gf_copy.dataframe.groupby(
                    "name", as_index=False
                ).agg(groupby_function)

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

    @staticmethod
    def speedup_efficiency(
        graphframes=[],
        weak=False,
        strong=False,
        efficiency=False,
        speedup=False,
        pivot_index="num_processes",
        metrics=["time"],
        threshold=None,
    ):
        """
        Calculates the speedup and efficiency values.
        Inputs:
         - graphframes: A list of graphframes.
         - weak: True for weak scaling experiments.
         - strong: True for strong scaling experiments.
         - efficiency: True if the user wants to calculate efficiency.
         - strong: True if the user wants to calculate speedup.
         - pivot_index: The metric in each graphframe's metadata used to do calculations.
         Default: num_processes.
         - metric: The numerical metric for which we want to calculate speedup and efficiency.
         Default: time
         - threshold: The threshold for filtering metric rows of the graphframes.
        Output:
         - a new dataframe that stores speedup and efficiency values.
        """
        from .graphframe import GraphFrame

        assert (
            strong is True or weak is True
        ), "at least one of the 'strong' and 'weak' parameters should be True."
        assert (
            efficiency is True or speedup is True
        ), "at least one of the 'efficiency' and 'speedup' parameters should be True."
        assert (
            weak is False or speedup is False
        ), "speed up can be calculated only for strong scaling."

        process_to_gf = []
        for gf in graphframes:
            assert (
                "num_processes" in gf.metadata.keys()
            ), "pivot_index missing from GraphFrame metadata: use update_metadata() to specify."
            process_to_gf.append((gf.metadata[pivot_index], gf))

        GraphFrame.unify_multiple_graphframes(graphframes)

        sorted(process_to_gf, key=lambda x: x[0])
        base_numpes = process_to_gf[0][0]
        base_graphframe = process_to_gf[0][1]

        result_df = pd.DataFrame()
        # add base values to the resulting dataframe.
        for column in base_graphframe.dataframe.columns:
            if column not in base_graphframe.inc_metrics + base_graphframe.exc_metrics:
                result_df[column] = base_graphframe.dataframe[column]

        # calculate speedup and efficiency.
        for other in process_to_gf[1:]:
            for metric in metrics:
                if weak:
                    new_column_name = "{}.{}.{}".format(other[0], metric, "efficiency")
                    # weak scaling efficiency: base / other
                    result_df[new_column_name] = (
                        base_graphframe.dataframe[metric] / other[1].dataframe[metric]
                    )
                else:
                    if speedup:
                        new_column_name = "{}.{}.{}".format(other[0], metric, "speedup")
                        # strong scaling speedup: base / other
                        result_df[new_column_name] = (
                            base_graphframe.dataframe[metric]
                            / other[1].dataframe[metric]
                        )
                    if efficiency:
                        new_column_name = "{}.{}.{}".format(
                            other[0], metric, "efficiency"
                        )
                        # strong scaling efficiency: base * num_procs_base / other
                        result_df[new_column_name] = (
                            base_graphframe.dataframe[metric] * base_numpes
                        ) / (other[1].dataframe[metric] * other[0])
        return result_df

    def correlation_analysis(self, graphframe, metrics=None, method="spearman"):
        """
        Calculates correlation between metrics of a given graphframe.
        Returns the correlation matrix.
        Pandas provides three different methods: pearson, spearman, kendall
        """
        if not isinstance(metrics, list):
            metrics = [metrics]

        assert len(metrics) > 1, "This function requires at least two metrics."

        for metric in metrics:
            assert (
                metric in graphframe.dataframe.columns
            ), "{} column not present in graphframe".format(metric)

        dataframe = graphframe.dataframe[metrics]
        corr_matrix = dataframe.corr(method=method)
        return corr_matrix
