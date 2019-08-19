# Copyright 2017-2019 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from hatchet import GraphFrame


def test_filter(mock_graph_literal):
    """Test the filter operation with a foo-bar tree."""
    gf = GraphFrame()
    gf.from_literal(mock_graph_literal)

    filtered_gf = gf.filter(lambda x: x["time"] > 5.0)
    assert len(filtered_gf.dataframe) == 9
