import hatchet as ht
import numpy as np
import pandas as pd
from scipy import stats


class BoxPlot:
    """
    Boxplot computation for a dataframe segment
    """

    def __init__(
        self,
        tgt_gf,
        bkg_gf=None,
        callsites=[],
        metrics=["time", "time (inc)"],
        iqr_scale=1.5,
    ):
        """
        Boxplot for callsite

        :param tgt_gf: (ht.GraphFrame) Target GraphFrame
        :param bkg_gf: (ht.GraphFrame) Relative supergraph
        :param callsites: (list) Callsite name
        :param metrics: (list) Runtime metrics
        :param iqr_scale: (float) IQR range for outliers.
        """
        assert isinstance(tgt_gf, ht.GraphFrame)
        assert isinstance(callsites, list)
        assert isinstance(iqr_scale, float)

        self.metrics = metrics
        self.iqr_scale = iqr_scale
        self.callsites = callsites

        tgt_gf.dataframe.reset_index(inplace=True)
        tgt_dict = BoxPlot.df_bi_level_group(
            tgt_gf.dataframe,
            "name",
            None,
            cols=metrics + ["nid"],
            group_by=["rank"],
            apply_func=lambda _: _.mean(),
        )

        if bkg_gf is not None:
            bkg_gf.dataframe.reset_index(inplace=True)
            bkg_dict = BoxPlot.df_bi_level_group(
                bkg_gf.dataframe,
                "name",
                None,
                cols=metrics + ["nid"],
                group_by=["rank"],
                apply_func=lambda _: _.mean(),
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
    def df_bi_level_group(
        df, frst_group_attr, scnd_group_attr, cols, group_by, apply_func, proxy={}
    ):
        _cols = cols + group_by

        # If there is only one attribute to group by, we use the 1st index.
        if len(group_by) == 1:
            group_by = group_by[0]

        # Find the grouping
        if scnd_group_attr is not None:
            _groups = [frst_group_attr, scnd_group_attr]
        else:
            _groups = [frst_group_attr]

        # Set the df.index as the _groups
        _df = df.set_index(_groups)
        _levels = _df.index.unique().tolist()

        # If "rank" is present in the columns, we will group by "rank".
        if "rank" in _df.columns and len(df["rank"].unique().tolist()) > 1:
            if scnd_group_attr is not None:
                if len(group_by) == 0:
                    _cols = _cols + ["rank"]
                    return {_: _df.xs(_)[_cols] for (_, __) in _levels}
                return {
                    _: (_df.xs(_)[_cols].groupby(group_by).mean()).reset_index()
                    for (_, __) in _levels
                }
            else:
                if len(group_by) == 0:
                    _cols = _cols + ["rank"]
                    return {_: _df.xs(_)[_cols] for _ in _levels}
                return {
                    _: (_df.xs(_)[_cols].groupby(group_by).mean()).reset_index()
                    for _ in _levels
                }
        else:
            return {_: _df.xs(_)[_cols] for _ in _levels}

    @staticmethod
    def outliers(data, scale=1.5, side="both"):
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
        Compute boxplot related information.

        :param df: Dataframe to calculate the boxplot information.
        :return:
        """

        ret = {_: {} for _ in self.metrics}
        for tk, tv in zip(self.metrics, self.metrics):
            q = np.percentile(df[tv], [0.0, 25.0, 50.0, 75.0, 100.0])
            mask = BoxPlot.outliers(df[tv], scale=self.iqr_scale)
            mask = np.where(mask)[0]

            if "rank" in df.columns:
                rank = df["rank"].to_numpy()[mask]
            else:
                rank = np.zeros(mask.shape[0], dtype=int)

            _data = df[tv].to_numpy()
            _min, _mean, _max = _data.min(), _data.mean(), _data.max()
            _var = _data.var() if _data.shape[0] > 0 else 0.0
            _imb = (_max - _mean) / _mean if not np.isclose(_mean, 0.0) else _max
            _skew = stats.skew(_data)
            _kurt = stats.kurtosis(_data)

            ret[tk] = {
                "q": q,
                "oval": df[tv].to_numpy()[mask],
                "orank": rank,
                "d": _data,
                "rng": (_min, _max),
                "uv": (_mean, _var),
                "imb": _imb,
                "ks": (_kurt, _skew),
            }
            if "dataset" in df.columns:
                ret[tk]["odset"] = df["dataset"].to_numpy()[mask]

        return ret

    def unpack(self):
        """
        Unpack the boxplot data into JSON format.
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
                        "outliers": {
                            "values": box["oval"].tolist(),
                            "ranks": box["orank"].tolist(),
                        },
                        "min": box["rng"][0],
                        "max": box["rng"][1],
                        "mean": box["uv"][0],
                        "var": box["uv"][1],
                        "imb": box["imb"],
                        "kurt": box["ks"][0],
                        "skew": box["ks"][1],
                    }

                    if "odset" in box:
                        result[callsite][box_type][metric]["odset"] = box[
                            "odset"
                        ].tolist()

        return result
