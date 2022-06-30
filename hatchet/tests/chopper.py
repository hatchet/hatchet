# Copyright 2021-2022 University of Maryland and other Hatchet Project
# Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import numpy as np
from hatchet.graphframe import GraphFrame
from hatchet.chopper import Chopper


def test_flat_profile(calc_pi_hpct_db):
    """Validate that the flat profile works correctly."""
    graphframe = GraphFrame.from_hpctoolkit(str(calc_pi_hpct_db))
    original_rows = graphframe.dataframe["name"].unique()
    flat_profile = graphframe.flat_profile()

    # Check if the node names are exactly the same
    assert sorted(flat_profile.index.tolist()) == sorted(original_rows)

    # Check if the aggregated time is correct for the root node.
    root = graphframe.graph.roots[0]
    assert flat_profile.loc[root.frame["name"]]["time (inc)"] == np.mean(
        graphframe.dataframe.loc[root]["time (inc)"].to_numpy()
    )

    # Check if the aggregated time is correct for the '__GI_sched_yield' node.
    another = graphframe.dataframe[
        graphframe.dataframe["name"] == "__GI_sched_yield"
    ].index[0][0]
    assert flat_profile.loc[another.frame["name"]]["time (inc)"] == np.mean(
        graphframe.dataframe.loc[another]["time (inc)"].to_numpy()
    )


def test_calculate_load_imbalance(calc_pi_hpct_db):
    """Validate that the load imbalance is calculated correctly."""

    graphframe = GraphFrame.from_hpctoolkit(str(calc_pi_hpct_db))
    load_imb_gf = graphframe.load_imbalance(metric_columns=["time (inc)"])

    # Check if load imbalance is correct for the root node.
    root = graphframe.graph.roots[0]
    root_original_metrics = graphframe.dataframe.loc[root]["time (inc)"].to_numpy()
    root_imbalance = load_imb_gf.dataframe.loc[root]["time (inc).imbalance"]
    assert (
        np.max(root_original_metrics) / np.mean(root_original_metrics) == root_imbalance
    )

    # Check if load imbalance is correct for the main node.
    main = root.children[0]
    main_original_metrics = graphframe.dataframe.loc[main]["time (inc)"].to_numpy()
    main_imbalance = load_imb_gf.dataframe.loc[main]["time (inc).imbalance"]
    assert (
        np.max(main_original_metrics) / np.mean(main_original_metrics) == main_imbalance
    )

    # Check if load imbalance is correct for the the node '__GI_sched_yield'.
    another = graphframe.dataframe[
        graphframe.dataframe["name"] == "__GI_sched_yield"
    ].index[0][0]
    another_original_metrics = graphframe.dataframe.loc[another][
        "time (inc)"
    ].to_numpy()
    another_imbalance = load_imb_gf.dataframe.loc[another]["time (inc).imbalance"]
    assert (
        np.max(another_original_metrics) / np.mean(another_original_metrics)
        == another_imbalance
    )


def test_hot_path(calc_pi_hpct_db):
    """Validate the hot path with known data from HPCToolkit."""
    graphframe = GraphFrame.from_hpctoolkit(str(calc_pi_hpct_db))

    # Correctness of this list is validated
    # via HPCViewer.
    hpctoolkit_hot_path = [
        "<program root>",
        "main",
        "62:MPI_Finalize",
        "PMPI_Finalize",
        "294:MPID_Finalize",
        "162:MPIDI_CH3_Finalize",
        "230:psm_dofinalize",
        "36:<unknown procedure>",
        "<unknown procedure>",
        "<unknown procedure>",
    ]

    hot_path = graphframe.hot_path(metric="time (inc)")

    for node in hot_path:
        assert node.frame["name"] in hpctoolkit_hot_path

    # test if parameters override.
    # should return the root if threshold equals 2
    hot_path = graphframe.hot_path(metric="time (inc)", threshold=2)
    assert len(hot_path) == 1
    assert hot_path[0].frame["name"] == "<program root>"


def test_analyze_scaling(small_mock1):
    """Validate that the analyze scaling works correctly."""
    gf1 = GraphFrame.from_literal(small_mock1)
    gf2 = GraphFrame.from_literal(small_mock1)

    # halve the time of the original data to produce a dummy profile of the same
    # program with a different number of processing elements
    gf2.dataframe["time"] = gf2.dataframe["time"].apply(lambda x: x / 2)

    gf_test = gf1.div(gf2)

    # use analyze_scaling function with all bool args set to True
    pes = [(gf1, 1), (gf2, 2)]
    metric = ["time"]
    gf_result = Chopper.analyze_scaling(pes, metric, 1, 1, 1, 1)

    # add all analysis information as new columns to the original and test dataframes
    gfs = [gf1, gf2, gf_test]
    for gf in gfs:
        gf.dataframe["time-spdup(1x2)"] = gf2.dataframe[metric] - gf1.dataframe[metric]
        gf.dataframe["time-efc(1x2)"] = gf_test.dataframe[metric] / 2
        gf.dataframe["time-wk_scl(1x2)"] = gf1.dataframe[metric] / gf2.dataframe[metric]

    # check if the new dataframe returned by analyze_scaling matches the test dataframe
    assert gf_test.dataframe.equals(gf_result.dataframe)

    # check if the analysis columns of the original two dataframes match each other
    assert gf1.dataframe.iloc[:, -3:].equals(gf2.dataframe.iloc[:, -3:])
