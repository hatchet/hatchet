# Copyright 2021 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from numpy import string_
import pandas as pd

import hatchet.graphframe
from hatchet.node import Node
from hatchet.graph import Graph
from hatchet.frame import Frame
from hatchet.util.timer import Timer


def _find_child_node(node, name):
    for c in node.children:
        if c.frame.get("name") == name:
            return c
    return None


class SpotDatasetReader:
    """ Reads a (single-run) dataset from SpotDB
    """

    def __init__(self, regionprofile, metadata, attr_info):
        """ Read SpotDB dataset
        """

        self.regionprofile = regionprofile
        self.attr_info = attr_info
        self.metadata = metadata
        self.df_data = []
        self.roots = {}
        self.metric_columns = set()

        self.timer = Timer()


    def create_graph(self):
        self.df_data.clear()

        for pathstr, vals in self.regionprofile.items():
            # parse { "a/b/c": { "metric": val, ... }, ... } records
            if len(pathstr) == 0:
                continue

            path = pathstr.split("/")
            name = path[-1]
            node = self._create_node(path)

            metrics = {}
            for k, v in vals.items():
                info = self.attr_info.get(k, dict())
                clmn = info.get("alias", k)
                type = info.get("type", "string")
                if "inclusive" in k:
                    clmn += " (inc)"

                if type == "double":
                    metrics[clmn] = float(v)
                elif type == "int" or type == "uint":
                    metrics[clmn] = int(v)
                else:
                    metrics[clmn] = v
                self.metric_columns.add(clmn)

            self.df_data.append(dict({ "name": name, "node": node }, **metrics))


    def read(self, default_metric="Total time (inc)"):
        with self.timer.phase("graph construction"):
            self.create_graph()

        graph = Graph(list(self.roots.values()))
        graph.enumerate_traverse()

        dataframe = pd.DataFrame(data=self.df_data)
        dataframe.set_index(["node"], inplace=True)

        exc_metrics = []
        inc_metrics = []
        for m in self.metric_columns:
            if "(inc)" in m:
                inc_metrics.append(m)
            else:
                exc_metrics.append(m)

        return hatchet.graphframe.GraphFrame(
            graph, dataframe, exc_metrics, inc_metrics, metadata=self.metadata,
            default_metric=default_metric
        )


    def _create_node(self, path):
        parent = self.roots.get(path[0], None)
        if parent is None:
            parent = Node(Frame(name=path[0]))
            self.roots[path[0]] = parent

        node = parent
        for name in path[1:]:
            node = _find_child_node(parent, name)
            if node is None:
                node = Node(Frame(name=name), parent)
                parent.add_child(node)
            parent = node

        return node


class SpotDBReader:
    """ Import multiple runs as graph frames from a SpotDB instance
    """

    def __init__(self, db_key, list_of_ids=None, default_metric="Total time (inc)"):
        self.db_key = db_key
        self.list_of_ids = list_of_ids
        self.default_metric = default_metric

    def read(self):
        import spotdb

        if isinstance(self.db_key, str):
            db = spotdb.connect(self.db_key)
        else:
            db = self.db_key

        runs = self.list_of_ids if self.list_of_ids is not None else db.get_all_run_ids()

        regionprofiles = db.get_regionprofiles(runs)
        metadata = db.get_global_data(runs)
        attr_info = db.get_metric_attribute_metadata()

        result = []

        for run in runs:
            if run in regionprofiles:
                result.append(SpotDatasetReader(regionprofiles[run], metadata[run], attr_info).read(self.default_metric))

        return result
