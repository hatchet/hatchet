# Copyright 2017-2020 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import warnings

from .pandas_writer import PandasWriter


class PickleWriter(PandasWriter):
    def __init__(self, filename):
        # TODO Remove Arguments when Python 2.7 support is dropped
        super(HDF5Writer, self).__init__(filename)

    def _write_to_file_type(self, df, **kwargs):
        df.to_pickle(self.fname, **kwargs)
