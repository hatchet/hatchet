# Copyright 2017-2020 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import pytest

import re

from hatchet import GraphFrame
from hatchet.node import traversal_order
from hatchet.query_matcher import QueryMatcher, InvalidQueryFilter, InvalidQueryPath


def test_construct_high_level_api():
    mock_node_mpi = {"name": "MPI_Bcast"}
    mock_node_ibv = {"name": "ibv_reg_mr"}
    mock_node_time_true = {"time (inc)": 0.1}
    mock_node_time_false = {"time (inc)": 0.001}
    path1 = [{"name": "MPI_[_a-zA-Z]*"}, "*", {"name": "ibv[_a-zA-Z]*"}]
    path2 = [{"name": "MPI_[_a-zA-Z]*"}, 2, {"name": "ibv[_a-zA-Z]*"}]
    path3 = [
        {"name": "MPI_[_a-zA-Z]*"},
        ("+", {"time (inc)": ">= 0.1"}),
        {"name": "ibv[_a-zA-Z]*"},
    ]
    path4 = [
        {"name": "MPI_[_a-zA-Z]*"},
        (3, {"time (inc)": 0.1}),
        {"name": "ibv[_a-zA-Z]*"},
    ]
    query1 = QueryMatcher(path1)
    query2 = QueryMatcher(path2)
    query3 = QueryMatcher(path3)
    query4 = QueryMatcher(path4)

    assert query1.query_pattern[0][0] == "."
    assert query1.query_pattern[0][1](mock_node_mpi)
    assert not query1.query_pattern[0][1](mock_node_ibv)
    assert not query1.query_pattern[0][1](mock_node_time_true)
    assert query1.query_pattern[1][0] == "*"
    assert query1.query_pattern[1][1](mock_node_mpi)
    assert query1.query_pattern[1][1](mock_node_ibv)
    assert query1.query_pattern[1][1](mock_node_time_true)
    assert query1.query_pattern[1][1](mock_node_time_false)
    assert query1.query_pattern[2][0] == "."

    assert query2.query_pattern[0][0] == "."
    assert query2.query_pattern[1][0] == "."
    assert query2.query_pattern[1][1](mock_node_mpi)
    assert query2.query_pattern[1][1](mock_node_ibv)
    assert query2.query_pattern[1][1](mock_node_time_true)
    assert query2.query_pattern[1][1](mock_node_time_false)
    assert query2.query_pattern[2][0] == "."
    assert query2.query_pattern[2][1](mock_node_mpi)
    assert query2.query_pattern[2][1](mock_node_ibv)
    assert query2.query_pattern[2][1](mock_node_time_true)
    assert query2.query_pattern[2][1](mock_node_time_false)
    assert query2.query_pattern[3][0] == "."

    assert query3.query_pattern[0][0] == "."
    assert query3.query_pattern[1][0] == "+"
    assert not query3.query_pattern[1][1](mock_node_mpi)
    assert not query3.query_pattern[1][1](mock_node_ibv)
    assert query3.query_pattern[1][1](mock_node_time_true)
    assert not query3.query_pattern[1][1](mock_node_time_false)
    assert query3.query_pattern[2][0] == "."

    assert query4.query_pattern[0][0] == "."
    assert query4.query_pattern[1][0] == "."
    assert not query4.query_pattern[1][1](mock_node_mpi)
    assert not query4.query_pattern[1][1](mock_node_ibv)
    assert query4.query_pattern[1][1](mock_node_time_true)
    assert not query4.query_pattern[1][1](mock_node_time_false)
    assert query4.query_pattern[2][0] == "."
    assert not query4.query_pattern[2][1](mock_node_mpi)
    assert not query4.query_pattern[2][1](mock_node_ibv)
    assert query4.query_pattern[2][1](mock_node_time_true)
    assert not query4.query_pattern[2][1](mock_node_time_false)
    assert query4.query_pattern[3][0] == "."
    assert not query4.query_pattern[3][1](mock_node_mpi)
    assert not query4.query_pattern[3][1](mock_node_ibv)
    assert query4.query_pattern[3][1](mock_node_time_true)
    assert not query4.query_pattern[3][1](mock_node_time_false)
    assert query4.query_pattern[4][0] == "."

    invalid_path = [
        {"name": "MPI_[_a-zA-Z]*"},
        ({"bad": "wildcard"}, {"time (inc)": 0.1}),
        {"name": "ibv[_a-zA-Z]*"},
    ]
    with pytest.raises(InvalidQueryPath):
        _ = QueryMatcher(invalid_path)

    invalid_path = [["name", "MPI_[_a-zA-Z]*"], "*", {"name": "ibv[_a-zA-Z]*"}]
    with pytest.raises(InvalidQueryPath):
        _ = QueryMatcher(invalid_path)


def test_construct_low_level_api():
    mock_node_mpi = {"name": "MPI_Bcast"}
    mock_node_ibv = {"name": "ibv_reg_mr"}
    mock_node_time_true = {"time (inc)": 0.1}
    mock_node_time_false = {"time (inc)": 0.001}

    def mpi_filter(df_row):
        if "name" not in df_row:
            return False
        if re.match(r"MPI_[_a-zA-Z]*\Z", df_row["name"]) is not None:
            return True
        return False

    def ibv_filter(df_row):
        if "name" not in df_row:
            return False
        if re.match(r"ibv[_a-zA-Z]*\Z", df_row["name"]) is not None:
            return True
        return False

    def time_ge_filter(df_row):
        if "time (inc)" not in df_row:
            return False
        return df_row["time (inc)"] >= 0.1

    def time_eq_filter(df_row):
        if "time (inc)" not in df_row:
            return False
        return df_row["time (inc)"] == 0.1

    query = QueryMatcher()

    query.match(filter_func=mpi_filter).rel("*").rel(filter_func=ibv_filter)
    assert query.query_pattern[0][0] == "."
    assert query.query_pattern[0][1](mock_node_mpi)
    assert not query.query_pattern[0][1](mock_node_ibv)
    assert not query.query_pattern[0][1](mock_node_time_true)
    assert query.query_pattern[1][0] == "*"
    assert query.query_pattern[1][1](mock_node_mpi)
    assert query.query_pattern[1][1](mock_node_ibv)
    assert query.query_pattern[1][1](mock_node_time_true)
    assert query.query_pattern[1][1](mock_node_time_false)
    assert query.query_pattern[2][0] == "."

    query.match(filter_func=mpi_filter).rel(2).rel(filter_func=ibv_filter)
    assert query.query_pattern[0][0] == "."
    assert query.query_pattern[1][0] == "."
    assert query.query_pattern[1][1](mock_node_mpi)
    assert query.query_pattern[1][1](mock_node_ibv)
    assert query.query_pattern[1][1](mock_node_time_true)
    assert query.query_pattern[1][1](mock_node_time_false)
    assert query.query_pattern[2][0] == "."
    assert query.query_pattern[2][1](mock_node_mpi)
    assert query.query_pattern[2][1](mock_node_ibv)
    assert query.query_pattern[2][1](mock_node_time_true)
    assert query.query_pattern[2][1](mock_node_time_false)
    assert query.query_pattern[3][0] == "."

    query.match(filter_func=mpi_filter).rel("+", time_ge_filter).rel(
        filter_func=ibv_filter
    )
    assert query.query_pattern[0][0] == "."
    assert query.query_pattern[1][0] == "+"
    assert not query.query_pattern[1][1](mock_node_mpi)
    assert not query.query_pattern[1][1](mock_node_ibv)
    assert query.query_pattern[1][1](mock_node_time_true)
    assert not query.query_pattern[1][1](mock_node_time_false)
    assert query.query_pattern[2][0] == "."

    query.match(filter_func=mpi_filter).rel(3, time_eq_filter).rel(
        filter_func=ibv_filter
    )
    assert query.query_pattern[0][0] == "."
    assert query.query_pattern[1][0] == "."
    assert not query.query_pattern[1][1](mock_node_mpi)
    assert not query.query_pattern[1][1](mock_node_ibv)
    assert query.query_pattern[1][1](mock_node_time_true)
    assert not query.query_pattern[1][1](mock_node_time_false)
    assert query.query_pattern[2][0] == "."
    assert not query.query_pattern[2][1](mock_node_mpi)
    assert not query.query_pattern[2][1](mock_node_ibv)
    assert query.query_pattern[2][1](mock_node_time_true)
    assert not query.query_pattern[2][1](mock_node_time_false)
    assert query.query_pattern[3][0] == "."
    assert not query.query_pattern[3][1](mock_node_mpi)
    assert not query.query_pattern[3][1](mock_node_ibv)
    assert query.query_pattern[3][1](mock_node_time_true)
    assert not query.query_pattern[3][1](mock_node_time_false)
    assert query.query_pattern[4][0] == "."


def test_node_caching(mock_graph_literal):
    path = [{"name": "fr[a-z]+"}, ("+", {"time (inc)": ">= 25.0"}), {"name": "baz"}]
    gf = GraphFrame.from_literal(mock_graph_literal)
    node = gf.graph.roots[0].children[2].children[0]

    query = QueryMatcher(path)
    query._cache_node(gf, node)

    assert 0 in query.search_cache[node._hatchet_nid]
    assert 1 in query.search_cache[node._hatchet_nid]
    assert 2 not in query.search_cache[node._hatchet_nid]


def test_match_0_or_more_wildcard(mock_graph_literal):
    path = [
        {"name": "qux"},
        ("*", {"time (inc)": "> 10"}),
        {"name": "gr[a-z]+", "time (inc)": "<= 10"},
    ]
    gf = GraphFrame.from_literal(mock_graph_literal)
    node = gf.graph.roots[0].children[1]
    none_node = gf.graph.roots[0].children[2].children[0].children[1].children[0]

    correct_paths = [
        [
            node.children[0],
            node.children[0].children[0],
            node.children[0].children[0].children[0],
        ],
        [node.children[0], node.children[0].children[0]],
    ]

    query = QueryMatcher(path)
    matched_paths = []
    for child in sorted(node.children, key=traversal_order):
        match = query._match_0_or_more(gf, child, 1)
        if match is not None:
            matched_paths.extend(match)

    assert sorted(matched_paths, key=len) == sorted(correct_paths, key=len)
    assert query._match_0_or_more(gf, none_node, 1) is None


def test_match_1_or_more_wildcard(mock_graph_literal):
    path = [
        {"name": "qux"},
        ("+", {"time (inc)": "> 10"}),
        {"name": "gr[a-z]+", "time (inc)": "<= 10"},
    ]
    gf = GraphFrame.from_literal(mock_graph_literal)
    node = gf.graph.roots[0].children[1]
    none_node = gf.graph.roots[0].children[2].children[0].children[1].children[0]

    correct_paths = [
        [
            node.children[0],
            node.children[0].children[0],
            node.children[0].children[0].children[0],
        ],
        [node.children[0], node.children[0].children[0]],
    ]

    query = QueryMatcher(path)
    matched_paths = []
    for child in sorted(node.children, key=traversal_order):
        match = query._match_1_or_more(gf, child, 1)
        if match is not None:
            matched_paths.extend(match)

    assert matched_paths == correct_paths
    assert query._match_1_or_more(gf, none_node, 1) is None

    zero_match_path = [
        {"name": "qux"},
        ("+", {"time (inc)": "> 50"}),
        {"name": "gr[a-z]+", "time (inc)": "<= 10"},
    ]
    zero_match_node = gf.graph.roots[0].children[0]
    query = QueryMatcher(zero_match_path)
    assert query._match_1_or_more(gf, zero_match_node, 1) is None


def test_match_1(mock_graph_literal):
    gf = GraphFrame.from_literal(mock_graph_literal)
    path = [
        {"name": "qux"},
        ("*", {"time (inc)": "> 10"}),
        {"name": "gr[a-z]+", "time (inc)": "<= 10.0"},
    ]
    query = QueryMatcher(path)

    assert query._match_1(gf, gf.graph.roots[0].children[0], 2) == [
        [gf.graph.roots[0].children[0].children[1]]
    ]
    assert query._match_1(gf, gf.graph.roots[0], 2) is None


def test_match(mock_graph_literal):
    gf = GraphFrame.from_literal(mock_graph_literal)
    root = gf.graph.roots[0].children[2]

    path0 = [
        {"name": "waldo"},
        "+",
        {"time (inc)": ">= 20.0"},
        "+",
        {"time (inc)": 5.0, "time": 5.0},
    ]
    match0 = [
        [
            root,
            root.children[0],
            root.children[0].children[1],
            root.children[0].children[1].children[0],
            root.children[0].children[1].children[0].children[0],
        ]
    ]
    query0 = QueryMatcher(path0)
    assert query0._match_pattern(gf, root, 0) == match0

    path1 = [
        {"name": "waldo"},
        ("+", {}),
        {"time (inc)": ">= 20.0"},
        "+",
        {"time (inc)": 7.5, "time": 7.5},
    ]
    query1 = QueryMatcher(path1)
    assert query1._match_pattern(gf, root, 0) is None


def test_apply(mock_graph_literal):
    gf = GraphFrame.from_literal(mock_graph_literal)
    path = [
        {"time (inc)": ">= 30.0"},
        (2, {"name": "[^b][a-z]+"}),
        ("*", {"name": "[^b][a-z]+"}),
        {"name": "gr[a-z]+"},
    ]
    root = gf.graph.roots[0]
    match = [
        [
            root,
            root.children[1],
            root.children[1].children[0],
            root.children[1].children[0].children[0],
            root.children[1].children[0].children[0].children[1],
        ],
        [
            root.children[1],
            root.children[1].children[0],
            root.children[1].children[0].children[0],
            root.children[1].children[0].children[0].children[1],
        ],
    ]
    query = QueryMatcher(path)

    assert query.apply(gf) == match

    path = [{"time (inc)": ">= 30.0"}, ".", {"name": "bar"}, "*"]
    match = [
        [
            root.children[1].children[0],
            root.children[1].children[0].children[0],
            root.children[1].children[0].children[0].children[0],
            root.children[1].children[0].children[0].children[0].children[0],
        ],
        [
            root.children[1].children[0],
            root.children[1].children[0].children[0],
            root.children[1].children[0].children[0].children[0],
            root.children[1].children[0].children[0].children[0].children[1],
        ],
    ]
    query = QueryMatcher(path)
    assert query.apply(gf) == match

    path = [{"name": "foo"}, {"name": "bar"}, {"time": 5.0}]
    match = [[root, root.children[0], root.children[0].children[0]]]
    query = QueryMatcher(path)
    assert query.apply(gf) == match

    path = [{"name": "foo"}, {"name": "qux"}, ("+", {"time (inc)": "> 15.0"})]
    match = [
        [
            root,
            root.children[1],
            root.children[1].children[0],
            root.children[1].children[0].children[0],
            root.children[1].children[0].children[0].children[0],
        ],
        [
            root,
            root.children[1],
            root.children[1].children[0],
            root.children[1].children[0].children[0],
        ],
    ]
    query = QueryMatcher(path)
    assert query.apply(gf) == match

    path = [{"name": "this"}, ("*", {"name": "is"}), {"name": "nonsense"}]

    query = QueryMatcher(path)
    assert query.apply(gf) == []

    path = [{"name": 5}, "*", {"name": "whatever"}]
    query = QueryMatcher(path)
    with pytest.raises(InvalidQueryFilter):
        query.apply(gf)

    path = [{"time": "badstring"}, "*", {"name": "whatever"}]
    query = QueryMatcher(path)
    with pytest.raises(InvalidQueryFilter):
        query.apply(gf)

    class DummyType:
        def __init__(self):
            self.x = 5.0
            self.y = -1
            self.z = "hello"

    bad_field_test_dict = list(mock_graph_literal)
    bad_field_test_dict[0]["children"][0]["children"][0]["metrics"][
        "list"
    ] = DummyType()
    gf = GraphFrame.from_literal(bad_field_test_dict)
    path = [{"name": "foo"}, {"name": "bar"}, {"list": DummyType()}]
    query = QueryMatcher(path)
    with pytest.raises(InvalidQueryFilter):
        query.apply(gf)

    path = ["*", {"name": "bar"}, {"name": "grault"}, "*"]
    match = [
        [root, root.children[0], root.children[0].children[1]],
        [root.children[0], root.children[0].children[1]],
        [
            root,
            root.children[1],
            root.children[1].children[0],
            root.children[1].children[0].children[0],
            root.children[1].children[0].children[0].children[0],
            root.children[1].children[0].children[0].children[0].children[1],
        ],
        [
            root.children[1],
            root.children[1].children[0],
            root.children[1].children[0].children[0],
            root.children[1].children[0].children[0].children[0],
            root.children[1].children[0].children[0].children[0].children[1],
        ],
        [
            root.children[1].children[0],
            root.children[1].children[0].children[0],
            root.children[1].children[0].children[0].children[0],
            root.children[1].children[0].children[0].children[0].children[1],
        ],
        [
            root.children[1].children[0].children[0],
            root.children[1].children[0].children[0].children[0],
            root.children[1].children[0].children[0].children[0].children[1],
        ],
        [
            root.children[1].children[0].children[0].children[0],
            root.children[1].children[0].children[0].children[0].children[1],
        ],
        [
            gf.graph.roots[1],
            gf.graph.roots[1].children[0],
            gf.graph.roots[1].children[0].children[1],
        ],
        [gf.graph.roots[1].children[0], gf.graph.roots[1].children[0].children[1]],
    ]
    query = QueryMatcher(path)
    assert sorted(query.apply(gf)) == sorted(match)

    path = ["*", {"name": "bar"}, {"name": "grault"}, "+"]
    query = QueryMatcher(path)
    assert query.apply(gf) == []


def test_apply_indices(calc_pi_hpct_db):
    gf = GraphFrame.from_hpctoolkit(str(calc_pi_hpct_db))
    main = gf.graph.roots[0].children[0]
    path = [
        {"name": "[0-9]*:?MPI_.*"},
        ("*", {"name": "^((?!MPID).)*"}),
        {"name": "[0-9]*:?MPID.*"},
    ]
    matches = [
        [
            main.children[0],
            main.children[0].children[0],
            main.children[0].children[0].children[0],
            main.children[0].children[0].children[0].children[0],
        ],
        [
            main.children[1],
            main.children[1].children[0],
            main.children[1].children[0].children[0],
        ],
    ]
    query = QueryMatcher(path)
    assert query.apply(gf) == matches

    gf.drop_index_levels()
    assert query.apply(gf) == matches


def test_high_level_depth(mock_graph_literal):
    gf = GraphFrame.from_literal(mock_graph_literal)
    query = QueryMatcher([("*", {"depth": 1})])
    roots = gf.graph.roots
    matches = [[c] for r in roots for c in r.children]
    assert query.apply(gf) == matches

    query = QueryMatcher([("*", {"depth": "<= 2"})])
    matches = [
        [roots[0], roots[0].children[0], roots[0].children[0].children[0]],
        [roots[0].children[0], roots[0].children[0].children[0]],
        [roots[0].children[0].children[0]],
        [roots[0], roots[0].children[0], roots[0].children[0].children[1]],
        [roots[0].children[0], roots[0].children[0].children[1]],
        [roots[0].children[0].children[1]],
        [roots[0], roots[0].children[1], roots[0].children[1].children[0]],
        [roots[0].children[1], roots[0].children[1].children[0]],
        [roots[0].children[1].children[0]],
        [roots[0], roots[0].children[2], roots[0].children[2].children[0]],
        [roots[0].children[2], roots[0].children[2].children[0]],
        [roots[0].children[2].children[0]],
        [roots[0], roots[0].children[2], roots[0].children[2].children[1]],
        [roots[0].children[2], roots[0].children[2].children[1]],
        [roots[0].children[2].children[1]],
        [roots[1], roots[1].children[0], roots[1].children[0].children[0]],
        [roots[1].children[0], roots[1].children[0].children[0]],
        [roots[1].children[0].children[0]],
        [roots[1], roots[1].children[0], roots[1].children[0].children[1]],
        [roots[1].children[0], roots[1].children[0].children[1]],
        [roots[1].children[0].children[1]],
    ]
    assert sorted(query.apply(gf)) == sorted(matches)

    with pytest.raises(InvalidQueryFilter):
        query = QueryMatcher([{"depth": "hello"}])
        query.apply(gf)


def test_high_level_hatchet_nid(mock_graph_literal):
    gf = GraphFrame.from_literal(mock_graph_literal)
    query = QueryMatcher([("*", {"node_id": ">= 20"})])
    root = gf.graph.roots[1]
    matches = [
        [root, root.children[0], root.children[0].children[0]],
        [root.children[0], root.children[0].children[0]],
        [root.children[0].children[0]],
        [root, root.children[0], root.children[0].children[1]],
        [root.children[0], root.children[0].children[1]],
        [root.children[0].children[1]],
    ]
    assert sorted(query.apply(gf)) == sorted(matches)

    query = QueryMatcher([{"node_id": 0}])
    assert query.apply(gf) == [[gf.graph.roots[0]]]

    with pytest.raises(InvalidQueryFilter):
        query = QueryMatcher([{"node_id": "hello"}])
        query.apply(gf)


def test_high_level_depth_index_levels(calc_pi_hpct_db):
    gf = GraphFrame.from_hpctoolkit(str(calc_pi_hpct_db))
    root = gf.graph.roots[0]

    query = QueryMatcher([("*", {"depth": "<= 2"})])
    matches = [
        [root, root.children[0], root.children[0].children[0]],
        [root.children[0], root.children[0].children[0]],
        [root.children[0].children[0]],
        [root, root.children[0], root.children[0].children[1]],
        [root.children[0], root.children[0].children[1]],
        [root.children[0].children[1]],
    ]
    assert sorted(query.apply(gf)) == sorted(matches)

    query = QueryMatcher([("*", {"depth": 0})])
    matches = [[root]]
    assert query.apply(gf) == matches

    with pytest.raises(InvalidQueryFilter):
        query = QueryMatcher([{"depth": "hello"}])
        query.apply(gf)


def test_high_level_node_id_index_levels(calc_pi_hpct_db):
    gf = GraphFrame.from_hpctoolkit(str(calc_pi_hpct_db))
    root = gf.graph.roots[0]

    query = QueryMatcher([("*", {"node_id": "<= 2"})])
    matches = [
        [root, root.children[0]],
        [root.children[0]],
        [root, root.children[0], root.children[0].children[0]],
        [root.children[0], root.children[0].children[0]],
        [root.children[0].children[0]],
    ]
    assert sorted(query.apply(gf)) == sorted(matches)

    query = QueryMatcher([("*", {"node_id": 0})])
    matches = [[root]]
    assert query.apply(gf) == matches

    with pytest.raises(InvalidQueryFilter):
        query = QueryMatcher([{"node_id": "hello"}])
        query.apply(gf)
