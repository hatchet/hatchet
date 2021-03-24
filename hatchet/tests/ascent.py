# Copyright 2017-2019 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import numpy as np

from hatchet import GraphFrame


def test_graphframe_yaml(ascent_yaml):
    """Sanity test a GraphFrame object with known data."""
    gf = GraphFrame.from_ascent(str(ascent_yaml))

    assert len(gf.graph) == 1260

    assert len(gf.dataframe.groupby("name").groups) == 54
    assert len(gf.dataframe.groupby("input_cells").groups) == 63
    assert len(gf.dataframe.groupby("cycle").groups) == 20

    for col in gf.dataframe.columns:
        if col in (
            "time",
            "input_cells",
            "input_domains",
            "output_cells",
            "output_domains",
            "mean",
            "variance",
            "skewness",
            "kurtosis",
            "bins",
            "field_min",
            "field_max",
            "entropy",
            "sim_time",
            "cycle_count",
        ):
            assert gf.dataframe[col].dtype == np.float64
        elif col in ("nid", "cycle"):
            assert gf.dataframe[col].dtype == np.int64
        elif col in ("path", "device", "in_topology", "output_topology", "name"):
            assert gf.dataframe[col].dtype == np.object

    # TODO: add tests to confirm values in dataframe


def test_graphframe_json(ascent_json):
    """Sanity test a GraphFrame object with known data."""
    gf = GraphFrame.from_ascent(str(ascent_json))

    assert len(gf.graph) == 1260

    assert len(gf.dataframe.groupby("name").groups) == 54
    assert len(gf.dataframe.groupby("input_cells").groups) == 63
    assert len(gf.dataframe.groupby("cycle").groups) == 20

    for col in gf.dataframe.columns:
        if col in (
            "time",
            "input_cells",
            "input_domains",
            "output_cells",
            "output_domains",
            "mean",
            "variance",
            "skewness",
            "kurtosis",
            "bins",
            "field_min",
            "field_max",
            "entropy",
            "sim_time",
            "cycle_count",
        ):
            assert gf.dataframe[col].dtype == np.float64
        elif col in ("nid", "cycle"):
            assert gf.dataframe[col].dtype == np.int64
        elif col in ("path", "device", "in_topology", "output_topology", "name"):
            assert gf.dataframe[col].dtype == np.object

    # TODO: add tests to confirm values in dataframe
