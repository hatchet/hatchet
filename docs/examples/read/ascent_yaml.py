#!/usr/bin/env python
#
# Copyright 2017-2020 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from __future__ import print_function

import pandas as pd
import numpy as np

import hatchet as ht

pd.set_option("display.width", 1500)
pd.set_option("display.max_colwidth", 20)
pd.set_option("display.max_rows", None)


if __name__ == "__main__":
    ascent_yaml = "hatchet/tests/data/ascent-cloverleaf-ex/yaml"

    gf = ht.GraphFrame.from_ascent(ascent_yaml)
    # print(gf.dataframe)

    # get valid cycles
    # print(gf.dataframe["cycle"].unique())

    # gf2 = gf.copy()
    #
    # Compute average metric (across all ranks) associated with each node
    # gf.drop_index_levels(function=np.mean)
    #
    # Compute max metric (across all ranks) associated with each node
    # gf2.drop_index_levels(function=np.max)
    #
    # Compute imbalance by dividing the max time by the mean time
    # in gf2 and gf, respectively. This creates a new column called
    # ``imbalance`` in the original dataframe.
    # gf.dataframe['imbalance'] = gf2.dataframe['time'].div(gf.dataframe['time'])
    # print(gf.tree(metric_column="imbalance"))

    # grab rows with cycle=40 in index
    # cyc_40 = gf.filter(lambda x: x["cycle"] == 40)
    # print(cyc_40.tree())

    # grab rows with cycle=110 in index
    # cyc_110 = gf.filter(lambda x: x["cycle"] == 110)
    # print(cyc_110.tree())

    # cyc_40.dataframe["cyc110_sub_cyc40"] = cyc_110.dataframe["time"] - cyc_40.dataframe["time"]
    # print(cyc_40.tree(metric_column="cyc110_sub_cyc40"))

    # max time of each filter across ranks and cycles
    gf.drop_index_levels(function=np.max)
