#!/usr/bin/env python
#
# Copyright 2017-2019 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from __future__ import print_function

import pandas as pd

import hatchet as ht

pd.set_option("display.width", 500)
pd.set_option("display.max_colwidth", 30)


if __name__ == "__main__":
    dirname = "hatchet/tests/data/hpctoolkit-cpi-database"

    gf = ht.GraphFrame.from_hpctoolkit(dirname)

    print(gf.dataframe.xs(0, level="rank"))
    print("\n")

    print(gf.tree())
