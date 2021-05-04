# Copyright 2017-2020 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import hatchet.graphframe
from hatchet.node import Node
from hatchet.graph import Graph

from abc import abstractmethod

# TODO The ABC class was introduced in Python 3.4.
# When support for earlier versions is (eventually) dropped,
# this entire "try-except" block can be reduced to:
# from abc import ABC
try:
    from abc import ABC
except ImportError:
    from abc import ABCMeta

    ABC = ABCMeta("ABC", (object,), {"__slots__": ()})


def _get_node_from_df_iloc(df, ind):
    node = None
    if isinstance(df.iloc[ind].name, tuple):
        node = df.iloc[ind].name[0]
    elif isinstance(df.iloc[ind].name, Node):
        node = df.iloc[ind].name
    else:
        # TODO Custom Error
        raise RuntimeError
    return node


def _get_parents_and_children(df):
    rel_dict = {}
    for i in range(len(df)):
        node = _get_node_from_df_iloc(df, i)
        if node not in rel_dict:
            rel_dict[node] = {}
            rel_dict[node]["parents"] = df.iloc[i].loc["parents"]
            rel_dict[node]["children"] = df.iloc[i].loc["children"]
        else:
            if sorted(rel_dict[node]["parents"]) != sorted(df.iloc[i].loc["parents"]):
                # TODO Custom Error
                raise RuntimeError
            if sorted(rel_dict[node]["children"]) != sorted(df.iloc[i].loc["children"]):
                # TODO Custom Error
                raise RuntimeError
    return rel_dict


def _reconstruct_graph(df, rel_dict):
    node_list = sorted(set(list(df.index.copy().to_frame()["node"])))
    for i in range(len(df)):
        node = _get_node_from_df_iloc(df, i)
        if len(node.children) == 0:
            node.children = [node_list[nid] for nid in rel_dict[node]["children"]]
        if len(node.parents) == 0:
            node.parents = [node_list[nid] for nid in rel_dict[node]["parents"]]
    node_list = sorted(set(list(df.index.copy().to_frame()["node"])))
    roots = [node for node in node_list if len(node.parents) == 0]
    return Graph(roots)


class PandasReader(ABC):
    """Abstract Base Class for reading in checkpointing files."""

    def __init__(self, filename):
        self.fname = filename

    @abstractmethod
    def _read_from_file_type(self, **kwargs):
        pass

    def read(self, **kwargs):
        df = self._read_from_file_type(**kwargs)
        rel_dict = _get_parents_and_children(df)
        graph = _reconstruct_graph(df, rel_dict)
        graph.normalize()
        df.drop(columns=["children", "parents"], inplace=True)
        return hatchet.graphframe.GraphFrame(graph, df)
