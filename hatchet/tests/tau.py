# Copyright 2021-2024 University of Maryland and other Hatchet Project
# Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import numpy as np

from hatchet import GraphFrame
from hatchet.external.console import ConsoleRenderer

import pytest


def test_graphframe(tau_profile_dir):
    """Sanity test a GraphFrame object with known data."""
    gf = GraphFrame.from_tau(str(tau_profile_dir))

    for col in gf.dataframe.columns:
        if col in ("time (inc)", "time"):
            assert gf.dataframe[col].dtype == np.float64
        elif col in ("line"):
            assert gf.dataframe[col].dtype == np.int64
        elif col in ("name", "node"):
            assert gf.dataframe[col].dtype == object

    # TODO: add tests to confirm values in dataframe


def test_tree(tau_profile_dir):
    """Sanity test a GraphFrame object with known data."""
    gf = GraphFrame.from_tau(str(tau_profile_dir))

    # check the tree for rank 0
    output = ConsoleRenderer(unicode=True, color=False).render(
        gf.graph.roots,
        gf.dataframe,
        gf.get_node_metadata,
        metric_column="time",
        precision=3,
        name_column="name",
        expand_name=False,
        context_column="file",
        rank=0,
        thread=0,
        depth=10000,
        highlight_name=False,
        colormap="RdYlGn",
        invert_colormap=False,
    )
    assert "449.000 .TAU application" in output
    assert "4458.000 MPI_Finalize()" in output
    assert "218.000 MPI_Bcast()" in output

    # check the tree for rank 1
    output = ConsoleRenderer(unicode=True, color=False).render(
        gf.graph.roots,
        gf.dataframe,
        gf.get_node_metadata,
        metric_column="time",
        precision=3,
        name_column="name",
        expand_name=False,
        context_column="",
        rank=1,
        thread=0,
        depth=10000,
        highlight_name=False,
        colormap="RdYlGn",
        invert_colormap=False,
    )
    assert "419.000 .TAU application" in output
    assert "4894.000 MPI_Finalize()" in output
    assert "333.000 MPI_Bcast()" in output


def test_sparse_tree(sparse_tau_profile_dir):
    """Sanity test a GraphFrame object with known data."""
    gf = GraphFrame.from_tau(str(sparse_tau_profile_dir))
    df = gf.dataframe

    # check the tree for rank 0
    output = ConsoleRenderer(unicode=True, color=False).render(
        gf.graph.roots,
        gf.dataframe,
        gf.get_node_metadata,
        metric_column="time",
        precision=3,
        name_column="name",
        expand_name=False,
        context_column="file",
        rank=0,
        thread=0,
        depth=10000,
        highlight_name=False,
        colormap="RdYlGn",
        invert_colormap=False,
    )
    assert "241468023.000 .TAU application" in output
    assert "64835.000 MPI_Allreduce()" in output
    assert "0.000 [CONTEXT]  MPI_Allreduce()" in output
    # Ensure nan outputed when rank/thread didn't execute the node
    assert "nan [SAMPLE] MPI_Allreduce" in output
    # Make sure we aren't outputting nan when data exists
    allreduce_node_df = df[df["name"] == "[SAMPLE] MPI_Allreduce"]
    with pytest.raises(KeyError):
        allreduce_node_df.xs((0, 0), level=[1, 2])

    # check the tree for rank 1
    output = ConsoleRenderer(unicode=True, color=False).render(
        gf.graph.roots,
        gf.dataframe,
        gf.get_node_metadata,
        metric_column="time",
        precision=3,
        name_column="name",
        expand_name=False,
        context_column="",
        rank=1,
        thread=0,
        depth=10000,
        highlight_name=False,
        colormap="RdYlGn",
        invert_colormap=False,
    )
    assert "235063506.000 .TAU application" in output
    assert "5893592.000 MPI_Allreduce()" in output
    assert "0.000 [CONTEXT]  MPI_Allreduce()" in output
    # Ensure nan outputed when rank/thread didn't execute the node
    assert "nan [SAMPLE] MPI_Allreduce" in output
    # Make sure we aren't outputting nan when data exists
    allreduce_node_df = df[df["name"] == "[SAMPLE] MPI_Allreduce"]
    with pytest.raises(KeyError):
        allreduce_node_df.xs((1, 0), level=[1, 2])


def test_children(tau_profile_dir):
    gf = GraphFrame.from_tau(str(tau_profile_dir))
    root = gf.graph.roots
    root_children = [
        "MPI_Init()",
        "MPI_Comm_size()",
        "MPI_Comm_rank()",
        "MPI_Get_processor_name()",
        "MPI_Bcast()",
        "MPI_Reduce()",
        "MPI_Finalize()",
    ]

    # check if only one root node is created
    assert len(root) == 1

    # check if root has right children #TODO: can be improved
    for child in root[0].children:
        assert child.frame["name"] in root_children


def test_graphframe_to_literal(tau_profile_dir):
    """Sanity test a GraphFrame object with known data."""
    gf = GraphFrame.from_tau(str(tau_profile_dir))
    graph_literal = gf.to_literal()

    gf_literal = GraphFrame.from_literal(graph_literal)

    assert len(gf.graph) == len(gf_literal.graph)
