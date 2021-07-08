# Copyright 2017-2021 Lawrence Livermore National Security, LLC and other
# CallFlow Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT
# ------------------------------------------------------------------------------

import numpy as np
import hatchet as ht
from scipy.stats import kurtosis, skew

class BoxPlot:
    """
    Boxplot computation for a dataframe segment
    """

    def __init__(self, tgt_gf, bkg_gf=None, callsite=[], iqr_scale=1.5):
        """
        Boxplot for callsite or module
        
        :param tgt_gf: (ht.GraphFrame) Target GraphFrame 
        :param bkg_gf: (ht.GraphFrame) Relative supergraph
        :param callsite: (str) Callsite name
        :param iqr_scale: (float) IQR range for outliers.
        """
        assert isinstance(tgt_gf, ht.GraphFrame)
        assert isinstance(callsite, list)
        assert isinstance(iqr_scale, float)

        assert 0

        self.box_types = ["tgt"]        
        if relative_gf is not None:
            self.box_types = ["tgt", "bkg"]

        self.nid = gf.get_idx(name, ntype)
        node = {"id": self.nid, "type": ntype, "name": name}

        # TODO: Avoid this.
        self.c_path = None
        self.rel_c_path = None

        if ntype == "callsite":
            df = sg.callsite_aux_dict[name]
            if 'component_path' in sg.dataframe.columns:
                self.c_path = sg.get_component_path(node)
                
            if relative_sg is not None:
                rel_df = relative_sg.callsite_aux_dict[name]

                if 'component_path' in relative_sg.dataframe.columns:
                    self.rel_c_path = sg.get_component_path(node)
            
        elif ntype == "module":
            df = sg.module_aux_dict[self.nid]
            if relative_sg is not None:
                rel_df = relative_sg.module_aux_dict[self.nid]
        
        if relative_sg is not None and "dataset" in rel_df.columns:
            self.ndataset = df_count(rel_df, 'dataset')

        self.time_columns = [proxy_columns.get(_, _) for _ in TIME_COLUMNS]
        self.result = {}
        self.ntype = ntype
        self.iqr_scale = iqr_scale

        self.result["name"] = name
        if ntype == "callsite":
            self.result["module"] = sg.get_module(sg.get_idx(name, ntype))

        if relative_sg is not None:
            self.result["bkg"] = self.compute(rel_df)
        self.result["tgt"] = self.compute(df)
        
    def compute(self, df):
        """
        Compute boxplot related information.

        :param df: Dataframe to calculate the boxplot information.
        :return:
        """

        ret = {_: {} for _ in TIME_COLUMNS}
        for tk, tv in zip(TIME_COLUMNS, self.time_columns):
            q = np.percentile(df[tv], [0.0, 25.0, 50.0, 75.0, 100.0])
            mask = outliers(df[tv], scale=self.iqr_scale)
            mask = np.where(mask)[0]

            if 'rank' in df.columns:
                rank = df['rank'].to_numpy()[mask]
            else:
                rank = np.zeros(mask.shape[0], dtype=int)

            _data = df[tv].to_numpy()
            _min, _mean, _max = _data.min(), _data.mean(), _data.max()
            _var = _data.var() if _data.shape[0] > 0 else 0.0
            _imb = (_max - _mean) / _mean if not np.isclose(_mean, 0.0) else _max
            _skew = skew(_data)
            _kurt = kurtosis(_data)

            ret[tk] = {
                "q": q,
                "oval": df[tv].to_numpy()[mask],
                "orank": rank,
                "d": _data,
                "rng": (_min, _max),
                "uv": (_mean, _var),
                "imb": _imb,
                "ks": (_kurt, _skew),
                "nid": self.nid,
            }
            if 'dataset' in df.columns:
                ret[tk]['odset'] = df['dataset'].to_numpy()[mask]

            # TODO: Find a better way to send the component_path from data.
            if self.c_path is not None:
                ret[tk]['cpath'] = self.c_path
            
            if self.rel_c_path is not None:
                ret[tk]['rel_cpath'] = self.rel_c_path

        return ret
            
    def unpack(self):
        """
        Unpack the boxplot data into JSON format.
        """
        result = {}
        for box_type in self.box_types:
            result[box_type] = {}
            for metric in self.time_columns:
                box = self.result[box_type][metric]
                result[box_type][metric] = {
                    "q": box["q"].tolist(),
                    "outliers": {
                        "values": box["oval"].tolist(),
                        "ranks": box["orank"].tolist()
                    },
                    "min": box["rng"][0],
                    "max": box["rng"][1],
                    "mean": box["uv"][0],
                    "var": box["uv"][1],
                    "imb": box["imb"],
                    "kurt": box["ks"][0],
                    "skew": box["ks"][1],
                    "nid": box["nid"],
                    "name": self.result["name"],
                }
                result["name"] = self.result["name"]
                
                if 'odset' in box:
                    result[box_type][metric]['odset'] = box['odset'].tolist()

                if 'cpath' in box:
                    result[box_type][metric]['cpath'] = box['cpath']

                if 'rel_cpath' in box:
                    result[box_type][metric]['rel_cpath'] = box['rel_cpath']

        return result

# ------------------------------------------------------------------------------
