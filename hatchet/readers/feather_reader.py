# Copyright 2017-2020 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import pandas as pd
from .pandas_reader import PandasReader


class FeatherReader(PandasReader):
    def __init__(self, filename):
        # TODO Remove Arguments when Python 2.7 support is dropped
        super(HDF5Reader, self).__init__(filename)

    def _read_from_file_type(self, **kwargs):
        return pd.read_feather(self.fname, **kwargs)
