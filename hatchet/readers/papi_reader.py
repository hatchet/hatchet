# Copyright 2017-2021 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import pandas as pd

from collections import OrderedDict
import argparse
import os
import sys
import json
# Make it work for Python 2+3 and with Unicode
import io
try:
  to_unicode = unicode
except NameError:
  to_unicode = str

import hatchet.graphframe
from hatchet.node import Node
from hatchet.graph import Graph
from hatchet.frame import Frame


class PAPIReader:
    def __init__(self, file_path):
        # this is the name of the PAPI performance report directory. The directory
        # contains json files per MPI rank.

        self.inc_metrics = []
        self.dict = {}

        json_dict = {}
        json_rank = OrderedDict()

        #check whether the file path is a file or a directory
        if os.path.isdir(file_path):

          #get measurement files
          file_list = os.listdir(file_path)
          file_list.sort()
          rank_cnt = 0
          
          for item in file_list:
            #determine mpi rank based on file name (rank_#)
            try:
              rank = item.split('_', 1)[1]
              rank = rank.rsplit('.', 1)[0]
            except:
              #skip file
              print("Warning: {} has the wrong format. It will be skipped.".format(item))
              continue
            try:
              rank = int(rank)
            except:
              rank = rank_cnt

            #open measurement file
            file_name = str(file_path) + "/" + str(item)

            try:
              with open(file_name) as json_file:
                #keep order of all objects
                try:
                  data = json.load(json_file, object_pairs_hook=OrderedDict)
                except:
                  print("Error: {} is not json.".format(file_path))
                  sys.exit()
            except IOError as ioe:
              print("Error: Cannot open file {} ({})".format(file_name, repr(ioe)))
              sys.exit()

            #get all events
            if not self.inc_metrics:
              self.inc_metrics = list(data['event_definitions'].keys())

            #get all threads
            json_rank[str(rank)] = OrderedDict()
            json_rank[str(rank)]['threads'] = data['threads']

            rank_cnt = rank_cnt + 1
          
          json_dict['ranks'] = json_rank
          self.dict = json_dict

        elif os.path.isfile(file_path):

          try:
            with open(file_path) as json_file:
              #keep order of all objects
              try:
                data = json.load(json_file, object_pairs_hook=OrderedDict)
              except:
                print("Error: {} is not json.".format(file_path))
                sys.exit()
          except IOError as ioe:
            print("Error: Cannot open file {} ({})".format(file_name, repr(ioe)))
            sys.exit()

          #get all events
          if not self.inc_metrics:
            self.inc_metrics = list(data['event_definitions'].keys())

          json_rank['0'] = OrderedDict()
          json_rank['0']['threads'] = data['threads']
          json_dict['ranks'] = json_rank
          self.dict = json_dict

        else:
          print("Error: {} does not exist.".format(file_path))
          sys.exit()

    def __add_child_node(self, list_roots, id, child_node):

        for root in list_roots:
          node_list = list(root.traverse())
          for node in node_list:
              #print("Node: ", node)
              if node.frame.values('id') == id:
                child_node.add_parent(node)
                node.add_child(child_node)
                break

    def __get_metrics(self, data, contain_read_events):
        metrics = OrderedDict()
        for metric in self.inc_metrics:
          if isinstance(data[metric],dict):
            contain_read_events[0] = 1
            metrics[metric] = int(data[metric]['region_value'])
          else:
            metrics[metric] = int(data[metric])
        return metrics

    def __get_read_metrics(self, data, read_id):
        metrics = OrderedDict()
        for metric in self.inc_metrics:
          if isinstance(data[metric],dict):
            metrics[metric] = int(data[metric][read_id])
        return metrics

    def read(self):
        #print(self.dict)
        list_roots = []
        node_dicts = []

        #add 'cycles' and 'real_time_nsec' to inc_metrics
        self.inc_metrics.append('cycles')
        self.inc_metrics.append('real_time_nsec')

        for rank, rank_value in self.dict['ranks'].items():
          #print("rank: ", int(rank))
          for thread, thread_value in rank_value['threads'].items():
            #print("thread: ", int(thread))
            for region, region_value in thread_value['regions'].items():

              #create graph for rank=0 and thread=0
              if int(rank) == 0 and int(thread) == 0:
                data = self.dict['ranks'][rank]['threads'][thread]['regions'][region]
                frame = Frame({"type": "region", "name": data['name'], "id": int(region)})
                node = Node(frame, None)

                contain_read_events = [0]
                metrics = self.__get_metrics(data, contain_read_events)

                node_dict = dict(
                  { "name": data['name'], "node": node,
                    "rank": int(rank),
                    "thread": int(thread),
                    "id": int(region),
                    **metrics,
                  }
                )
                node_dicts.append(node_dict)
                if int(data['parent_region_id']) == -1:
                  list_roots.append(node)
                else:
                  self.__add_child_node(list_roots, int(data['parent_region_id']), node)
                
                #check if we have to create child nodes for read events
                if contain_read_events[0] == 1:

                  #check how many read calls are used
                  read_num = len(data['cycles'])

                  for i in range (1, read_num):
                    node_name_read = "read_" + str(i)

                    read_frame = Frame({"type": "region", "name": node_name_read, "id": int(region)})
                    read_node = Node(read_frame, node)
                    read_metrics = self.__get_read_metrics(data, node_name_read)
                    node_dict = dict(
                      { "name": node_name_read, "node": read_node,
                        "rank": int(rank),
                        "thread": int(thread),
                        "id": int(region),
                        **read_metrics,
                      }
                    )
                    node_dicts.append(node_dict)
                    node.add_child(read_node)


              else:
                #fill up node dictionaries for all remaining ranks and threads
                print("soon")


        graph = Graph(list_roots)
        graph.enumerate_traverse()

        dataframe = pd.DataFrame(data=node_dicts)
        dataframe.set_index(["node", "rank", "thread"], inplace=True)
        dataframe.sort_index(inplace=True)

        return hatchet.graphframe.GraphFrame(graph, dataframe, [], self.inc_metrics)
