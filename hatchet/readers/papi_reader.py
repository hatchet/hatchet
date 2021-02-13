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

        ####### sample graphframe
        # Example with two threads
        #
        #   #pragma omp parallel
        #     begin do_work
        #         read do_work
        #         read do_work
        #     end do_work
        #
        # Output:
        # Rank=0, Thread=0 do_work
        # Rank=0, Thread=0   do_work(r1)
        # Rank=0, Thread=0   do_work(r2)
        # Rank=0, Thread=1 do_work
        # Rank=0, Thread=1   do_work(r1)
        # Rank=0, Thread=1   do_work(r2)


        #              do_work
        #              /     \
        #      do_work(r1)  do_work(r2)


        metrics= {
          "cycles": 2025033750,
          "real_time_nsec": 1015090454,
          "perf::TASK-CLOCK": 14980591,
          "PAPI_TOT_INS": 31869696,
          "PAPI_TOT_CYC": 29027697,
          "PAPI_FP_INS": 0,
          "PAPI_FP_OPS": 54
        }

        node_name = ["do_work"]
        node_name_read = ["do_work(r1)", "do_work(r2)"]

        # root node
        frame = Frame({"type": "region", "name": node_name[0]})
        graph_root = Node(frame, None)

        node_dict = dict(
          { "name": node_name[0],"node": graph_root,
            "rank": 0,
            "thread": 0,
            **metrics,
          }
        )
        node_dicts.append(node_dict)
        node_dict = dict(
          { "name": node_name[0],"node": graph_root,
            "rank": 0,
            "thread": 1,
            **metrics,
          }
        )
        node_dicts.append(node_dict)

        counter = 0
        for name in node_name_read:
          frame = Frame({"type": "region", "name": name})
          node = Node(frame, None)
          
          node_dict = dict(
            { "name": name,"node": node,
              "rank": 0,
              "thread": 0,
              **metrics,
            }
          )
          node_dicts.append(node_dict)
          if counter < 1:
            node_dict = dict(
              { "name": name,"node": node,
                "rank": 0,
                "thread": 1,
                **metrics,
              }
            )
            node_dicts.append(node_dict)
          graph_root.add_child(node)
          counter = counter + 1



        list_roots.append(graph_root)
        graph = Graph(list_roots)
        graph.enumerate_traverse()

        exc_metrics = []
        inc_metrics = [
          'cycles',
          'real_time_nsec',
          'perf::TASK-CLOCK',
          'PAPI_TOT_INS',
          'PAPI_TOT_CYC',
          'PAPI_FP_INS',
          'PAPI_FP_OPS'
        ]

        dataframe = pd.DataFrame(data=node_dicts)
        #dataframe.set_index(["node"], inplace=True)
        dataframe.set_index(["node", "rank", "thread"], inplace=True)
        dataframe.sort_index(inplace=True)

        return hatchet.graphframe.GraphFrame(graph, dataframe, exc_metrics, inc_metrics)
