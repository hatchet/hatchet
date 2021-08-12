# Copyright 2017-2021 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import pandas as pd

import sys

from .dataframe_writer import DataframeWriter

def jsonify_series_nodes(pd_series):
    jsonified_list = []
    for node in pd_series:
        jsonified_node = {
            "depth": node._depth,
            "hatchet_nid": node._hatchet_nid,
            "frame": self.frame.attrs,
        }
        jsonified_list.append(jsonified_node)
    return pd.Series(jsonified_list)

class JsonWriter(DataframeWriter):
    def __init__(self, filename):
        if sys.version_info[0] == 2:
            super(JsonWriter, self).__init__(filename)
        else:
            super().__init__(filename)

    def _write_dataframe_to_file(self, df, **kwargs):
        df.reset_index(inplace=True)
        df["node"] = jsonify_series_nodes(df["node"])
        df.to_json(self.filename, **kwargs)
