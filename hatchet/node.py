# Copyright 2017-2019 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from functools import total_ordering

from .frame import Frame


@total_ordering
class Node:
    """A node in the graph. The node only stores its frame."""

    def __init__(self, frame_obj, parent=None):
        self.frame = frame_obj

        self.parents = []
        if parent is not None:
            self.add_parent(parent)
        self.children = []

    def add_parent(self, node):
        """Adds a parent to this node's list of parents."""
        assert isinstance(node, Node)
        self.parents.append(node)

    def add_child(self, node):
        """Adds a child to this node's list of children."""
        assert isinstance(node, Node)
        self.children.append(node)

    def check_dag_equal(self, other, vs=None, vo=None):
        """Check if DAG rooted at self has the same structure as that rooted at
        other.
        """
        if vs is None:
            vs = set()
        if vo is None:
            vo = set()

        vs.add(id(self))
        vo.add(id(other))

        # if number of children do not match, then nodes are not equal
        if len(self.children) != len(other.children):
            return False

        # sort children of each node by its frame
        ssorted = sorted(self.children, key=lambda x: x.frame)
        osorted = sorted(other.children, key=lambda x: x.frame)

        for self_child, other_child in zip(ssorted, osorted):
            # if frames do not match, then nodes are not equal
            if self_child.frame != other_child.frame:
                return False

            visited_s = id(self_child) in vs
            visited_o = id(other_child) in vo

            # check for duplicate nodes
            if visited_s != visited_o:
                return False

            # skip visited nodes
            if visited_s or visited_o:
                continue

            # recursive check for node equality
            if not self_child.check_dag_equal(other_child, vs, vo):
                return False

        return True

    def traverse(self, order="pre", attrs=None, visited=None):
        """Traverse the tree depth-first and yield each node.

        Arguments:
            order (str):  "pre" or "post" for preorder or postorder (default pre)
            attrs (list or str, optional): If provided, extract these fields
                from nodes while traversing and yield them.
        """
        if order not in ("pre", "post"):
            raise ValueError("order must be one of 'pre' or 'post'")

        if visited is None:
            visited = set()

        key = id(self)
        if key in visited:
            return
        visited.add(key)

        def value(node):
            return node if attrs is None else node.frame.values(attrs)

        if order == "pre":
            yield value(self)

        for child in self.children:
            for item in child.traverse(order, attrs, visited):
                yield item

        if order == "post":
            yield value(self)

    def __hash__(self):
        return hash(id(self))

    def __eq__(self, other):
        return id(self) == id(other)

    def __lt__(self, other):
        return id(self) < id(other)

    def __str__(self):
        """Returns a string representation of the node."""
        return str(self.frame)

    def copy(self):
        """Copy this node without preserving parents or children."""
        return Node(self.frame.copy())

    @classmethod
    def from_lists(cls, lists):
        r"""Construct a hierarchy of nodes from recursive lists.

        For example, this will construct a simple tree:

            Node.from_lists(
                ["a",
                    ["b", "d", "e"],
                    ["c", "f", "g"],
                ]
            )

                 a
                / \
               b   c
             / |   | \
            d  e   f  g

        And this will construct a simple diamond DAG:

            d = Node(Frame(name="d"))
            Node.from_lists(
                ["a",
                    ["b", d],
                    ["c", d]
                ]
            )

                 a
                / \
               b   c
                \ /
                 d

        In the above examples, the 'a' represents a Node with its
        frame == Frame(name="a").
        """

        def _from_lists(lists, parent):
            if isinstance(lists, (tuple, list)):
                node = Node(Frame(name=lists[0]))
                children = lists[1:]
                for val in children:
                    _ = _from_lists(val, node)
            elif isinstance(lists, str):
                node = Node(Frame(name=lists))
            elif isinstance(lists, Node):
                node = lists
            else:
                raise ValueError("Argument must be str, list, or Node: %s" % lists)

            if parent:
                node.add_parent(parent)
                parent.add_child(node)

            return node

        return _from_lists(lists, None)

    def __repr__(self):
        return "Node({%s})" % ", ".join(
            "%s: %s" % (repr(k), repr(v)) for k, v in sorted(self.frame.attrs.items())
        )
