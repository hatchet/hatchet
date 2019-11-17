# Copyright 2017-2019 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import pytest

import numpy as np
import pandas as pd

from hatchet import GraphFrame
from hatchet.frame import Frame
from hatchet.graph import Graph
from hatchet.node import Node


def test_copy(mock_graph_literal):
    gf = GraphFrame.from_literal(mock_graph_literal)
    other = gf.copy()

    assert gf.graph is other.graph
    assert gf.dataframe is not other.dataframe
    assert gf.dataframe.equals(other.dataframe)
    assert gf.inc_metrics == other.inc_metrics
    assert gf.exc_metrics == other.exc_metrics


def test_deepcopy(mock_graph_literal):
    gf = GraphFrame.from_literal(mock_graph_literal)
    other = gf.deepcopy()

    assert gf.graph == other.graph
    assert gf.dataframe is not other.dataframe
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
    # indexes are the same since we are reading in the same dataset
    assert all(gf1.dataframe.index == gf2.dataframe.index)

    gf1.unify(gf2)

    assert gf1.graph is gf2.graph

    # Indexes should still be the same after unify. Sort indexes before comparing.
    gf1.dataframe.sort_index(inplace=True)
    gf2.dataframe.sort_index(inplace=True)
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


def test_from_lists():
    gf = GraphFrame.from_lists(("a", ("b", "c"), ("d", "e")))
    gf.dataframe.reset_index(inplace=True, drop=False)

    assert list(gf.graph.traverse(attrs="name")) == ["a", "b", "c", "d", "e"]

    assert all(gf.dataframe["time"] == ([1.0] * 5))

    nodes = set(gf.graph.traverse())
    assert all(node in list(gf.dataframe["node"]) for node in nodes)


def test_update_inclusive_metrics():
    gf = GraphFrame.from_lists(("a", ("b", "c"), ("d", "e")))
    (a, b, c, d, e) = gf.graph.traverse()

    # this is computed automatically by from_lists -- drop it for this test.
    del gf.dataframe["time (inc)"]

    gf.update_inclusive_columns()
    assert gf.dataframe.loc[a, "time (inc)"] == 5
    assert gf.dataframe.loc[b, "time (inc)"] == 2
    assert gf.dataframe.loc[c, "time (inc)"] == 1
    assert gf.dataframe.loc[d, "time (inc)"] == 2
    assert gf.dataframe.loc[e, "time (inc)"] == 1


def test_subtree_sum_value_error():
    gf = GraphFrame.from_lists(("a", ("b", "c"), ("d", "e")))

    # in and out columns with different lengths
    with pytest.raises(ValueError):
        gf.subtree_sum(["time"], [])


def test_subtree_sum_inplace():
    gf = GraphFrame.from_lists(("a", ("b", "c"), ("d", "e")))
    (a, b, c, d, e) = gf.graph.traverse()

    gf.subtree_sum(["time"])
    assert gf.dataframe.loc[a, "time"] == 5
    assert gf.dataframe.loc[b, "time"] == 2
    assert gf.dataframe.loc[c, "time"] == 1
    assert gf.dataframe.loc[d, "time"] == 2
    assert gf.dataframe.loc[e, "time"] == 1


def test_subtree_product():
    gf = GraphFrame.from_lists(("a", ("b", "c"), ("d", "e")))
    (a, b, c, d, e) = gf.graph.traverse()

    gf.dataframe["time2"] = gf.dataframe["time"] * 2

    gf.subtree_sum(["time", "time2"], ["out", "out2"], function=np.prod)
    assert gf.dataframe.loc[a, "out"] == 1
    assert gf.dataframe.loc[b, "out"] == 1
    assert gf.dataframe.loc[c, "out"] == 1
    assert gf.dataframe.loc[d, "out"] == 1
    assert gf.dataframe.loc[e, "out"] == 1

    assert gf.dataframe.loc[a, "out2"] == 32
    assert gf.dataframe.loc[b, "out2"] == 4
    assert gf.dataframe.loc[c, "out2"] == 2
    assert gf.dataframe.loc[d, "out2"] == 4
    assert gf.dataframe.loc[e, "out2"] == 2


def check_filter_squash(gf, filter_func, expected_graph, expected_inc_time):
    """Ensure filtering and squashing results in the right Graph and GraphFrame."""
    orig_graph = gf.graph.copy()

    filtered = gf.filter(filter_func)
    index_names = filtered.dataframe.index.names
    filtered.dataframe.reset_index(inplace=True)
    assert filtered.graph is gf.graph
    assert filtered.graph == orig_graph
    assert all(n in filtered.graph.traverse() for n in filtered.dataframe["node"])
    filtered.dataframe.set_index(index_names, inplace=True)

    squashed = filtered.squash()
    index_names = squashed.dataframe.index.names
    squashed.dataframe.reset_index(inplace=True, drop=False)
    assert filtered.graph is not squashed.graph
    assert squashed.graph == expected_graph
    assert len(squashed.dataframe.index) == len(expected_graph)
    squashed_node_names = list(expected_graph.traverse(attrs="name"))
    assert all(
        n.frame["name"] in squashed_node_names for n in squashed.dataframe["node"]
    )
    squashed.dataframe.set_index(index_names, inplace=True)

    # verify inclusive metrics at different nodes
    nodes = list(squashed.graph.traverse())
    assert len(nodes) == len(expected_inc_time)

    assert expected_inc_time == [
        squashed.dataframe.loc[node, "time (inc)"] for node in nodes
    ]


def test_filter_squash():
    r"""Test squash on a simple tree with one root.

          a
         / \      remove bd     a
        b   d    ---------->   / \
       /      \               c   e
      c        e

    """
    check_filter_squash(
        GraphFrame.from_lists(("a", ("b", "c"), ("d", "e"))),
        lambda row: row["node"].frame["name"] in ("a", "c", "e"),
        Graph.from_lists(("a", "c", "e")),
        [3, 1, 1],  # a, c, e
    )


def test_filter_squash_with_merge():
    r"""Test squash with a simple node merge.

          a
         / \      remove bd     a
        b   d    ---------->    |
       /      \                 c
      c        c

    Note that here, because b and d have been removed, a will have only
    one child called c, which will contain merged (summed) data from the
    original c rows.

    """
    check_filter_squash(
        GraphFrame.from_lists(("a", ("b", "c"), ("d", "c"))),
        lambda row: row["node"].frame["name"] in ("a", "c"),
        Graph.from_lists(("a", "c")),
        [3, 2],  # a, c
    )


def test_filter_squash_with_rootless_merge():
    r"""Test squash on a simple tree with several rootless node merges.

               a
          ___/ | \___     remove abcd
         b     c     d   ------------>  e f g
        /|\   /|\   /|\
       e f g e f g e f g

    Note that here, because b and d have been removed, a will have only
    one child called c, which will contain merged (summed) data from the
    original c rows.

    """
    check_filter_squash(
        GraphFrame.from_lists(
            ("a", ("b", "e", "f", "g"), ("c", "e", "f", "g"), ("d", "e", "f", "g"))
        ),
        lambda row: row["node"].frame["name"] not in ("a", "b", "c", "d"),
        Graph.from_lists(["e"], ["f"], ["g"]),
        [3, 3, 3],  # e, f, g
    )


def test_filter_squash_different_roots():
    r"""Test squash on a simple tree with one root but make multiple roots.

          a
         / \      remove a     b  d
        b   d    --------->   /    \
       /      \              c      e
      c        e

    """
    check_filter_squash(
        GraphFrame.from_lists(("a", ("b", "c"), ("d", "e"))),
        lambda row: row["node"].frame["name"] != "a",
        Graph.from_lists(("b", "c"), ("d", "e")),
        [2, 1, 2, 1],  # b, c, d, e
    )


def test_filter_squash_diamond():
    r"""Test that diamond edges are collapsed when squashing.

    Ensure we can handle the most basic DAG.

            a
           / \      remove bc     a
          b   c    ---------->    |
           \ /                    d
            d

    """
    d = Node(Frame(name="d"))
    check_filter_squash(
        GraphFrame.from_lists(("a", ("b", d), ("c", d))),
        lambda row: row["node"].frame["name"] not in ("b", "c"),
        Graph.from_lists(("a", "d")),
        [2, 1],  # a, d
    )


def test_filter_squash_bunny():
    r"""Test squash on a complicated "bunny" shaped graph.

    This has multiple roots as well as multiple parents that themselves
    have parents.

          e   g
         / \ / \
        f   a   h    remove abc     e   g
           / \      ----------->   / \ / \
          b   c                   f   d   h
           \ /
            d

    """
    d = Node(Frame(name="d"))
    diamond = Node.from_lists(("a", ("b", d), ("c", d)))

    new_d = Node(Frame(name="d"))

    check_filter_squash(
        GraphFrame.from_lists(("e", "f", diamond), ("g", diamond, "h")),
        lambda row: row["node"].frame["name"] not in ("a", "b", "c"),
        Graph.from_lists(("e", new_d, "f"), ("g", new_d, "h")),
        [3, 1, 1, 3, 1],  # e, d, f, g, h
    )


def test_filter_squash_bunny_to_goat():
    r"""Test squash on a "bunny" shaped graph:

    This one is more complex because there are more transitive edges to
    maintain between the roots (e, g) and b and c.

          e   g                     e   g
         / \ / \                   /|\ /|\
        f   a   h    remove ac    f | b | h
           / \      ---------->     | | |
          b   c                      \|/
           \ /                        d
            d

    """
    d = Node(Frame(name="d"))
    diamond = Node.from_lists(("a", ("b", d), ("c", d)))

    new_d = Node(Frame(name="d"))
    new_b = Node.from_lists(("b", new_d))

    check_filter_squash(
        GraphFrame.from_lists(("e", "f", diamond), ("g", diamond, "h")),
        lambda row: row["node"].frame["name"] not in ("a", "c"),
        Graph.from_lists(("e", new_b, new_d, "f"), ("g", new_b, new_d, "h")),
        [4, 2, 1, 1, 4, 1],  # e, b, d, f, g, h
    )


@pytest.mark.xfail(reason="Hatchet does not yet handle merging with parents properly.")
def test_filter_squash_bunny_to_goat_with_merge():
    r"""Test squash on a "bunny" shaped graph:

    This one is more complex because there are more transitive edges to
    maintain between the roots (e, g) and b and c.

          e   g
         / \ / \
        f   a   h    remove ac      e   g
           / \      ---------->    / \ / \
          b   c                   f   b   h
           \ /
            b

    """
    b = Node(Frame(name="b"))
    diamond = Node.from_lists(("a", ("b", b), ("c", b)))

    new_b = Node(Frame(name="b"))

    check_filter_squash(
        GraphFrame.from_lists(("e", "f", diamond), ("g", diamond, "h")),
        lambda row: row["node"].frame["name"] not in ("a", "c"),
        Graph.from_lists(("e", new_b, "f"), ("g", new_b, "h")),
        [4, 2, 1, 4, 1],  # e, b, f, g, h
    )


def test_filter_squash_mock_literal(mock_graph_literal):
    """Test the squash operation with a foo-bar tree."""
    gf = GraphFrame.from_literal(mock_graph_literal)
    nodes = list(gf.graph.traverse())
    assert not all(gf.dataframe.loc[nodes, "time"] > 5.0)
    filtered_gf = gf.filter(lambda x: x["time"] > 5.0)

    squashed_gf = filtered_gf.squash()
    squashed_nodes = list(squashed_gf.graph.traverse())
    assert all(squashed_gf.dataframe.loc[squashed_nodes, "time"] > 5.0)
    assert len(squashed_gf.graph) == 7


def test_tree(mock_graph_literal):
    gf = GraphFrame.from_literal(mock_graph_literal)

    output = gf.tree(metric="time", color=False)
    assert output.startswith("0.000 foo")
    assert "10.000 waldo" in output
    assert "15.000 garply" in output

    output = gf.tree(metric="time (inc)", color=False)
    assert "50.000 waldo" in output
    assert "15.000 garply" in output

    output = gf.tree(metric="time (inc)", threshold=0.3, color=False)
    assert "50.000 waldo" in output
    assert "15.000 garply" not in output


def test_to_dot(mock_graph_literal):
    gf = GraphFrame.from_literal(mock_graph_literal)
    output = gf.to_dot(metric="time")

    # do a simple edge check -- this isn't exhaustive
    for node in gf.graph.traverse():
        for child in node.children:
            assert '"%s" -> "%s"' % (node._hatchet_nid, child._hatchet_nid) in output
