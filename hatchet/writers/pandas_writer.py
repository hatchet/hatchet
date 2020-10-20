# Copyright 2017-2020 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from hatchet.node import Node

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


def _fill_children_and_parents(df):
    dump_df = df.copy()
    dump_df["children"] = [[] for _ in range(len(dump_df))]
    dump_df["parents"] = [[] for _ in range(len(dump_df))]
    for i in range(len(dump_df)):
        node = _get_node_from_df_iloc(dump_df, i)
        dump_df.iat[i, dump_df.columns.get_loc("children")] = [
            c._hatchet_nid for c in node.children
        ]
        dump_df.iat[i, dump_df.columns.get_loc("parents")] = [
            p._hatchet_nid for p in node.parents
        ]
    return dump_df


class PandasWriter(ABC):
    def __init__(self, filename):
        self.fname = filename

    @abstractmethod
    def _write_to_file_type(self, df, **kwargs):
        pass

    def write(self, gf, **kwargs):
        gf_cpy = gf.deepcopy()
        dump_df = _fill_children_and_parents(gf_cpy.dataframe)
        for i in range(len(dump_df)):
            node = _get_node_from_df_iloc(dump_df, i)
            if len(node.children) != 0:
                node.children = []
            if len(node.parents) != 0:
                node.parents = []
        self._write_to_file_type(dump_df, **kwargs)
