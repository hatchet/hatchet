# Copyright 2020 The Regents of the University of California, through Lawrence
# Berkeley National Laboratory, and other Hatchet Project Developers. See the
# top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import json
import pandas as pd

from hatchet.graphframe import GraphFrame
from ..node import Node
from ..graph import Graph
from ..frame import Frame
from ..util.timer import Timer


class TimemoryReader:
    """Read in timemory JSON output"""

    def __init__(self, input, select=None):
        if isinstance(input, dict):
            self.graph_dict = input
        elif isinstance(input, str) and input.endswith("json"):
            with open(input) as f:
                self.graph_dict = json.load(f)
        elif not isinstance(input, str):
            self.graph_dict = json.loads(input.read())
        else:
            raise TypeError("input must be dict, json file, or string")
        self.name_to_hnode = {}
        self.name_to_dict = {}
        self.timer = Timer()
        self.metric_cols = []
        self.properties = {}
        self.include_tid = False
        self.include_nid = False
        if select is None:
            self.select = select
        elif isinstance(select, list):

            if select:

                def _get_select(val):
                    if isinstance(val, str):
                        return val.lower()
                    elif callable(val):
                        return val().lower()
                    raise TypeError(
                        "Items in select must be string or callable: {}".format(
                            type(val).__name__
                        )
                    )

                self.select = [_get_select(v) for v in select]
        else:
            raise TypeError("select must be None or list of string")

    def create_graph(self):
        """Create graph and dataframe"""

        list_roots = []
        node_dicts = []
        graph_dict = self.graph_dict

        def remove_keys(_dict, _keys):
            """Remove keys from dictionary"""
            if isinstance(_keys, str):
                if _keys in _dict:
                    del _dict[_keys]
            else:
                for _key in _keys:
                    _dict = remove_keys(_dict, _key)
            return _dict

        def patch_keys(_dict, _extra):
            """Add a suffix to dictionary keys"""
            _tmp = {}
            for key, itr in _dict.items():
                _tmp["{}{}".format(key, _extra)] = itr
            return _tmp

        def add_metrics(_dict):
            """Add any keys to metric_cols which don't already exist"""
            for key, itr in _dict.items():
                if key not in self.metric_cols:
                    self.metric_cols.append(key)

        def process_regex(_data):
            """Process the regex data for func/file/line info"""
            _tmp = {}
            if _data is not None and len(_data.groups()) > 0:
                for _key in ("head", "func", "file", "line", "tail"):
                    try:
                        _val = _data.group(_key)
                        if _val:
                            _tmp[_key] = _val
                    except Exception:
                        pass
            return _tmp if _tmp else None

        def perform_regex(_itr):
            """Performs a search for standard configurations of function + file + line"""
            import re

            _tmp = None
            for _pattern in [
                r"(?P<head>.+)([ \t]+)\[(?P<func>\S+)([/])(?P<file>\S+):(?P<line>[0-9]+)\]$",
                r"(?P<func>\S+)([@/])(?P<file>\S+):(?P<line>[0-9]+)[/]*(?P<tail>.*)",
                r"(?P<func>\S+)([@/])(?P<file>\S+)([/])(?P<tail>.*)",
                r"(?P<func>\S+):(?P<line>[0-9]+)([/]*)(?P<tail>.*)",
            ]:
                _tmp = process_regex(re.search(_pattern, _itr))
                if _tmp:
                    break
            return _tmp if _tmp else None

        def get_keys(_prefix):
            """Get the standard set of dictionary entries.
            Also, parses the prefix for func-file-line info
            which is typically in the form:
                <FUNC>@<FILE>:<LINE>/...
                <FUNC>/<FILE>:<LINE>/...
                <SOURCE>    [<FUNC>/<FILE>:<LINE>]
            """
            _keys = {
                "type": "region",
                "name": _prefix,
            }
            _extra = {"file": "<unknown>", "line": "0"}
            _pdict = perform_regex(_prefix)
            if _pdict is not None:
                if "head" in _pdict:
                    _keys["name"] = _pdict["head"].rstrip()
                    _extra["line"] = _pdict["line"]
                    _extra["file"] = _pdict["file"]
                else:
                    _keys["name"] = _pdict["func"]
                    _extra["file"] = (
                        _pdict["file"] if "file" in _pdict else "<unknown file>"
                    )
                    if "line" in _pdict:
                        _extra["line"] = _pdict["line"]
                    if "tail" in _pdict:
                        _keys["name"] = "{}/{}".format(_keys["name"], _pdict["tail"])
            return (_keys, _extra)

        def get_md_suffix(_obj):
            """Gets a multi-dimensional suffix"""
            _ret = []
            if isinstance(_obj, str):
                _ret = [_obj]
            elif isinstance(_obj, dict):
                for _key, _item in _obj.items():
                    _ret.append(_key.strip().replace(" ", "-").replace("_", "-"))
            elif isinstance(_obj, list) or isinstance(_obj, tuple):
                for _item in _obj:
                    _ret.append(_item.strip().replace(" ", "-").replace("_", "-"))
            return _ret

        def get_md_entries(_obj, _suffix):
            """Gets a multi-dimensional entries"""
            _ret = {}
            for _key, _item in _obj.items():
                for i, (k, v) in enumerate(_item.items()):
                    _ret["{}.{}".format(_key, _suffix[i])] = v
            return _ret

        def parse_node(_key, _dict, _hparent, _rank):
            """Create node_dict for one node and then call the function
            recursively on all children.
            """

            # If the hash is zero, that indicates that the node
            # is a dummy for the root or is used for synchronizing data
            # between multiple threads
            if _dict["node"]["hash"] == 0:
                if "children" in _dict:
                    for _child in _dict["children"]:
                        parse_node(_key, _child, _hparent, _rank)
                return

            _prop = self.properties[_key]
            _keys, _extra = get_keys(_dict["node"]["prefix"])
            if _rank is not None:
                _keys["nid"] = _rank
                self.include_nid = True
            _extra["count"] = _dict["node"]["inclusive"]["entry"]["laps"]
            _extra["tid"] = _dict["node"]["tid"]
            _extra["pid"] = _dict["node"]["pid"]
            # aggregated results have a list of threads and processes
            if len(_extra["tid"]) == 1:
                _keys["tid"] = _extra["tid"][0]
                del _extra["tid"]
                self.include_tid = True
            if len(_extra["pid"]) == 1:
                _extra["pid"] = _extra["pid"][0]
            _labels = None if "type" not in _prop else _prop["type"]
            # if the data is multi-dimensional
            _md = True if not isinstance(_labels, str) else False

            _hnode = Node(Frame(_keys), _hparent)

            _remove = ["cereal_class_version", "count"]
            _inc_stats = remove_keys(_dict["node"]["inclusive"]["stats"], _remove)
            _exc_stats = remove_keys(_dict["node"]["exclusive"]["stats"], _remove)

            if _md:
                _suffix = get_md_suffix(_labels)
                _exc_stats = get_md_entries(_exc_stats, _suffix)
                _inc_stats = get_md_entries(_inc_stats, _suffix)

            _inc_stats = patch_keys(_inc_stats, ".inc")
            _exc_stats = patch_keys(_exc_stats, "")

            add_metrics(_extra)
            add_metrics(_exc_stats)
            add_metrics(_inc_stats)

            node_dicts.append(
                dict({"node": _hnode, **_keys}, **_extra, **_exc_stats, **_inc_stats)
            )

            if _hparent is None:
                list_roots.append(_hnode)
            else:
                _hparent.add_child(_hnode)

            if "children" in _dict:
                for _child in _dict["children"]:
                    parse_node(_key, _child, _hnode, _rank)

        def eval_graph(_key, _dict, _rank):
            """Evaluate the entry and determine if it has relevant data.
            If the hash is zero, that indicates that the node
            is a dummy for the root or is used for synchronizing data
            between multiple threads
            """
            _nchild = len(_dict["children"])
            if _nchild == 0:
                print("Skipping {}...".format(_key))
                return
            if _rank is not None:
                print("Adding {} for rank {}...".format(_key, _rank))
            else:
                print("Adding {}...".format(_key))

            if _dict["node"]["hash"] > 0:
                parse_node(_key, _dict, None, _rank)
            elif "children" in _dict:
                # call for all children
                for child in _dict["children"]:
                    parse_node(_key, child, None, _rank)

        def read_graph(_key, _itr, _offset):
            """The layout of the graph at this stage
            is subject to slightly different structures
            based on whether distributed memory parallelism (DMP)
            (e.g. MPI, UPC++) was supported and active
            """
            for i in range(len(_itr)):
                _dict = _itr[i]
                _idx = None if _offset is None else i + _offset
                if isinstance(_dict, list):
                    for j in range(len(_dict)):
                        eval_graph(_key, _dict[j], _idx)
                else:
                    eval_graph(_key, _dict, _idx)

        def read_properties(_dict, _key, _itr):
            """Read in the properties for a component. This
            contains information on the type of the component,
            a description, a unit_value relative to the
            standard, a unit label, whether the data is
            only relevant per-thread, the number of MPI and/or
            UPC++ ranks (some results can theoretically use
            both UPC++ and MPI), the number of threads in
            the application, and the total number of processes
            """
            if _key not in _dict:
                _dict[_key] = {}
            try:
                _dict[_key]["properties"] = remove_keys(
                    itr["properties"], "cereal_class_version"
                )
            except KeyError:
                pass
            for k in (
                "type",
                "description",
                "unit_value",
                "unit_repr",
                "thread_scope_only",
                "mpi_size",
                "upcxx_size",
                "thread_count",
                "process_count",
            ):
                if k not in _dict[_key] or _dict[_key][k] is None:
                    if k in itr:
                        _dict[_key][k] = itr[k]
                    else:
                        _dict[_key][k] = None

        for key, itr in graph_dict["timemory"].items():
            # strip out the namespace if provided
            key = key.replace("tim::", "").replace("component::", "").lower()
            # check for selection
            if self.select is not None and key not in self.select:
                continue
            # read in properties
            read_properties(self.properties, key, itr)
            # if no DMP supported
            if "graph" in itr:
                print("Reading graph...")
                read_graph(key, itr["graph"], None)
            else:
                # read in MPI results
                if "mpi" in itr:
                    print("Reading MPI...")
                    read_graph(key, itr["mpi"], 0)
                # if MPI and UPC++, report ranks
                # offset by MPI_Comm_size
                _offset = self.properties[key]["mpi_size"]
                _offset = 0 if _offset is None else int(_offset)
                if "upc" in itr:
                    print("Reading UPC...")
                    read_graph(key, itr["upc"], _offset)
                elif "upcxx" in itr:
                    print("Reading UPC++...")
                    read_graph(key, itr["upcxx"], _offset)

        # find any columns where the entries are None or "null"
        non_null = {}
        for itr in node_dicts:
            for key, item in itr.items():
                if key not in non_null:
                    non_null[key] = False
                if item is not None:
                    if not isinstance(item, str):
                        non_null[key] = True
                    elif isinstance(item, str) and item != "null":
                        non_null[key] = True

        # find any columns where the entries are all "null"
        for itr in node_dicts:
            for key, item in non_null.items():
                if not item:
                    del itr[key]

        # create the graph of the roots
        graph = Graph(list_roots)
        graph.enumerate_traverse()

        # separate out the inclusive vs. exclusive columns
        exc_metrics = []
        inc_metrics = []
        for column in self.metric_cols:
            if column.endswith(".inc"):
                inc_metrics.append(column)
            else:
                exc_metrics.append(column)

        indices = ["node"]
        # this attempt at MultiIndex does not work
        # if self.include_nid:
        #    indices.append("nid")
        # if self.include_tid:
        #    indices.append("tid")
        dataframe = pd.DataFrame(data=node_dicts)
        dataframe.set_index(indices, inplace=True)
        dataframe.sort_index(inplace=True)

        return GraphFrame(graph, dataframe, exc_metrics, inc_metrics)

    def read(self):
        """Read timemory json."""
        return self.create_graph()
