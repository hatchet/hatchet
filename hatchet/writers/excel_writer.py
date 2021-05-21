# Copyright 2017-2020 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from .pandas_writer import PandasWriter

import pandas as pd
import pickle


def pickle_series_elems(pd_series):
    pickled_elems = [pickle.dumps(e) for e in pd_series]
    return pd.Series(pickled_elems)


class ExcelWriter(PandasWriter):
    def __init__(self, filename):
        # TODO Remove Arguments when Python 2.7 support is dropped
        super(ExcelWriter, self).__init__(filename)

    def _write_to_file_type(self, df, **kwargs):
        df.reset_index(inplace=True)
        df["node"] = pickle_series_elems(df["node"])
        df.to_excel(self.fname, **kwargs)
