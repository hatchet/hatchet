#!/usr/bin/env python
#
# Copyright 2017-2019 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from __future__ import print_function

import pandas as pd

import hatchet as ht

pd.set_option("display.width", 1500)
pd.set_option("display.max_colwidth", 20)
pd.set_option("display.max_rows", None)


if __name__ == "__main__":
    filename = (
        "hatchet/tests/data/caliper-lulesh-json/lulesh-sample-annotation-profile.json"
    )

    gf = ht.GraphFrame.from_caliper_json(filename)

    print(gf.dataframe)
    print("\n")

    print(gf.graph.to_string(gf.graph.roots, gf.dataframe))
    with open("test.dot", "w") as fileh:
        fileh.write(gf.graph.to_dot(gf.graph.roots, gf.dataframe))
