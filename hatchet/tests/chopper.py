# Copyright 2021-2022 University of Maryland and other Hatchet Project
# Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import pandas as pd
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


def test_multirun_analysis(small_mock1):
    gf1 = GraphFrame.from_literal(small_mock1)

    gf2, gf4, gf8 = gf1.deepcopy(), gf1.deepcopy(), gf1.deepcopy()

    gf1.update_metadata(1)
    gf2.update_metadata(2)
    gf4.update_metadata(4)
    gf8.update_metadata(8)

    # assign different time values to each graphframe
    gf2.dataframe["time"] = [0, 4, 4, 8, 7, 8]
    gf4.dataframe["time"] = [0, 2, 2, 4, 5, 4]
    gf8.dataframe["time"] = [0, 1, 1, 2, 3, 2]

    # recalculate all inclusive metrics for graphframes with modified exclusive times
    gf2.calculate_inclusive_metrics()
    gf4.calculate_inclusive_metrics()
    gf8.calculate_inclusive_metrics()

    # run multirun_analyis function on the exclusive times
    df_test_exc = Chopper().multirun_analysis(
        graphframes=[gf1, gf2, gf4, gf8],
        metric="time",
        pivot_index="num_processes",
        columns="name",
        threshold=0,
    )

    # join the dataframes containing the dummy data and create a pivot table
    df_dummy_exc = pd.concat(
        [gf1.dataframe, gf2.dataframe, gf4.dataframe, gf8.dataframe]
    )
    df_dummy_exc = df_dummy_exc.pivot(
        index="num_processes", columns="name", values="time"
    )

    # drop the time data for function A because it does not satisfy the threshold of 0
    df_dummy_exc = df_dummy_exc.drop("A", axis="columns")

    # check if the test and dummy dataframes match
    assert df_test_exc.equals(df_dummy_exc)

    # run multirun analysis on the inclusive times
    df_test_inc = Chopper().multirun_analysis(
        graphframes=[gf1, gf2, gf4, gf8],
        metric="time (inc)",
        pivot_index="num_processes",
        columns="name",
    )

    # join the dataframes containing the dummy data and create a pivot table
    df_dummy_inc = pd.concat(
        [gf1.dataframe, gf2.dataframe, gf4.dataframe, gf8.dataframe]
    )
    df_dummy_inc = df_dummy_inc.pivot(
        index="num_processes", columns="name", values="time (inc)"
    )

    # check if the test and dummy dataframes match
    assert df_test_inc.equals(df_dummy_inc)
