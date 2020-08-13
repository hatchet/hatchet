# Copyright 2017-2020 Lawrence Livermore National Security, LLC and other
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

    assert len(graph_literal) == len(mock_graph_literal) == len(gf.graph.roots)
