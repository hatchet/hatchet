# Copyright 2017-2019 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from hatchet import GraphFrame


def test_filter(mock_graph_literal):
    """Test the filter operation with a foo-bar tree."""
    gf = GraphFrame.from_literal(mock_graph_literal)

    filtered_gf = gf.filter(lambda x: x["time"] > 5.0)
    assert len(filtered_gf.dataframe) == 9
    assert all(time > 5.0 for time in filtered_gf.dataframe["time"])

    filtered_gf = gf.filter(lambda x: x["name"].startswith("g"))
    assert len(filtered_gf.dataframe) == 7
    assert all(name.startswith("g") for name in filtered_gf.dataframe["name"])


def test_add(mock_graph_literal):
    gf1 = GraphFrame.from_literal(mock_graph_literal)
    gf2 = GraphFrame.from_literal(mock_graph_literal)

    assert gf1.graph is not gf2.graph

    gf3 = gf1.add(gf2)

    assert gf3.graph == gf1.graph.union(gf2.graph)

    assert gf3.dataframe["time"].sum() == 330
    assert gf3.dataframe["time (inc)"].sum() == 1280

    gf4 = gf3.copy()
    assert gf4.graph is gf3.graph

    gf5 = gf3.add(gf4)
    assert gf5.graph == gf3.graph == gf4.graph


def test_sub(mock_graph_literal):
    gf1 = GraphFrame.from_literal(mock_graph_literal)
    gf2 = GraphFrame.from_literal(mock_graph_literal)

    assert gf1.graph is not gf2.graph

    gf3 = gf1.sub(gf2)

    assert gf3.graph == gf1.graph.union(gf2.graph)

    for metric in gf3.exc_metrics + gf3.inc_metrics:
        assert gf3.dataframe[metric].sum() == 0

    gf4 = gf3.copy()
    assert gf4.graph is gf3.graph

    gf5 = gf3.sub(gf4)
    assert gf5.graph == gf3.graph == gf4.graph


def test_add_operator(mock_graph_literal):
    gf1 = GraphFrame.from_literal(mock_graph_literal)
    gf2 = GraphFrame.from_literal(mock_graph_literal)

    assert gf1.graph is not gf2.graph

    gf3 = gf1 + gf2

    assert gf3.graph == gf1.graph.union(gf2.graph)

    assert gf3.dataframe["time"].sum() == 330
    assert gf3.dataframe["time (inc)"].sum() == 1280

    gf4 = gf3.copy()
    assert gf4.graph is gf3.graph

    gf5 = gf3 + gf4
    assert gf5.graph == gf3.graph == gf4.graph


def test_sub_operator(mock_graph_literal):
    gf1 = GraphFrame.from_literal(mock_graph_literal)
    gf2 = GraphFrame.from_literal(mock_graph_literal)

    assert gf1.graph is not gf2.graph

    gf3 = gf1 - gf2

    assert gf3.graph == gf1.graph.union(gf2.graph)

    for metric in gf3.exc_metrics + gf3.inc_metrics:
        assert gf3.dataframe[metric].sum() == 0

    gf4 = gf3.copy()
    assert gf4.graph is gf3.graph

    gf5 = gf3.sub(gf4)

    assert gf5.graph == gf3.graph == gf4.graph


def test_iadd_operator(mock_graph_literal):
    gf1 = GraphFrame.from_literal(mock_graph_literal)
    gf2 = GraphFrame.from_literal(mock_graph_literal)

    assert gf1.graph is not gf2.graph

    gf1 += gf2

    assert gf1.graph == gf1.graph.union(gf2.graph)

    assert gf1.dataframe["time"].sum() == 330
    assert gf1.dataframe["time (inc)"].sum() == 1280

    gf3 = gf1.copy()
    assert gf3.graph is gf1.graph

    gf3 += gf1

    assert gf3.graph == gf1.graph


def test_isub_operator(mock_graph_literal):
    gf1 = GraphFrame.from_literal(mock_graph_literal)
    gf2 = GraphFrame.from_literal(mock_graph_literal)

    assert gf1.graph is not gf2.graph

    gf1 -= gf2

    assert gf1.graph == gf1.graph.union(gf2.graph)

    for metric in gf1.exc_metrics + gf1.inc_metrics:
        assert gf1.dataframe[metric].sum() == 0

    gf3 = gf1.copy()
    assert gf3.graph is gf1.graph

    gf3 -= gf1

    assert gf3.graph == gf1.graph
