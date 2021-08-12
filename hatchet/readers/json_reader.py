# Copyright 2017-2021 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import pandas as pd

import sys

from ..frame import Frame
from ..node import Node
from .dataframe_reader import DataframeReader


def unjsonify_series_nodes(pd_series):
    unjsonified_list = []
    for json_node in pd_series:
        frame = Frame(attrs=json_node["frame"])
        node = Node(frame, hnid=json_node["hatchet_nid"], depth=json_node["depth"])
        unjsonified_list.append(node)
    return pd.Series(unjsonified_list)


class JsonReader(DataframeReader):
    def __init__(self, filename):
        if sys.version_info[0] == 2:
            super(JsonReader, self).__init__(filename)
        else:
            super().__init__(filename)

    def _read_dataframe_from_file(self, **kwargs):
        json_df = pd.read_json(self.filename, **kwargs)
        json_df["node"] = unjsonify_series_nodes(json_df["node"])
        multindex_cols = ["node", "rank", "thread"]
        while len(multindex_cols) > 0:
            if set(multindex_cols).issubset(json_df.columns):
                return json_df.reset_index(drop=True).set_index(multindex_cols)
            multindex_cols.pop()
        # TODO Replace with a custom error
        raise RuntimeError("Could not generate a valid Index or MultiIndex")
