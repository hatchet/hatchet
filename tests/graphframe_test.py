

def test_union_a():
    """Sanity test GraphFrame.union()."""
    # hard-coded graphframe a input
    node_a = Node(callpath_tuple=None, parent=None)
    node_a.callpath = ('MPI',)
    node_a.parent = None
    node_a.children = []
    graph_a = Graph(roots=None)
    graph_a.roots = [node_a]
    data_a = [[142, 0, 'MPI', node_a]]
    columns_a = ['count', 'mpi.rank', 'path', 'node']
    dataframe_a = pd.DataFrame(data=data_a, columns=columns_a)
    dataframe_a.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    graphframe_a = GraphFrame()
    graphframe_a.dataframe = dataframe_a
    graphframe_a.graph = graph_a

    # hard-coded graphframe b input
    node_b = Node(callpath_tuple=None, parent=None)
    node_b.callpath = ('IB',)
    node_b.parent = None
    node_b.children = []
    graph_b = Graph(roots=None)
    graph_b.roots = [node_b]
    data_b = [[1842, 0, 'IB', node_b]]
    columns_b = ['count', 'mpi.rank', 'path', 'node']
    dataframe_b = pd.DataFrame(data=data_b, columns=columns_b)
    dataframe_b.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    graphframe_b = GraphFrame()
    graphframe_b.dataframe = dataframe_b
    graphframe_b.graph = graph_b

    # hard-coded unioned graphframe output
    result_graph = Graph(roots=None)
    result_graph.roots = [node_a, node_b]
    result_data = [[142, 0, 'MPI', node_a],
                   [1842, 0, 'IB', node_b]]
    result_columns = ['count', 'mpi.rank', 'path', 'node']
    result_dataframe = pd.DataFrame(data=result_data, columns=result_columns)
    result_dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)

    # get unioned graphframe output
    unioned_graphframe = graphframe_a.union(graphframe_b)

    # test graph equalities
    for root_a, root_b in zip(sorted(result_graph.roots),
                              sorted(unioned_graphframe.graph.roots)):
        for node_a, node_b in zip(root_a.traverse(), root_b.traverse()):
            assert node_a.callpath == node_b.callpath

    # test dataframe equalities
    assert result_dataframe.equals(unioned_graphframe.dataframe)


def test_union_b():
    """Sanity test GraphFrame.union()."""
    # hard-coded graphframe a input
    nodes_a = [Node(callpath_tuple=None, parent=None) for _ in range(2)]
    nodes_a[0].callpath = ('main',)
    nodes_a[0].parent = None
    nodes_a[0].children = [nodes_a[1]]
    nodes_a[1].callpath = ('main', 'foo',)
    nodes_a[1].parent = nodes_a[0]
    nodes_a[1].children = []
    graph_a = Graph(roots=None)
    graph_a.roots = [nodes_a[0]]
    data_a = [[142, 0, 'foo', nodes_a[1]]]
    columns_a = ['count', 'mpi.rank', 'path', 'node']
    dataframe_a = pd.DataFrame(data=data_a, columns=columns_a)
    dataframe_a.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    graphframe_a = GraphFrame()
    graphframe_a.dataframe = dataframe_a
    graphframe_a.graph = graph_a

    # hard-coded graphframe b input
    nodes_b = [Node(callpath_tuple=None, parent=None) for _ in range(2)]
    nodes_b[0].callpath = ('main',)
    nodes_b[0].parent = None
    nodes_b[0].children = [nodes_b[1]]
    nodes_b[1].callpath = ('main', 'bar',)
    nodes_b[1].parent = nodes_b[0]
    nodes_b[1].children = []
    graph_b = Graph(roots=None)
    graph_b.roots = [nodes_b[0]]
    data_b = [[1842, 1, 'main', nodes_b[0]]]
    columns_b = ['count', 'mpi.rank', 'path', 'node']
    dataframe_b = pd.DataFrame(data=data_b, columns=columns_b)
    dataframe_b.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    graphframe_b = GraphFrame()
    graphframe_b.dataframe = dataframe_b
    graphframe_b.graph = graph_b

    # hard-coded unioned graphframe output
    nodes_c = [Node(callpath_tuple=None, parent=None) for _ in range(3)]
    nodes_c[0].callpath = ('main',)
    nodes_c[0].parent = None
    nodes_c[0].children = [nodes_c[1], nodes_c[2]]
    nodes_c[1].callpath = ('main', 'foo')
    nodes_c[1].parent = nodes_c[0]
    nodes_c[1].children = []
    nodes_c[2].callpath = ('main', 'bar')
    nodes_c[2].parent = nodes_c[0]
    nodes_c[2].children = []
    result_graph = Graph(roots=None)
    result_graph.roots = [nodes_c[0]]
    result_data = [[142, 0, 'foo', nodes_c[1]],
                   [1842, 1, 'main', nodes_c[0]]]
    result_columns = ['count', 'mpi.rank', 'path', 'node']
    result_dataframe = pd.DataFrame(data=result_data, columns=result_columns)
    result_dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)

    # get unioned graphframe output
    unioned_graphframe = graphframe_a.union(graphframe_b)

    # test graph equalities
    for root_a, root_b in zip(sorted(result_graph.roots),
                              sorted(unioned_graphframe.graph.roots)):
        for node_a, node_b in zip(root_a.traverse(), root_b.traverse()):
            assert node_a.callpath == node_b.callpath

    # test dataframe equalities
    assert result_dataframe.equals(unioned_graphframe.dataframe)
