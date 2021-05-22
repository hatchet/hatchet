# Copyright 2017-2020 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from .pandas_writer import PandasWriter


class CSVWriter(PandasWriter):
    def __init__(self, filename):
        # TODO Remove Arguments when Python 2.7 support is dropped
        super(CSVWriter, self).__init__(filename)

    def _write_to_file_type(self, df, **kwargs):
        df.to_csv(self.fname, **kwargs)