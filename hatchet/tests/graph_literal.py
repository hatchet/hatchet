# Copyright 2017-2021 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from hatchet import GraphFrame


def test_graphframe(mock_graph_literal):
    """Sanity test a GraphFrame object with known data."""
    gf = GraphFrame.from_literal(mock_graph_literal)

    assert len(gf.dataframe) == 24


def test_graphframe_to_literal(mock_graph_literal):
    gf = GraphFrame.from_literal(mock_graph_literal)
    graph_literal = gf.to_literal()

    test_literal_output = gf.from_literal(graph_literal)

    assert len(test_literal_output.graph.roots) == len(gf.graph.roots)
    assert len(test_literal_output.graph) == len(gf.graph)


def test_with_duplicates(mock_graph_literal_duplicates):
    gf = GraphFrame.from_literal(mock_graph_literal_duplicates)

    assert len(gf.graph) == 6

    graph_literal = gf.to_literal()
    assert mock_graph_literal_duplicates.sort() == graph_literal.sort()


def test_with_duplicate_in_first_node(mock_graph_literal_duplicate_first):
    gf = GraphFrame.from_literal(mock_graph_literal_duplicate_first)

    assert len(gf.graph) == 6

    graph_literal = gf.to_literal()
    assert mock_graph_literal_duplicate_first.sort() == graph_literal.sort()
