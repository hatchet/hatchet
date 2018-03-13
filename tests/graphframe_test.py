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
from hatchet import *


def test_filter_without_descendants():
    """Sanity test GraphFrame.filter()."""
    # hard-coded graph
    nodes = [Node(callpath_tuple=None, parent=None) for _ in range(7)]
    nodes[0].callpath = ('main',)
    nodes[0].parent = None
    nodes[0].children = [nodes[1], nodes[4]]
    nodes[1].callpath = ('main', 'MPI_Send')
    nodes[1].parent = nodes[0]
    nodes[1].children = [nodes[2], nodes[3]]
    nodes[2].callpath = ('main', 'MPI_Send', 'descendant_a')
    nodes[2].parent = nodes[1]
    nodes[2].children = []
    nodes[3].callpath = ('main', 'MPI_Send', 'descendant_b')
    nodes[3].parent = nodes[1]
    nodes[3].children = []
    nodes[4].callpath = ('main', 'MPI_Recv')
    nodes[4].parent = nodes[0]
    nodes[4].children = [nodes[5]]
    nodes[5].callpath = ('main', 'MPI_Recv', 'descendant_a')
    nodes[5].parent = nodes[4]
    nodes[5].children = [nodes[6]]
    nodes[6].callpath = ('main', 'MPI_Recv', 'descendant_a', 'descendant_a_a')
    nodes[6].parent = nodes[5]
    nodes[6].children = []
    graph = Graph(roots=None)
    graph.roots = [nodes[0]]

    # hard-coded dataframe
    data = [[1, 0, 'main', nodes[0]],
            [23, 0, 'MPI_Send', nodes[1]],
            [8236, 0, 'descendant_a', nodes[2]],
            [131, 0, 'descendant_b', nodes[3]],
            [4452, 0, 'descendant_a_a', nodes[6]]]
    columns = ['count', 'mpi.rank', 'path', 'node']
    dataframe = pd.DataFrame(data=data, columns=columns)
    dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)

    # hard-coded graphframe
    graphframe = GraphFrame()
    graphframe.dataframe = dataframe
    graphframe.graph = graph

    # filter the graphframe
    result = graphframe.filter(lambda x: 'MPI' in x['path'])

    # hard-coded result dataframe
    result_data = [[23, 0, 'MPI_Send', nodes[1]]]
    result_columns = ['count', 'mpi.rank', 'path', 'node']
    result_dataframe = pd.DataFrame(data=result_data, columns=result_columns)
    result_dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)

    # test dataframe equalities
    assert result.dataframe.equals(result_dataframe)


def test_filter_with_descendants():
    """Sanity test GraphFrame.filter()."""
    # hard-coded graph
    nodes = [Node(callpath_tuple=None, parent=None) for _ in range(7)]
    nodes[0].callpath = ('main',)
    nodes[0].parent = None
    nodes[0].children = [nodes[1], nodes[4]]
    nodes[1].callpath = ('main', 'MPI_Send')
    nodes[1].parent = nodes[0]
    nodes[1].children = [nodes[2], nodes[3]]
    nodes[2].callpath = ('main', 'MPI_Send', 'descendant_a')
    nodes[2].parent = nodes[1]
    nodes[2].children = []
    nodes[3].callpath = ('main', 'MPI_Send', 'descendant_b')
    nodes[3].parent = nodes[1]
    nodes[3].children = []
    nodes[4].callpath = ('main', 'MPI_Recv')
    nodes[4].parent = nodes[0]
    nodes[4].children = [nodes[5]]
    nodes[5].callpath = ('main', 'MPI_Recv', 'descendant_a')
    nodes[5].parent = nodes[4]
    nodes[5].children = [nodes[6]]
    nodes[6].callpath = ('main', 'MPI_Recv', 'descendant_a', 'descendant_a_a')
    nodes[6].parent = nodes[5]
    nodes[6].children = []
    graph = Graph(roots=None)
    graph.roots = [nodes[0]]

    # hard-coded dataframe
    data = [[1, 0, 'main', nodes[0]],
            [23, 0, 'MPI_Send', nodes[1]],
            [8236, 0, 'descendant_a', nodes[2]],
            [131, 0, 'descendant_b', nodes[3]],
            [4452, 0, 'descendant_a_a', nodes[6]]]
    columns = ['count', 'mpi.rank', 'path', 'node']
    dataframe = pd.DataFrame(data=data, columns=columns)
    dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)

    # hard-coded graphframe
    graphframe = GraphFrame()
    graphframe.dataframe = dataframe
    graphframe.graph = graph

    # filter the graphframe
    result = graphframe.filter(lambda x: 'MPI' in x['path'],
                               has_descendants=True)

    # hard-coded result dataframe
    result_data = [[23, 0, 'MPI_Send', nodes[1]],
                   [8236, 0, 'descendant_a', nodes[2]],
                   [131, 0, 'descendant_b', nodes[3]]]
    result_columns = ['count', 'mpi.rank', 'path', 'node']
    result_dataframe = pd.DataFrame(data=result_data, columns=result_columns)
    result_dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)

    # test dataframe equalities
    assert result.dataframe.equals(result_dataframe)
