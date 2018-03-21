

def test_fill_a():
    """Sanity test GraphFrame.fill()."""
    # hard-coded graphframe input
    nodes = [Node(callpath_tuple=None, parent=None) for _ in range(4)]
    nodes[0].callpath = ('main',)
    nodes[0].parent = None
    nodes[0].children = [nodes[1]]
    nodes[1].callpath = ('main', 'foo')
    nodes[1].parent = nodes[0]
    nodes[1].children = [nodes[2]]
    nodes[2].callpath = ('main', 'foo', 'bar')
    nodes[2].parent = nodes[1]
    nodes[2].children = [nodes[3]]
    nodes[3].callpath = ('main', 'foo', 'bar', 'baz')
    nodes[3].parent = nodes[2]
    nodes[3].children = []
    graph = Graph(roots=None)
    graph.roots = [nodes[0]]
    data = [[28, 1, 'foo', nodes[1]],
            [43, 2, 'baz', nodes[3]]]
    columns = ['count', 'mpi.rank', 'path', 'node']
    dataframe = pd.DataFrame(data=data, columns=columns)
    dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    graphframe = GraphFrame()
    graphframe.dataframe = dataframe
    graphframe.graph = graph

    # hard-coded graphframe output
    result_graph = graph
    result_data = [[28, 1, 'foo', nodes[1]],
                   [43, 2, 'baz', nodes[3]],
                   [0, 1, 'main', nodes[0]],
                   [0, 2, 'bar', nodes[2]],
                   [0, 2, 'foo', nodes[1]],
                   [0, 2, 'main', nodes[0]]]
    result_columns = ['count', 'mpi.rank', 'path', 'node']
    result_dataframe = pd.DataFrame(data=result_data, columns=result_columns)
    result_dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    result_graphframe = GraphFrame()
    result_graphframe.dataframe = result_dataframe
    result_graphframe.graph = result_graph

    # computed graphframe output
    fill_maps = {'node': lambda x: x.loc['node'].parent,
                 'mpi.rank': lambda x: x.loc['mpi.rank'],
                 'count': lambda x: 0,
                 'path': lambda x: x.loc['node'].parent.callpath[-1]}
    filled_graphframe = graphframe.fill(fill_maps=fill_maps)

    # test graph equalities
    assert filled_graphframe.graph is result_graphframe.graph

    # test dataframe equalities
    assert filled_graphframe.dataframe.equals(result_graphframe.dataframe)


def test_fill_b():
    """Sanity test GraphFrame.fill()."""
    # hard-coded graphframe input
    nodes = [Node(callpath_tuple=None, parent=None) for _ in range(4)]
    nodes[0].callpath = ('main',)
    nodes[0].parent = None
    nodes[0].children = [nodes[1]]
    nodes[1].callpath = ('main', 'foo')
    nodes[1].parent = nodes[0]
    nodes[1].children = [nodes[2]]
    nodes[2].callpath = ('main', 'foo', 'bar')
    nodes[2].parent = nodes[1]
    nodes[2].children = [nodes[3]]
    nodes[3].callpath = ('main', 'foo', 'bar', 'baz')
    nodes[3].parent = nodes[2]
    nodes[3].children = []
    graph = Graph(roots=None)
    graph.roots = [nodes[0]]
    data = [[28, 1, 'foo', nodes[1]],
            [43, 1, 'baz', nodes[3]]]
    columns = ['count', 'mpi.rank', 'path', 'node']
    dataframe = pd.DataFrame(data=data, columns=columns)
    dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    graphframe = GraphFrame()
    graphframe.dataframe = dataframe
    graphframe.graph = graph

    # hard-coded graphframe output
    result_graph = graph
    result_data = [[28, 1, 'foo', nodes[1]],
                   [43, 1, 'baz', nodes[3]],
                   [0, 1, 'main', nodes[0]],
                   [0, 1, 'bar', nodes[2]]]
    result_columns = ['count', 'mpi.rank', 'path', 'node']
    result_dataframe = pd.DataFrame(data=result_data, columns=result_columns)
    result_dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    result_graphframe = GraphFrame()
    result_graphframe.dataframe = result_dataframe
    result_graphframe.graph = result_graph

    # computed graphframe output
    fill_maps = {'node': lambda x: x.loc['node'].parent,
                 'mpi.rank': lambda x: x.loc['mpi.rank'],
                 'count': lambda x: 0,
                 'path': lambda x: x.loc['node'].parent.callpath[-1]}
    filled_graphframe = graphframe.fill(fill_maps=fill_maps)

    # test graph equalities
    assert filled_graphframe.graph is result_graphframe.graph

    # test dataframe equalities
    assert filled_graphframe.dataframe.equals(result_graphframe.dataframe)
