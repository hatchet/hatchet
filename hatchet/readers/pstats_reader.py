import pstats
import pandas as pd


import hatchet.graphframe
from ..node import Node
from ..graph import Graph
from ..frame import Frame


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


class PstatsReader:
    def __init__(self, filename):
        self.pstats_file = filename

        self.name_to_hnode = {}
        self.name_to_dict = {}

        # variables for DFS cycle pruning algorithm
        self.id = 0
        self.visited = []
        self.stack = []

    def _prune_cycles(self, node):
        """Performs a depth first search and removes back edges when found"""
        self.visited.append(node)
        self.stack.append(node)

        pruned_list = []
        cycle_flag = False

        for child in node.children:
            if child not in self.visited:
                self._prune_cycles(child)
            elif child in self.stack:
                cycle_flag = True

            # Needed to load children in the case of an already
            # visited but valid node.
            if not cycle_flag:
                pruned_list.append(child)
                cycle_flag = False

        node.children = pruned_list

        self.stack.pop(-1)
        return False

    def _get_src(self, stat):
        """Gets the source/parent of our current desitnation node"""
        return stat[StatData.SRCNODE]

    def _add_node_metadata(self, stat_name, stat_module_data, stats, hnode):
        """Puts all the metadata associated with a node in a dictionary to insert into pandas."""
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
        print(pstats.__file__)
        stats_dict = pstats.Stats(self.pstats_file).__dict__["stats"]

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
                dst_hnode = Node(
                    Frame({"type": "function", "name": dst_name}), None, hnid=self.id
                )
                self.name_to_hnode[dst_name] = dst_hnode
                self._add_node_metadata(dst_name, dst_module_data, dst_stats, dst_hnode)
                self.id += 1

            # get all parents of our current destination node
            # create source nodes and link with destination node
            srcs = self._get_src(dst_stats)
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
                            Frame({"type": "function", "name": src_name}),
                            None,
                            hnid=self.id,
                        )
                        self.name_to_hnode[src_name] = src_hnode

                        # lookup stat data for source here
                        src_stats = stats_dict[src_module_data]
                        self._add_node_metadata(
                            src_name, src_module_data, src_stats, src_hnode
                        )
                        self.id += 1

                if src_name is not None:
                    dst_hnode.add_parent(src_hnode)
                    src_hnode.add_child(dst_hnode)

        list_roots = []
        for (key, val) in self.name_to_hnode.items():
            if not val.parents:
                list_roots.append(val)

        # Removes back edges from graph to remove
        # cycles and fix infinite loops problems with output
        for i in range(len(list_roots)):
            self._prune_cycles(list_roots[i])

        return list_roots

    def read(self):
        roots = self.create_graph()
        graph = Graph(roots)

        dataframe = pd.DataFrame.from_dict(data=list(self.name_to_dict.values()))
        index = ["node"]
        dataframe.set_index(index, inplace=True)
        dataframe.sort_index(inplace=True)

        return hatchet.graphframe.GraphFrame(graph, dataframe, ["time"], ["time (inc)"])
