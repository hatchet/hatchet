#!/usr/bin/env python

from __future__ import print_function

import numpy as np

import hatchet as ht


if __name__ == "__main__":
    ascent_yaml = "hatchet/tests/data/ascent-cloverleaf-ex/yaml"
    gf = ht.GraphFrame.from_ascent(ascent_yaml)

    print(gf.dataframe)
    print(gf.tree(metric_column="time"))

    gf2 = gf.copy()
    gf3 = gf.copy()
    gf4 = gf.copy()

    # Compute average metric (across all ranks) associated with each node
    gf2.drop_index_levels(function=np.mean)

    # Compute max metric (across all ranks) associated with each node
    gf3.drop_index_levels(function=np.max)

    # Compute imbalance by dividing the max time by the mean time
    # in gf2 and gf, respectively. This creates a new column called
    # ``imbalance`` in the original dataframe.
    gf2.dataframe["imbalance"] = gf3.dataframe["time"].div(gf2.dataframe["time"])

    print(gf2.tree(metric_column="imbalance"))

    # max time of each filter across ranks and cycles
    gf4.drop_index_levels(function=np.max)

    # grab rows with cycle=40 in index
    cyc_40 = gf.filter(lambda x: x["cycle"] == 40)
    print(cyc_40.tree(metric_column="time"))

    # grab rows with cycle=110 in index
    cyc_110 = gf.filter(lambda x: x["cycle"] == 110)
    print(cyc_110.tree(metric_column="time"))

    # compare performance across cycles
    cyc_40.dataframe["cyc110_sub_cyc40"] = (
        cyc_110.dataframe["time"] - cyc_40.dataframe["time"]
    )
    print(cyc_40.tree(metric_column="cyc110_sub_cyc40"))
