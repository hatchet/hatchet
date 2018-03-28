##############################################################################
# Copyright (c) 2017-2018, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# This file is part of Hatchet.
# Created by Abhinav Bhatele <bhatele@llnl.gov>.
# LLNL-CODE-741008. All rights reserved.
#
# For details, see: https://github.com/LLNL/hatchet
# Please also read the LICENSE file for the MIT License notice.
##############################################################################

import pandas as pd
from hatchet.node import Node
from hatchet.graph import Graph
from hatchet.graphframe import GraphFrame


def test_filter_a():
    """Sanity test GraphFrame.filter()."""
    # graphframe input
    input_nodes = [Node(callpath_tuple=None, parent=None) for _ in range(3)]
    input_nodes[0].callpath = ('main',)
    input_nodes[0].parent = None
    input_nodes[0].children = [input_nodes[1], input_nodes[2]]
    input_nodes[1].callpath = ('main', 'MPI_Send')
    input_nodes[1].parent = input_nodes[0]
    input_nodes[1].children = []
    input_nodes[2].callpath = ('main', 'MPI_Recv')
    input_nodes[2].parent = input_nodes[0]
    input_nodes[2].children = []
    input_graph = Graph(roots=None)
    input_graph.roots = [input_nodes[0]]
    input_data = [[1, 0, 'main', input_nodes[0]],
                  [3023, 0, 'MPI_Send', input_nodes[1]],
                  [8236, 0, 'MPI_Recv', input_nodes[2]]]
    input_columns = ['count', 'mpi.rank', 'path', 'node']
    input_dataframe = pd.DataFrame(data=input_data, columns=input_columns)
    input_dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    input_graphframe = GraphFrame()
    input_graphframe.dataframe = input_dataframe
    input_graphframe.graph = input_graph

    # expected graphframe output
    expected_graph = input_graph
    expected_data = [[3023, 0, 'MPI_Send', input_nodes[1]],
                     [8236, 0, 'MPI_Recv', input_nodes[2]]]
    expected_columns = ['count', 'mpi.rank', 'path', 'node']
    expected_dataframe = pd.DataFrame(data=expected_data,
                                      columns=expected_columns)
    expected_dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    expected_graphframe = GraphFrame()
    expected_graphframe.dataframe = expected_dataframe
    expected_graphframe.graph = expected_graph

    # computed graphframe output
    is_row_qualified = lambda x: 'MPI' in x['path']
    computed_graphframe = input_graphframe.filter(is_row_qualified)

    # test graphframe equalities
    assert computed_graphframe.dataframe.equals(expected_graphframe.dataframe)
    assert computed_graphframe.graph is expected_graphframe.graph


def test_filter_b():
    """Sanity test GraphFrame.filter()."""
    # graphframe input
    input_nodes = [Node(callpath_tuple=None, parent=None) for _ in range(3)]
    input_nodes[0].callpath = ('MPI_call_a',)
    input_nodes[0].parent = None
    input_nodes[0].children = [input_nodes[1]]
    input_nodes[1].callpath = ('MPI_call_a', 'intermediary_call')
    input_nodes[1].parent = input_nodes[0]
    input_nodes[1].children = [input_nodes[2]]
    input_nodes[2].callpath = ('MPI_call_a', 'intermediary_call', 'MPI_call_b')
    input_nodes[2].parent = input_nodes[1]
    input_nodes[2].children = []
    input_graph = Graph(roots=None)
    input_graph.roots = [input_nodes[0]]
    input_data = [[1, 0, 'MPI_call_a', input_nodes[0]],
            [3023, 0, 'intermediary_call', input_nodes[1]],
            [9274, 0, 'MPI_call_b', input_nodes[2]]]
    input_columns = ['count', 'mpi.rank', 'path', 'node']
    input_dataframe = pd.DataFrame(data=input_data, columns=input_columns)
    input_dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    input_graphframe = GraphFrame()
    input_graphframe.dataframe = input_dataframe
    input_graphframe.graph = input_graph

    # expected graphframe output
    expected_graph = input_graph
    expected_data = [[1, 0, 'MPI_call_a', input_nodes[0]],
                     [9274, 0, 'MPI_call_b', input_nodes[2]]]
    expected_columns = ['count', 'mpi.rank', 'path', 'node']
    expected_dataframe = pd.DataFrame(data=expected_data,
                                      columns=expected_columns)
    expected_dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    expected_graphframe = GraphFrame()
    expected_graphframe.dataframe = expected_dataframe
    expected_graphframe.graph = expected_graph

    # computed graphframe output
    is_row_qualified = lambda x: 'MPI' in x['path']
    computed_graphframe = input_graphframe.filter(is_row_qualified)

    # test graphframe equalities
    assert computed_graphframe.dataframe.equals(expected_graphframe.dataframe)
    assert computed_graphframe.graph is expected_graphframe.graph
