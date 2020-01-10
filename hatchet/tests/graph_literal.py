# Copyright 2017-2020 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from hatchet import GraphFrame


def test_graphframe(mock_graph_literal):
    """Sanity test a GraphFrame object with known data."""
    gf = GraphFrame.from_literal(mock_graph_literal)

    assert len(gf.dataframe) == 24
