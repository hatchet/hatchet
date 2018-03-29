

def test_reduce_a():
    """Sanity test GraphFrame.reduce()."""
    # graphframe input
    input_nodes = [Node(callpath_tuple=None, parent=None) for _ in range(2)]
    input_nodes[0].callpath = ('foo',)
    input_nodes[0].parent = None
    input_nodes[0].children = [input_nodes[1]]
    input_nodes[1].callpath = ('bar',)
    input_nodes[1].parent = input_nodes[0]
    input_nodes[1].children = []
    input_graph = Graph(roots=None)
    input_graph.roots = [input_nodes[0]]
    input_data = [[4, 0, 'foo', input_nodes[0]],
                  [6, 0, 'foo', input_nodes[0]],
                  [13, 0, 'bar', input_nodes[1]],
                  [14, 0, 'bar', input_nodes[1]]]
    input_columns = ['count', 'mpi.rank', 'path', 'node']
    input_dataframe = pd.DataFrame(data=input_data, columns=input_columns)
    input_dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    input_graphframe = GraphFrame()
    input_graphframe.dataframe = input_dataframe
    input_graphframe.graph = input_graph

    # expected graphframe output
    expected_graph = input_graph
    expected_data = [[5, 0, 'foo', input_nodes[0]],
                     [13.5, 0, 'bar', input_nodes[1]]]
    expected_columns = ['count', 'mpi.rank', 'path', 'node']
    expected_dataframe = pd.DataFrame(data=expected_data,
                                      columns=expected_columns)
    expected_dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    expected_graphframe = GraphFrame()
    expected_graphframe.dataframe = expected_dataframe
    expected_graphframe.graph = expected_graph

    # computed graphframe output
    reduction_operators = {'node': lambda x: x[0],
                           'mpi.rank': lambda x: x[0],
                           'count': lambda x: sum(x) / float(len(x)),
                           'path': lambda x: x[0]}
    computed_graphframe = input_graphframe.reduce(reduction_operators)

    # test graphframe equalities
    assert computed_graphframe.dataframe.equals(expected_graphframe.dataframe)
    assert computed_graphframe.graph is expected_graphframe.graph


def test_reduce_b():
    """Sanity test GraphFrame.reduce()."""
    # graphframe input
    input_nodes = [Node(callpath_tuple=None, parent=None) for _ in range(2)]
    input_nodes[0].callpath = ('foo',)
    input_nodes[0].parent = None
    input_nodes[0].children = [input_nodes[1]]
    input_nodes[1].callpath = ('bar',)
    input_nodes[1].parent = input_nodes[0]
    input_nodes[1].children = []
    input_graph = Graph(roots=None)
    input_graph.roots = [input_nodes[0]]
    input_data = [[901, 0, 'foo', input_nodes[0]],
                  [1842, 0, 'foo', input_nodes[0]],
                  [5060, 0, 'foo', input_nodes[0]],
                  [23, 0, 'foo', input_nodes[0]],
                  [951, 0, 'foo', input_nodes[0]],
                  [6, 0, 'foo', input_nodes[0]],
                  [18, 0, 'bar', input_nodes[1]],
                  [423, 0, 'bar', input_nodes[1]],
                  [1241, 0, 'bar', input_nodes[1]],
                  [23, 0, 'bar', input_nodes[1]],
                  [156, 0, 'bar', input_nodes[1]],
                  [64, 0, 'bar', input_nodes[1]]]
    input_columns = ['count', 'mpi.rank', 'path', 'node']
    input_dataframe = pd.DataFrame(data=input_data, columns=input_columns)
    input_dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    input_graphframe = GraphFrame()
    input_graphframe.dataframe = input_dataframe
    input_graphframe.graph = input_graph

    # expected graphframe output
    expected_graph = input_graph
    expected_data = [[107138897 / float(36), 0, 'foo', input_nodes[0]],
                     [6784145 / float(36), 0, 'bar', input_nodes[1]]]
    expected_columns = ['count', 'mpi.rank', 'path', 'node']
    expected_dataframe = pd.DataFrame(data=expected_data,
                                      columns=expected_columns)
    expected_dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    expected_graphframe = GraphFrame()
    expected_graphframe.dataframe = expected_dataframe
    expected_graphframe.graph = expected_graph

    # computed graphframe output
    import numpy as np
    reduction_operators = {'node': lambda x: x[0],
                           'mpi.rank': lambda x: x[0],
                           'count': lambda x: np.var(x),
                           'path': lambda x: x[0]}
    computed_graphframe = input_graphframe.reduce(reduction_operators)

    # test graphframe equalities
    assert computed_graphframe.dataframe.equals(expected_graphframe.dataframe)
    assert computed_graphframe.graph is expected_graphframe.graph
