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


class CSVWriter(PandasWriter):
    def __init__(self, filename):
        # TODO Remove Arguments when Python 2.7 support is dropped
        super(CSVWriter, self).__init__(filename)

    def _write_to_file_type(self, df, **kwargs):
        df.reset_index(inplace=True)
        df["node"] = pickle_series_elems(df["node"])
        df["children"] = df["children"].apply(str, convert_dtype=True)
        df["parents"] = df["parents"].apply(str, convert_dtype=True)
        df.to_csv(self.fname, **kwargs)
