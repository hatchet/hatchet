import numpy as np
import pandas as pd
from scipy import stats
import hatchet as ht


class BoxPlot:
    def __init__(
        self, cat_column, tgt_gf, bkg_gf=None, callsites=[], metrics=[], iqr_scale=1.5
    ):
        """
        Boxplot computation for callsites. The data can be computed for two use
        cases:
        1. Examining runtime distributions of a single GraphFrame.
        2. Comparing runtime distributions of a target GraphFrame against a
           background GraphFrame.

        Arguments:
            cat_column: (string) Categorical column to aggregate the boxplot computation.
            tgt_gf: (ht.GraphFrame) Target GraphFrame.
            bkg_gf: (ht.GraphFrame) Background GraphFrame.
            callsite: (list) List of callsites.
            metrics: (list) List of metrics to compute.
            iqr_scale: (float) IQR range for outliers.

        Return: None
        """
        assert isinstance(tgt_gf, ht.GraphFrame)
        assert isinstance(callsites, list)
        assert isinstance(metrics, list)
        assert isinstance(iqr_scale, float)

        if bkg_gf is not None:
            assert isinstance(bkg_gf, ht.GraphFrame)
            assert cat_column in bkg_gf.dataframe.column

        tgt_gf.dataframe = tgt_gf.dataframe.reset_index()
        if cat_column not in tgt_gf.dataframe.columns:
            raise Exception(f"{cat_column} not found in tgt_gf.")

        if bkg_gf is not None:
            bkg_gf.dataframe = bkg_gf.dataframe.reset_index()
            if cat_column not in bkg_gf.dataframe.columns:
                raise Exception(f"{cat_column} not found in bkg_gf.")

        self.metrics = metrics
        self.iqr_scale = iqr_scale
        self.callsites = callsites
        self.cat_column = cat_column

        if len(metrics) == 0:
            self.metrics = tgt_gf.inc_metrics + tgt_gf.exc_metrics

        tgt_gf.dataframe.reset_index(inplace=True)
        tgt_dict = BoxPlot.df_groupby(
            tgt_gf.dataframe,
            groupby="name",
            cols=self.metrics + [self.cat_column],
        )

        if bkg_gf is not None:
            bkg_gf.dataframe.reset_index(inplace=True)
            bkg_dict = BoxPlot.df_groupby(
                bkg_gf.dataframe,
                groupby="name",
                cols=self.metrics + [self.cat_column],
            )

        self.result = {}

        self.box_types = ["tgt"]
        if bkg_gf is not None:
            self.box_types = ["tgt", "bkg"]

        for callsite in self.callsites:
            ret = {}
            tgt_df = tgt_dict[callsite]
            ret["tgt"] = self.compute(tgt_df)

            if bkg_gf is not None:
                bkg_df = bkg_dict[callsite]
                ret["bkg"] = self.compute(bkg_df)

            self.result[callsite] = ret

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
        _df = df.set_index([groupby])
        _levels = _df.index.unique().tolist()

        return {_: _df.xs(_)[cols] for _ in _levels}

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
            mask = BoxPlot.outliers(df[tv], scale=self.iqr_scale)
            mask = np.where(mask)[0]

            _data = df[tv].to_numpy()
            _min, _mean, _max = _data.min(), _data.mean(), _data.max()
            _var = _data.var() if _data.shape[0] > 0 else 0.0
            _imb = (_max - _mean) / _mean if not np.isclose(_mean, 0.0) else _max
            _skew = stats.skew(_data)
            _kurt = stats.kurtosis(_data)

            ret[tk] = {
                "q": q,
                "ometric": df[tv].to_numpy()[mask],
                "ocat": df[self.cat_column].to_numpy()[mask],
                "d": _data,
                "rng": (_min, _max),
                "uv": (_mean, _var),
                "imb": _imb,
                "ks": (_kurt, _skew),
            }

        return ret

    def unpack(self):
        """
        Unpack the boxplot data into JSON format.

        Arguments:

        Return:
            result (dict): {
                "callsite1": {
                    "metric1": {
                        "q": (array) quartiles (i.e., [q0, q1, q2, q3, q4]),
                        "ocat": (array) outlier from cat_column,
                        "ometric": (array) outlier from metri,
                        "min": (number) minimum,
                        "max": (number) maximum,
                        "mean": (number) mean,
                        "var": (number) variance,
                        "imb": (number) imbalance,
                        "kurt": (number) kurtosis,
                        "skew": (number) skewness,
                    }, ...
                }, ...
            }
        """
        result = {}
        for callsite in self.callsites:
            result[callsite] = {}
            for box_type in self.box_types:
                result[callsite][box_type] = {}
                for metric in self.metrics:
                    box = self.result[callsite][box_type][metric]
                    result[callsite][box_type][metric] = {
                        "q": box["q"].tolist(),
                        "ocat": box["ocat"].tolist(),
                        "ometric": box["ometric"].tolist(),
                        "min": box["rng"][0],
                        "max": box["rng"][1],
                        "mean": box["uv"][0],
                        "var": box["uv"][1],
                        "imb": box["imb"],
                        "kurt": box["ks"][0],
                        "skew": box["ks"][1],
                    }


        return result
