# Copyright 2017-2020 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import pstats
import sys
import pandas as pd


import hatchet.graphframe
from hatchet.node import Node
from hatchet.graph import Graph
from hatchet.frame import Frame


def print_incomptable_msg(stats_file):
    """
    Function which makes the syntax cleaner in Profiler.write_to_file().
    """
    errmsg = """\n Error: Incompatible pstats file ({})\n Please run your code in Python {} to read in this file. \n"""
    if sys.version_info[0] == 2:
        print(errmsg.format(stats_file, 3))
    if sys.version_info[0] == 3:
        print(errmsg.format(stats_file, 2.7))


class StatData:
    """ Faux Enum for python """

    NUMCALLS = 0
    NATIVECALLS = 1
    EXCTIME = 2
    INCTIME = 3
    SRCNODE = 4


class NameData:
    """ Faux Enum for python """

    FILE = 0
    LINE = 1
    FNCNAME = 2


class CProfileReader:
    def __init__(self, filename):
        self.pstats_file = filename

        self.name_to_hnode = {}
        self.name_to_dict = {}

    def _get_src(self, stat):
        """Gets the source/parent of our current destination node"""
        return stat[StatData.SRCNODE]

    def _add_node_metadata(self, stat_name, stat_module_data, stats, hnode):
        """Puts all the metadata associated with a node in a dictionary to insert
        into pandas.
        """
        node_dict = {
            "file": stat_module_data[NameData.FILE],
            "line": stat_module_data[NameData.LINE],
            "name": stat_module_data[NameData.FNCNAME],
            "numcalls": stats[StatData.NUMCALLS],
            "nativecalls": stats[StatData.NATIVECALLS],
            "time (inc)": stats[StatData.INCTIME],
            "time": stats[StatData.EXCTIME],
            "node": hnode,
        }
        self.name_to_dict[stat_name] = node_dict

    def create_graph(self):
        """Performs the creation of our node graph"""
        try:
            stats_dict = pstats.Stats(self.pstats_file).__dict__["stats"]
        except ValueError:
            print_incomptable_msg(self.pstats_file)
            raise
        list_roots = []

        # We iterate through each function/node in our stats dict
        for dst_module_data, dst_stats in stats_dict.items():
            dst_name = dst_module_data[NameData.FNCNAME]

            # need unique name for a particular node
            dst_name = "{}:{}:{}".format(
                dst_name,
                dst_module_data[NameData.FILE].split("/")[-1],
                dst_module_data[NameData.LINE],
            )
            dst_hnode = self.name_to_hnode.get(dst_name)
            if not dst_hnode:
                # create a node if it doesn't exist yet
                dst_hnode = Node(Frame({"type": "function", "name": dst_name}), None)
                self.name_to_hnode[dst_name] = dst_hnode
                self._add_node_metadata(dst_name, dst_module_data, dst_stats, dst_hnode)

            # get all parents of our current destination node
            # create source nodes and link with destination node
            srcs = self._get_src(dst_stats)
            if srcs == {}:
                list_roots.append(dst_hnode)
            else:
                for src_module_data in srcs.keys():
                    src_name = src_module_data[NameData.FNCNAME]

                    if src_name is not None:
                        src_name = "{}:{}:{}".format(
                            src_name,
                            src_module_data[NameData.FILE].split("/")[-1],
                            src_module_data[NameData.LINE],
                        )
                        src_hnode = self.name_to_hnode.get(src_name)

                        if not src_hnode:
                            # create a node if it doesn't exist yet
                            src_hnode = Node(
                                Frame({"type": "function", "name": src_name}), None
                            )
                            self.name_to_hnode[src_name] = src_hnode

                            # lookup stat data for source here
                            src_stats = stats_dict[src_module_data]
                            self._add_node_metadata(
                                src_name, src_module_data, src_stats, src_hnode
                            )
                        dst_hnode.add_parent(src_hnode)
                        src_hnode.add_child(dst_hnode)

        return list_roots

    def read(self):
        roots = self.create_graph()
        graph = Graph(roots)
        graph.enumerate_traverse()

        dataframe = pd.DataFrame.from_dict(data=list(self.name_to_dict.values()))
        index = ["node"]
        dataframe.set_index(index, inplace=True)
        dataframe.sort_index(inplace=True)

        return hatchet.graphframe.GraphFrame(graph, dataframe, ["time"], ["time (inc)"])
