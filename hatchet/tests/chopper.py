import numpy as np
from hatchet.graphframe import GraphFrame


def test_flat_profile(calc_pi_hpct_db):
    """Validate that the flat profile works correctly."""
    graphframe = GraphFrame.from_hpctoolkit(str(calc_pi_hpct_db))
    original_rows = graphframe.dataframe["name"].unique()
    flat_profile = graphframe.flat_profile(
        groupby_column="time (inc)",
        drop_ranks=True,
        drop_threads=True,
        agg_function=np.mean,
    )

    # Check if the node names are exactly the same
    assert sorted(flat_profile.index.tolist()) == sorted(original_rows)

    # Check if value is correct for the root node.
    root = graphframe.graph.roots[0]
    assert flat_profile.loc[root.frame["name"]]["time (inc)"] == np.mean(
        graphframe.dataframe.loc[root]["time (inc)"].to_numpy()
    )

    # Check if load imbalance is correct for the the node '__GI_sched_yield'.
    another = graphframe.dataframe[
        graphframe.dataframe["name"] == "__GI_sched_yield"
    ].index[0][0]
    assert flat_profile.loc[another.frame["name"]]["time (inc)"] == np.mean(
        graphframe.dataframe.loc[another]["time (inc)"].to_numpy()
    )


def test_calculate_load_imbalance(calc_pi_hpct_db):
    """Validate that the load imbalance is calculated correctly."""

    graphframe = GraphFrame.from_hpctoolkit(str(calc_pi_hpct_db))
    load_imb_gf = graphframe.calculate_load_imbalance(metric_columns=["time (inc)"])

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
    program_root = graphframe.graph.roots[0]

    # Correctness of this list is check
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

    hot_path = graphframe.hot_path(program_root)

    for node in hot_path:
        assert node.frame["name"] in hpctoolkit_hot_path
