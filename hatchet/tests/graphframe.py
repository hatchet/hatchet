# Copyright 2017-2019 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import pytest

import pandas as pd

from hatchet import GraphFrame
from hatchet.graph import Graph


def test_copy(mock_graph_literal):
    gf = GraphFrame.from_literal(mock_graph_literal)
    other = gf.copy()

    assert gf.graph == other.graph
    assert gf.inc_metrics == other.inc_metrics
    assert gf.exc_metrics == other.exc_metrics


def test_drop_index_levels(calc_pi_hpct_db):
    gf = GraphFrame.from_hpctoolkit(str(calc_pi_hpct_db))
    num_nodes = len(gf.graph)

    gf.drop_index_levels()
    num_rows = len(gf.dataframe.index)

    assert num_nodes == num_rows


def test_unify_hpctoolkit_data(calc_pi_hpct_db):
    gf1 = GraphFrame.from_hpctoolkit(str(calc_pi_hpct_db))
    gf2 = GraphFrame.from_hpctoolkit(str(calc_pi_hpct_db))

    assert gf1.graph is not gf2.graph
    with pytest.raises(ValueError):
        # this is an invalid comparison because the indexes are different at this point
        gf1.dataframe["node"].apply(id) != gf2.dataframe["node"].apply(id)
    assert all(gf1.dataframe.index != gf2.dataframe.index)

    gf1.unify(gf2)

    # indexes are now the same.
    assert gf1.graph is gf2.graph
    assert all(gf1.dataframe["node"].apply(id) == gf2.dataframe["node"].apply(id))
    assert all(gf1.dataframe.index == gf2.dataframe.index)


def test_invalid_constructor():
    # bad Graph
    with pytest.raises(ValueError):
        GraphFrame(None, None)

    # bad dataframe
    with pytest.raises(ValueError):
        GraphFrame(Graph([]), None)

    # dataframe has no "node" index
    with pytest.raises(ValueError):
        GraphFrame(Graph([]), pd.DataFrame())
