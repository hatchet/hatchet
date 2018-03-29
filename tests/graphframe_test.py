

def test_fill_a():
    """Sanity test GraphFrame.fill()."""
    # graphframe input
    input_nodes = [Node(callpath_tuple=None, parent=None) for _ in range(4)]
    input_nodes[0].callpath = ('main',)
    input_nodes[0].parent = None
    input_nodes[0].children = [input_nodes[1]]
    input_nodes[1].callpath = ('main', 'foo')
    input_nodes[1].parent = input_nodes[0]
    input_nodes[1].children = [input_nodes[2]]
    input_nodes[2].callpath = ('main', 'foo', 'bar')
    input_nodes[2].parent = input_nodes[1]
    input_nodes[2].children = [input_nodes[3]]
    input_nodes[3].callpath = ('main', 'foo', 'bar', 'baz')
    input_nodes[3].parent = input_nodes[2]
    input_nodes[3].children = []
    input_graph = Graph(roots=None)
    input_graph.roots = [input_nodes[0]]
    input_data = [[28, 1, 'foo', input_nodes[1]],
                  [43, 2, 'baz', input_nodes[3]]]
    input_columns = ['count', 'mpi.rank', 'path', 'node']
    input_dataframe = pd.DataFrame(data=input_data, columns=input_columns)
    input_dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    input_graphframe = GraphFrame()
    input_graphframe.dataframe = input_dataframe
    input_graphframe.graph = input_graph

    # expected graphframe output
    expected_graph = input_graph
    expected_data = [[28, 1, 'foo', input_nodes[1]],
                     [0, 1, 'main', input_nodes[0]],
                     [43, 2, 'baz', input_nodes[3]],
                     [0, 2, 'bar', input_nodes[2]],
                     [0, 2, 'foo', input_nodes[1]],
                     [0, 2, 'main', input_nodes[0]]]
    expected_columns = ['count', 'mpi.rank', 'path', 'node']
    expected_dataframe = pd.DataFrame(data=expected_data,
                                      columns=expected_columns)
    expected_dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    expected_graphframe = GraphFrame()
    expected_graphframe.dataframe = expected_dataframe
    expected_graphframe.graph = expected_graph

    # computed graphframe output
    fill_maps = {'node': lambda x: x.loc['node'].parent,
                 'mpi.rank': lambda x: x.loc['mpi.rank'],
                 'count': lambda x: 0,
                 'path': lambda x: x.loc['node'].parent.callpath[-1]}
    computed_graphframe = input_graphframe.fill(fill_maps)

    # test graphframe equalities
    assert computed_graphframe.dataframe.equals(expected_graphframe.dataframe)
    assert computed_graphframe.graph is expected_graphframe.graph


def test_fill_b():
    """Sanity test GraphFrame.fill()."""
    # graphframe input
    input_nodes = [Node(callpath_tuple=None, parent=None) for _ in range(4)]
    input_nodes[0].callpath = ('main',)
    input_nodes[0].parent = None
    input_nodes[0].children = [input_nodes[1]]
    input_nodes[1].callpath = ('main', 'foo')
    input_nodes[1].parent = input_nodes[0]
    input_nodes[1].children = [input_nodes[2]]
    input_nodes[2].callpath = ('main', 'foo', 'bar')
    input_nodes[2].parent = input_nodes[1]
    input_nodes[2].children = [input_nodes[3]]
    input_nodes[3].callpath = ('main', 'foo', 'bar', 'baz')
    input_nodes[3].parent = input_nodes[2]
    input_nodes[3].children = []
    input_graph = Graph(roots=None)
    input_graph.roots = [input_nodes[0]]
    input_data = [[28, 1, 'foo', input_nodes[1]],
                  [43, 1, 'baz', input_nodes[3]]]
    input_columns = ['count', 'mpi.rank', 'path', 'node']
    input_dataframe = pd.DataFrame(data=input_data, columns=input_columns)
    input_dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    input_graphframe = GraphFrame()
    input_graphframe.dataframe = input_dataframe
    input_graphframe.graph = input_graph

    # expected graphframe output
    expected_graph = input_graph
    expected_data = [[28, 1, 'foo', input_nodes[1]],
                     [0, 1, 'main', input_nodes[0]],
                     [43, 1, 'baz', input_nodes[3]],
                     [0, 1, 'bar', input_nodes[2]]]
    expected_columns = ['count', 'mpi.rank', 'path', 'node']
    expected_dataframe = pd.DataFrame(data=expected_data,
                                      columns=expected_columns)
    expected_dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    expected_graphframe = GraphFrame()
    expected_graphframe.dataframe = expected_dataframe
    expected_graphframe.graph = expected_graph

    # computed graphframe output
    fill_maps = {'node': lambda x: x.loc['node'].parent,
                 'mpi.rank': lambda x: x.loc['mpi.rank'],
                 'count': lambda x: 0,
                 'path': lambda x: x.loc['node'].parent.callpath[-1]}
    computed_graphframe = input_graphframe.fill(fill_maps)

    # test graphframe equalities
    assert computed_graphframe.dataframe.equals(expected_graphframe.dataframe)
    assert computed_graphframe.graph is expected_graphframe.graph
