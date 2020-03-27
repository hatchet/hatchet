# Copyright 2017-2020 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import numpy as np
import os.path

from hatchet import GraphFrame


def test_graphframe_literal(literal_hatchet_snapshot):
    """Sanity test a GraphFrame object with known literal data."""
    gf = GraphFrame.from_hatchet_snapshot(str(literal_hatchet_snapshot))

    assert len(gf.graph) == 24
    for col in gf.dataframe.columns:
        if col in ("name"):
            assert gf.dataframe[col].dtype == np.object
        elif col in ("time", "time (inc)"):
            assert gf.dataframe[col].dtype == np.float64


def test_graphframe_hpct(hpct_hatchet_snapshot):
    """Sanity test a GraphFrame object with known HPCToolkit data."""
    gf = GraphFrame.from_hatchet_snapshot(str(hpct_hatchet_snapshot))

    assert len(gf.graph) == 34
    for col in gf.dataframe.columns:
        if col in ("time", "time (inc"):
            assert gf.dataframe[col].dtype == np.float64
        elif col in ("nid", "line"):
            assert gf.dataframe[col].dtype == np.int64
        elif col in ("file", "module", "name", "type"):
            assert gf.dataframe[col].dtype == np.object


def test_graphframe_caliper(caliper_hatchet_snapshot):
    """Sanity test a GraphFrame object with known Caliper data."""
    gf = GraphFrame.from_hatchet_snapshot(str(caliper_hatchet_snapshot))

    assert len(gf.graph) == 24
    for col in gf.dataframe.columns:
        if col in ("time", "time (inc"):
            assert gf.dataframe[col].dtype == np.float64
        elif col in ("nid"):
            assert gf.dataframe[col].dtype == np.int64
        elif col in ("name"):
            assert gf.dataframe[col].dtype == np.object


def test_graphframe_save_load_literal(mock_graph_literal):
    """Test save and load operations with known literal data."""
    gf1 = GraphFrame.from_literal(mock_graph_literal)
    gf1.save(fname="hatchet-literal-snapshot")
    assert os.path.isfile("hatchet-literal-snapshot.json")

    gf2 = GraphFrame.from_hatchet_snapshot("hatchet-literal-snapshot.json")

    assert all(gf1.dataframe.columns == gf2.dataframe.columns)
    assert gf1.dataframe.shape == gf2.dataframe.shape

    gf1.dataframe.sort_index(inplace=True)
    gf2.dataframe.sort_index(inplace=True)
    assert all(gf1.dataframe.index == gf2.dataframe.index)

    assert len(gf1.graph) == len(gf2.graph)


def test_graphframe_save_load_hpct(calc_pi_hpct_db):
    """Test save and load operations with known HPCToolkit data."""
    gf1 = GraphFrame.from_hpctoolkit(str(calc_pi_hpct_db))
    gf1.save(fname="hatchet-hpct-snapshot")
    assert os.path.isfile("hatchet-hpct-snapshot.json")

    gf2 = GraphFrame.from_hatchet_snapshot("hatchet-hpct-snapshot.json")

    assert all(gf1.dataframe.columns == gf2.dataframe.columns)
    assert gf1.dataframe.shape == gf2.dataframe.shape

    gf1.dataframe.sort_index(inplace=True)
    gf2.dataframe.sort_index(inplace=True)
    assert all(gf1.dataframe.index == gf2.dataframe.index)

    assert len(gf1.graph) == len(gf2.graph)


def test_graphframe_save_load_caliper(lulesh_caliper_json):
    """Test save and load operations with known Caliper data."""
    gf1 = GraphFrame.from_caliper_json(str(lulesh_caliper_json))
    gf1.save(fname="hatchet-caliper-snapshot")
    assert os.path.isfile("hatchet-caliper-snapshot.json")

    gf2 = GraphFrame.from_hatchet_snapshot("hatchet-caliper-snapshot.json")

    assert all(gf1.dataframe.columns == gf2.dataframe.columns)
    assert gf1.dataframe.shape == gf2.dataframe.shape

    gf1.dataframe.sort_index(inplace=True)
    gf2.dataframe.sort_index(inplace=True)
    assert all(gf1.dataframe.index == gf2.dataframe.index)

    assert len(gf1.graph) == len(gf2.graph)


def test_sub_save_load(small_mock1, small_mock2):
    """Test save and load operations with subtracted data."""
    gf1 = GraphFrame.from_literal(small_mock1)
    gf2 = GraphFrame.from_literal(small_mock2)

    assert len(gf1.graph) == 6
    assert len(gf2.graph) == 7

    gf3 = gf1 - gf2
    assert len(gf3.graph) == 8

    gf3.save("hatchet-snapshot")
    assert os.path.isfile("hatchet-snapshot.json")

    gf4 = GraphFrame.from_hatchet_snapshot("hatchet-snapshot.json")

    assert all(gf3.dataframe.columns == gf4.dataframe.columns)
    assert gf3.dataframe.shape == gf4.dataframe.shape

    gf3.dataframe.sort_index(inplace=True)
    gf4.dataframe.sort_index(inplace=True)
    assert all(gf3.dataframe.index == gf4.dataframe.index)

    assert len(gf3.graph) == len(gf4.graph)
