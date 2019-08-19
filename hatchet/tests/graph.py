# Copyright 2017-2019 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from hatchet.node import Node
from hatchet.frame import Frame
from hatchet.graph import Graph


def test_from_lists():
    """Ensure we can traverse roots in correct order without repeating a
       shared subdag.
    """
    d = Node(Frame(name="d"))
    diamond_subdag = Node.from_lists(("a", ("b", d), ("c", d)))

    g = Graph.from_lists(("e", "f", diamond_subdag), ("g", diamond_subdag, "h"))
    assert list(g.traverse(attrs="name")) == ["e", "f", "a", "b", "d", "c", "g", "h"]


def test_copy():
    d = Node(Frame(name="d"))
    diamond_subdag = Node.from_lists(("a", ("b", d), ("c", d)))
    g = Graph.from_lists(("e", "f", diamond_subdag), ("g", diamond_subdag, "h"))

    assert g.copy() == g


def test_union_dag():
    # make graphs g1, g2, and g3, where you know g3 is the union of g1 and g2
    c = Node.from_lists(("c", "d"))
    g1 = Graph.from_lists(("a", ("b", c), ("e", c, "f")))

    d = Node(Frame(name="d"))
    g2 = Graph.from_lists(("a", ("b", ("c", d)), ("e", d, "f")))

    d2 = Node(Frame(name="d"))
    c2 = Node.from_lists(("c", d2))
    g3 = Graph.from_lists(("a", ("b", c2), ("e", c2, d2, "f")))

    assert g1 != g2

    g4 = g1.union(g2)

    assert g4 == g3
