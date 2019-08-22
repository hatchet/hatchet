# Copyright 2017-2019 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from hatchet import GraphFrame


def test_copy(mock_graph_literal):
    gf = GraphFrame()
    gf.from_literal(mock_graph_literal)

    other = gf.copy()

    assert gf.graph == other.graph
    assert gf.inc_metrics == other.inc_metrics
    assert gf.exc_metrics == other.exc_metrics


def test_drop_index_levels(calc_pi_hpct_db):
    gf = GraphFrame()
    gf.from_hpctoolkit(str(calc_pi_hpct_db))
    num_nodes = len(gf.graph)

    gf.drop_index_levels()
    num_rows = len(gf.dataframe.index)

    assert num_nodes == num_rows

def test_squash(mock_graph_literal):
    """Test the squash operation with a foo-bar tree."""
    gf = GraphFrame()
    gf.from_literal(mock_graph_literal)

    filtered_gf = gf.filter(lambda x: x["time"] > 5.0)

    squashed_gf = filtered_gf.squash()
    assert len(squashed_gf.dataframe) == 5
