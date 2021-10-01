# Copyright 2021 University of Maryland and other Hatchet Project
# Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import numpy as np
import pandas as pd
from scipy import stats
import hatchet as ht


class BoxPlot:
    def __init__(
        self,
        multi_index_gf,
        drop_index="",
        metrics=[],
    ):
        """
        Boxplot class computes the runtime distributions of a multi-indexed GraphFrame.


        Arguments:
            multi_index_gf: (ht.GraphFrame) Target GraphFrame.
            drop_index: (string) Categorical column to aggregate the boxplot
            computation. (Optional, as long as there is only 2 indexes in the
            ht.GraphFrame)
            metrics: (list) List of metrics to compute.

        Return: None
        """
        assert isinstance(multi_index_gf, ht.GraphFrame)
        assert isinstance(drop_index, str)
        assert isinstance(metrics, list)

        df_index = list(multi_index_gf.dataframe.index.names)

        # Validate if only 2 indexes are provided. Else, warn the user to pass `drop_column`.
        if len(df_index) > 2 and not drop_index:
            raise Exception(
                "multi_index_gf contains len(self.df_index) indexes. Please specify the `drop_index` by which BoxPlot API will compute the distribution to avoid ambiguity."
            )

        # Validate primary index is 'node'.
        if "node" not in df_index:
            raise Exception(
                "BoxPlot expects 'node' to be a primary index of 'multi_index_gf'."
            )

        # Validate drop_index in the dataframe, if provided.
        if drop_index and drop_index not in df_index:
            raise Exception(
                f"'drop_index: {drop_index}' is not a valid index of 'multi_index_gf'."
            )

        # Validate metrics are columns in the dataframe, if provided.
        if len(metrics) > 0:
            for metric in metrics:
                if metric not in multi_index_gf.dataframe.columns:
                    raise Exception(f"{metric} not found in the gf.dataframe.")

        # Set drop_index as the secondary index.
        if len(df_index) == 2:
            self.drop_index = multi_index_gf.dataframe.names[1]
        else:
            self.drop_index = drop_index

        # Reset the indexes in the dataframe.
        multi_index_gf_copy = multi_index_gf.copy()
        multi_index_gf_copy.dataframe = multi_index_gf.dataframe.reset_index()

        # Set the metrics for computation.
        if len(metrics) == 0:
            self.metrics = (
                multi_index_gf_copy.inc_metrics + multi_index_gf_copy.exc_metrics
            )
        else:
            self.metrics = metrics

        # Drop the 'node' and `drop_index` from the ht.GraphFrame.DataFrame's indexes.
        df_index.remove("node")
        df_index.remove(self.drop_index)

        self.df_index = df_index
        # BoxPlot API will aggregate considering the `hatchet_nid` and the
        # `drop_index`.
        self.group_by = ["hatchet_nid"] + self.df_index

        # Hatchet columns that are required by BoxPlot API for computation.
        self.ht_columns = ["name", "node"]

        # Group the dataframe by the provided group_by columns.
        self.callsites, callsites_dict = BoxPlot.df_groupby(
            multi_index_gf_copy.dataframe,
            groupby=self.group_by,
            cols=self.metrics + self.ht_columns + [self.drop_index],
        )

        # Dump the computation result for each callsite.
        self.result = {
            callsite: self.compute(callsites_dict[callsite])
            for callsite in self.callsites
        }

        # Convert it to a GraphFrame.
        self.gf = self.to_gf(multi_index_gf_copy)

    @staticmethod
    def df_groupby(df, groupby, cols):
        """
        Group the dataframe by groupby column.

        Arguments:
            df (graphframe): self's graphframe
            groupby: groupby columns on dataframe
            cols: columns from the dataframe

        Return:
            (dict): A dictionary of dataframes (columns) keyed by groups.
        """
        _df = df.set_index(groupby)
        _levels = _df.index.unique().tolist()
        return _levels, {_: _df.xs(_)[cols] for _ in _levels}

    @staticmethod
    def outliers(data, scale=1.5, side="both"):
        """
        Calculate outliers from the data.

        Arguments:
            data (np.ndarray or pd.Series): Array of values.
            scale (float): IQR range for outliers.
            side (str): directions for calculating the outliers, i.e., left,
            right, both.

        Return:
            outliers (np.ndarray): Array of outlier values.
        """
        assert isinstance(data, (pd.Series, np.ndarray))
        assert len(data.shape) == 1
        assert isinstance(scale, float)
        assert side in ["gt", "lt", "both"]

        d_q13 = np.percentile(data, [25.0, 75.0])
        iqr_distance = np.multiply(stats.iqr(data), scale)

        if side in ["gt", "both"]:
            upper_range = d_q13[1] + iqr_distance
            upper_outlier = np.greater(data - upper_range.reshape(1), 0)

        if side in ["lt", "both"]:
            lower_range = d_q13[0] - iqr_distance
            lower_outlier = np.less(data - lower_range.reshape(1), 0)

        if side == "gt":
            return upper_outlier
        if side == "lt":
            return lower_outlier
        if side == "both":
            return np.logical_or(upper_outlier, lower_outlier)

    def compute(self, df):
        """
        Compute boxplot quartiles and statistics.

        Arguments:
            df: Dataframe to calculate the boxplot information.

        Return:
            ret (dict): {
                "metric1": {
                    "q": (array) quartiles (i.e., [q0, q1, q2, q3, q4]),
                    "ometric": (array) outlier from metric,
                    "ocat": (array) outlier from cat_column,
                    "d": (array) metric values,
                    "rng": (tuple) (min, max),
                    "uv": (tuple) (mean, variance),
                    "imb": (number) imbalance,
                    "ks": (tuple) (kurtosis, skewness)
                }
            }
        """
        ret = {_: {} for _ in self.metrics}
        for tk, tv in zip(self.metrics, self.metrics):
            q = np.percentile(df[tv], [0.0, 25.0, 50.0, 75.0, 100.0])
            mask = BoxPlot.outliers(df[tv], scale=1.5)
            mask = np.where(mask)[0]

            _data = df[tv].to_numpy()
            _min, _mean, _max = _data.min(), _data.mean(), _data.max()
            _var = _data.var() if _data.shape[0] > 0 else 0.0
            _imb = (_max - _mean) / _mean if not np.isclose(_mean, 0.0) else _max
            _skew = stats.skew(_data)
            _kurt = stats.kurtosis(_data)

            # TODO: Outliers and their corresponding rank member is not being
            # fetched accurately.
            # _outliers = df[tv].to_numpy()[mask]

            ret[tk] = {
                "q": q,
                # "ometric": _outliers,
                # "ocat": df.index[1] if len(_outliers) > 0 else -1, # not being used in the vis yet.
                "d": _data,
                "rng": (_min, _max),
                "uv": (_mean, _var),
                "imb": _imb,
                "ks": (_kurt, _skew),
            }

            for ht_column in self.ht_columns + [self.drop_index]:
                ret[tk][ht_column] = df[ht_column].iloc[0]

        return ret

    def to_json(self):
        """
        Unpack the boxplot data into JSON format.

        Arguments:

        Return:
            result (dict): {
                "callsite1": {
                    "tgt": self._unpack_callsite,
                    "bkg": self._unpack_callsite
                },
            }
        """
        return {
            callsite: self._unpack_callsite(callsite) for callsite in self.callsites
        }

    def _unpack_callsite(self, callsite):
        """
        Helper function to unpack the data by callsite.

        Arguments:
            callsite: Callsite's name
            with_htnode: (bool) An option to add hatchet.Node to the dict.

        Return:
            ret (dict): {
                "metric": {
                    "q": (array) quartiles (i.e., [q0, q1, q2, q3, q4]),
                    "ocat": (array) outlier from cat_column, (TODO)
                    "ometric": (array) outlier from metri, (TODO)
                    "min": (number) minimum,
                    "max": (number) maximum,
                    "mean": (number) mean,
                    "var": (number) variance,
                    "imb": (number) imbalance,
                    "kurt": (number) kurtosis,
                    "skew": (number) skewness,
                }
            }
        """
        ret = {}
        for metric in self.metrics:
            box = self.result[callsite][metric]
            ret[metric] = {
                "q": box["q"].tolist(),
                # "ocat": box["ocat"], # TODO
                # "ometric": box["ometric"].tolist(), # TODO
                "min": box["rng"][0],
                "max": box["rng"][1],
                "mean": box["uv"][0],
                "var": box["uv"][1],
                "imb": box["imb"],
                "kurt": box["ks"][0],
                "skew": box["ks"][1],
            }

            for ht_column in self.ht_columns + [self.drop_index]:
                ret[metric][ht_column] = box[ht_column]

        return ret

    def _to_gf_by_metric(self, gf, metric):
        """
        Wrapper function to unpack the boxplot data into Hatchet.GraphFrame by
        respective metric.

        Argument:
            gf: (hatchet.GraphFrame) GraphFrame
            metric: (string) Metric

        Return:
            hatchet.GraphFrame with boxplot information as columns.

        """
        _dtype = {
            "name": str,
            "q": object,
            # "ocat": object, # TODO
            # "ometric": object, # TODO
            "min": np.float64,
            "max": np.float64,
            "mean": np.float64,
            "var": np.float64,
            "imb": np.float64,
            "kurt": np.float64,
            "skew": np.float64,
        }
        _dict = {
            callsite: self._unpack_callsite(callsite)[metric]
            for callsite in self.callsites
        }
        tmp_df = pd.DataFrame.from_dict(data=_dict).T
        tmp_df = tmp_df.astype(_dtype)
        tmp_df.index.names = self.group_by
        tmp_df.reset_index(inplace=True)

        tmp_df = tmp_df.drop(columns=[self.drop_index])
        tmp_df.set_index(["node"] + self.df_index, inplace=True)

        # TODO: Would we need to squash the graph. (Check in the to_gf() method.)
        # Call into the gf.groupby_aggregate() (in PR) before returning the gf.
        return ht.GraphFrame(gf.graph, tmp_df, gf.exc_metrics, gf.inc_metrics)

    def to_gf(self, gf):
        """
        Unpack the boxplot data into GraphFrame object.

        Note: In this case, only the hatchet.dataframe will be updated, with
        hatchet.Graph being the same as the input gf.

        Arguments:
            gf: (hatchet.GraphFrame) GraphFrame

        Return:
            (dict) : {
                "metric": hatchet.GraphFrame, ...
            }
        """
        return {metric: self._to_gf_by_metric(gf, metric) for metric in self.metrics}
