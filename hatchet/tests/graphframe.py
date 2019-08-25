# Copyright 2017-2019 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import pytest

import pandas as pd

from hatchet import GraphFrame
from hatchet.frame import Frame
from hatchet.graph import Graph
from hatchet.node import Node


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


def test_from_lists():
    gf = GraphFrame.from_lists(("a", ("b", "c"), ("d", "e")))

    assert list(gf.graph.traverse(attrs="name")) == ["a", "b", "c", "d", "e"]

    assert all(gf.dataframe["time"] == ([1.0] * 5))

    nodes = set(gf.graph.traverse())
    assert all(node in gf.dataframe["node"] for node in nodes)


def check_filter_squash(gf, filter_func, expected_graph):
    """Ensure filtering and squashing results in the right Graph and GraphFrame."""
    orig_graph = gf.graph.copy()

    filtered = gf.filter(filter_func)
    assert filtered.graph is gf.graph
    assert filtered.graph == orig_graph
    assert all(n in filtered.graph.traverse() for n in filtered.dataframe["node"])

    squashed = filtered.squash()
    assert filtered.graph is gf.graph
    assert filtered.graph is not squashed.graph
    assert all(n not in gf.graph.traverse() for n in squashed.dataframe["node"])

    assert squashed.graph == expected_graph
    assert len(squashed.dataframe.index) == len(expected_graph)
    squashed_node_names = list(expected_graph.traverse(attrs="name"))
    assert all(
        n.frame["name"] in squashed_node_names for n in squashed.dataframe["node"]
    )


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
    )


def test_filter_squash_diamond():
    r"""Test taht diamond edges are collapsed when squashing.

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
        Graph.from_lists(("e", "f", new_d), ("g", new_d, "h")),
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
        Graph.from_lists(("e", "f", new_d, new_b), ("g", new_b, new_d, "h")),
    )
