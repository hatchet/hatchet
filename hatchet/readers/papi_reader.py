# Copyright 2017-2021 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import pandas as pd

import hatchet.graphframe
from hatchet.node import Node
from hatchet.graph import Graph
from hatchet.frame import Frame


class PAPIReader:
    def __init__(self, graph_dict):
        """Read from list of dictionaries.

        graph_dict (dict): List of dictionaries encoding nodes.
        """
        self.graph_dict = graph_dict

    def read(self):

        list_roots = []
        node_dicts = []

####### call tree
        # node_name = "do_work"
        # frame = Frame({"type": "region", "name": node_name})
        # graph_root = Node(frame, None)
        # node_dict = dict(
        #   {"node": graph_root, "name": node_name,
        #   'rank': 0,
        #      'thread': 0,
        #      'region_count': 1,
        #      "cycles": 2025033750,
        #      "real_time_nsec": 1015090454,
        #      "perf::TASK-CLOCK": 14980591,
        #      "PAPI_TOT_INS": 31869696,
        #      "PAPI_TOT_CYC": 29027697,
        #      "PAPI_FP_INS": 0,
        #      "PAPI_FP_OPS": 54}
        # )
        # node_dicts.append(node_dict)

        # node_name = "do_work(read)"
        # frame1 = Frame({"type": "region", "name": node_name})
        # child_root = Node(frame1, graph_root)
        # node_dict = dict(
        #   {"node": child_root, "name": node_name,
        #   'rank': 0,
        #      'thread': 0,
        #      'region_count': 1,
        #      "cycles": 2025033750,
        #      "real_time_nsec": 1015090454,
        #      "perf::TASK-CLOCK": 14980591,
        #      "PAPI_TOT_INS": 31869696,
        #      "PAPI_TOT_CYC": 29027697,
        #      "PAPI_FP_INS": 0,
        #      "PAPI_FP_OPS": 54}
        # )
        # node_dicts.append(node_dict)
        # graph_root.add_child(child_root)
        # list_roots.append(graph_root)


        # node_name = "do_work"
        # frame2 = Frame({"type": "region", "name": node_name })
        # graph_root2 = Node(frame2, None)
        # node_dict = dict(
        #   {"node": graph_root2, "name": node_name,
        #   'rank': 0,
        #      'thread': 1,
        #      'region_count': 1,
        #      "cycles": 2025736622,
        #      "real_time_nsec": 1015445611,
        #      "perf::TASK-CLOCK": 15279270,
        #      "PAPI_TOT_INS": 31873731,
        #      "PAPI_TOT_CYC": 28806889,
        #      "PAPI_FP_INS": 0,
        #      "PAPI_FP_OPS": 98}
        # )
        # node_dicts.append(node_dict)
        # list_roots.append(graph_root2)

        # node_name = "do_work"
        # frame3 = Frame({"type": "region", "name": node_name })
        # graph_root3 = Node(frame3, None)
        # node_dict = dict(
        #   {"node": graph_root3, "name": node_name,
        #   'rank': 1,
        #      'thread': 0,
        #      'region_count': 1,
        #      "cycles": 2030360894,
        #      "real_time_nsec": 1017576862,
        #      "perf::TASK-CLOCK": 17452816,
        #      "PAPI_TOT_INS": 31902057,
        #      "PAPI_TOT_CYC": 30709312,
        #      "PAPI_FP_INS": 0,
        #      "PAPI_FP_OPS": 149}
        # )
        # node_dicts.append(node_dict)
        # list_roots.append(graph_root3)

        # node_name = "do_work"
        # frame4 = Frame({"type": "region", "name": node_name })
        # graph_root4 = Node(frame4, None)
        # node_dict = dict(
        #   {"node": graph_root4, "name": node_name,
        #   'rank': 1,
        #      'thread': 1,
        #      'region_count': 1,
        #      "cycles": 2030360933,
        #      "real_time_nsec": 1017570681,
        #      "perf::TASK-CLOCK": 17515841,
        #      "PAPI_TOT_INS": 32087423,
        #      "PAPI_TOT_CYC": 30683338,
        #      "PAPI_FP_INS": 0,
        #      "PAPI_FP_OPS": 25}
        # )
        # node_dicts.append(node_dict)
        # list_roots.append(graph_root4)
#######        

####### system tree including instrumented regions
        process_metrics = {
          "region_count": '',
          "cycles": '',
          "real_time_nsec": '',
          "perf::TASK-CLOCK": None,
          "PAPI_TOT_INS": '',
          "PAPI_TOT_CYC": '',
          "PAPI_FP_INS": '',
          "PAPI_FP_OPS": ''
        }

        node_name = "MPI Rank 0"
        frame = Frame({"type": "rank", "name": node_name})
        graph_root = Node(frame, None)
        node_dict = dict(
          {"node": graph_root, "name": node_name, **process_metrics}
        )
        node_dicts.append(node_dict)

        node_name = "CPU thread 0"
        frame = Frame({"type": "thread", "name": node_name})
        graph_root1 = Node(frame, graph_root)
        node_dict = dict(
          {"node": graph_root1, "name": node_name, **process_metrics}
        )
        node_dicts.append(node_dict)
        graph_root.add_child(graph_root1)

        node_name = "do_work"
        frame = Frame({"type": "region", "name": node_name})
        graph_root2 = Node(frame, graph_root1)
        node_dict = dict(
          {"node": graph_root2, "name": node_name,
             "region_count": 1,
             "cycles": 2025033750,
             "real_time_nsec": 1015090454,
             "perf::TASK-CLOCK": 14980591,
             "PAPI_TOT_INS": 31869696,
             "PAPI_TOT_CYC": 29027697,
             "PAPI_FP_INS": 0,
             "PAPI_FP_OPS": 54}
        )
        node_dicts.append(node_dict)
        graph_root1.add_child(graph_root2)

        node_name = "CPU thread 1"
        frame = Frame({"type": "thread", "name": node_name})
        graph_root3 = Node(frame, graph_root)
        node_dict = dict(
          {"node": graph_root3, "name": node_name, **process_metrics}
        )
        node_dicts.append(node_dict)
        graph_root.add_child(graph_root3)

        node_name = "do_work"
        frame = Frame({"type": "region", "name": node_name})
        graph_root4 = Node(frame, graph_root3)
        node_dict = dict(
          {"node": graph_root4, "name": node_name,
             "region_count": 1,
             "cycles": 2025033750,
             "real_time_nsec": 1015090454,
             "perf::TASK-CLOCK": 14980591,
             "PAPI_TOT_INS": 31869696,
             "PAPI_TOT_CYC": 29027697,
             "PAPI_FP_INS": 0,
             "PAPI_FP_OPS": 54}
        )
        node_dicts.append(node_dict)
        graph_root3.add_child(graph_root4)

        list_roots.append(graph_root)

#######


        #print("list_roots ", list_roots)
        #print("node_dicts ", node_dicts)

        graph = Graph(list_roots)
        graph.enumerate_traverse()

        inc_metrics = [
          'region_count',
          'cycles',
          'real_time_nsec',
          'perf::TASK-CLOCK',
          'PAPI_TOT_INS',
          'PAPI_TOT_CYC',
          'PAPI_FP_INS',
          'PAPI_FP_OPS'
        ]

        exc_metrics = []

        dataframe = pd.DataFrame(data=node_dicts)
        dataframe.columns = dataframe.columns.str.strip()

        # print(dataframe)

        #print(dataframe.columns.tolist())
        # print("\n\n")

        #return hatchet.graphframe.GraphFrame(graph, dataframe, exc_metrics, inc_metrics)

        dataframe.set_index(["node"], inplace=True)
        #dataframe.set_index(["node", "rank", "thread"], inplace=True)
        print(dataframe)
        gf = hatchet.graphframe.GraphFrame(graph, dataframe, exc_metrics, inc_metrics)
        #print(gf.tree(metric_column="perf::TASK-CLOCK", context_column="region_count", rank=1, thread=1))
        print(gf.tree(metric_column="perf::TASK-CLOCK", context_column="region_count"))
