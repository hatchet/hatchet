# Copyright 2017-2019 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from hatchet.node import Node
from hatchet.frame import Frame


def test_from_lists():
    node = Node.from_lists("a")
    assert node.frame == Frame(name="a")

    a = Frame(name="a")
    b = Frame(name="b")
    c = Frame(name="c")

    node = Node.from_lists(["a", ["b", "c"]])

    assert node.frame == a
    assert node.children[0].frame == b
    assert node.children[0].children[0].frame == c


def test_traverse_pre():
    node = Node.from_lists(["a", ["b", "d", "e"], ["c", "f", "g"]])
    assert list(node.traverse(attrs="name")) == ["a", "b", "d", "e", "c", "f", "g"]


def test_traverse_post():
    node = Node.from_lists(["a", ["b", "d", "e"], ["c", "f", "g"]])
    assert list(node.traverse(order="post", attrs="name")) == [
        "d",
        "e",
        "b",
        "f",
        "g",
        "c",
        "a",
    ]


def test_traverse_dag():
    d = Node(Frame(name="d"))
    node = Node.from_lists(["a", ["b", d], ["c", d]])
    assert list(node.traverse(attrs="name")) == ["a", "b", "d", "c"]


def test_node_repr():
    d = Node(Frame(a=1, b=2, c=3))
    assert repr(d) == "Node({'a': 1, 'b': 2, 'c': 3})"
