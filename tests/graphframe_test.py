

def test_union_a():
    """Sanity test GraphFrame.union()."""
    # graphframe a input
    input_nodes_a = [Node(callpath_tuple=None, parent=None) for _ in range(1)]
    input_nodes_a[0].callpath = ('MPI',)
    input_nodes_a[0].parent = None
    input_nodes_a[0].children = []
    input_graph_a = Graph(roots=None)
    input_graph_a.roots = [input_nodes_a[0]]
    input_data_a = [[142, 0, 'MPI', input_nodes_a[0]]]
    input_columns_a = ['count', 'mpi.rank', 'path', 'node']
    input_dataframe_a = pd.DataFrame(data=input_data_a, columns=input_columns_a)
    input_dataframe_a.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    input_graphframe_a = GraphFrame()
    input_graphframe_a.dataframe = input_dataframe_a
    input_graphframe_a.graph = input_graph_a

    # graphframe b input
    input_nodes_b = [Node(callpath_tuple=None, parent=None) for _ in range(1)]
    input_nodes_b[0].callpath = ('IB',)
    input_nodes_b[0].parent = None
    input_nodes_b[0].children = []
    input_graph_b = Graph(roots=None)
    input_graph_b.roots = [input_nodes_b[0]]
    input_data_b = [[1842, 0, 'IB', input_nodes_b[0]]]
    input_columns_b = ['count', 'mpi.rank', 'path', 'node']
    input_dataframe_b = pd.DataFrame(data=input_data_b, columns=input_columns_b)
    input_dataframe_b.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    input_graphframe_b = GraphFrame()
    input_graphframe_b.dataframe = input_dataframe_b
    input_graphframe_b.graph = input_graph_b

    # expected graphframe output
    expected_nodes = [Node(callpath_tuple=None, parent=None) for _ in range(2)]
    expected_nodes[0].callpath = ('MPI',)
    expected_nodes[0].parent = None
    expected_nodes[0].children = []
    expected_nodes[1].callpath = ('IB',)
    expected_nodes[1].parent = None
    expected_nodes[1].children = []
    expected_graph = Graph(roots=None)
    expected_graph.roots = [expected_nodes[0], expected_nodes[1]]
    expected_data = [[142, 0, 'MPI', expected_nodes[0]],
                     [1842, 0, 'IB', expected_nodes[1]]]
    expected_columns = ['count', 'mpi.rank', 'path', 'node']
    expected_dataframe = pd.DataFrame(data=expected_data,
                                      columns=expected_columns)
    expected_dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    expected_graphframe = GraphFrame()
    expected_graphframe.dataframe = expected_dataframe
    expected_graphframe.graph = expected_graph

    # computed graphframe output
    computed_graphframe = input_graphframe_a.union(input_graphframe_b)

    # test graphframe equalities
    assert computed_graphframe.dataframe.equals(expected_graphframe.dataframe)
    assert computed_graphframe.graph.roots == expected_graphframe.graph.roots
    for root_a, root_b in zip(computed_graphframe.graph.roots,
                              expected_graphframe.graph.roots):
        assert list(root_a.traverse()) == list(root_b.traverse())


def test_union_b():
    """Sanity test GraphFrame.union()."""
    # graphframe a input
    input_nodes_a = [Node(callpath_tuple=None, parent=None) for _ in range(3)]
    input_nodes_a[0].callpath = ('main',)
    input_nodes_a[0].parent = None
    input_nodes_a[0].children = [input_nodes_a[1], input_nodes_a[2]]
    input_nodes_a[1].callpath = ('main', 'foo')
    input_nodes_a[1].parent = input_nodes_a[0]
    input_nodes_a[1].children = []
    input_nodes_a[2].callpath = ('main', 'bar')
    input_nodes_a[2].parent = input_nodes_a[0]
    input_nodes_a[2].children = []
    input_graph_a = Graph(roots=None)
    input_graph_a.roots = [input_nodes_a[0]]
    input_data_a = [[142, 0, 'foo', input_nodes_a[1]]]
    input_columns_a = ['count', 'mpi.rank', 'path', 'node']
    input_dataframe_a = pd.DataFrame(data=input_data_a, columns=input_columns_a)
    input_dataframe_a.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    input_graphframe_a = GraphFrame()
    input_graphframe_a.dataframe = input_dataframe_a
    input_graphframe_a.graph = input_graph_a

    # graphframe b input
    input_nodes_b = [Node(callpath_tuple=None, parent=None) for _ in range(3)]
    input_nodes_b[0].callpath = ('main',)
    input_nodes_b[0].parent = None
    input_nodes_b[0].children = [input_nodes_b[1]]
    input_nodes_b[1].callpath = ('main', 'bar')
    input_nodes_b[1].parent = input_nodes_b[0]
    input_nodes_b[1].children = [input_nodes_b[2]]
    input_nodes_b[2].callpath = ('main', 'bar', 'baz')
    input_nodes_b[2].parent = input_nodes_b[1]
    input_nodes_b[2].children = []
    input_graph_b = Graph(roots=None)
    input_graph_b.roots = [input_nodes_b[0]]
    input_data_b = [[1842, 1, 'main', input_nodes_b[0]]]
    input_columns_b = ['count', 'mpi.rank', 'path', 'node']
    input_dataframe_b = pd.DataFrame(data=input_data_b, columns=input_columns_b)
    input_dataframe_b.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    input_graphframe_b = GraphFrame()
    input_graphframe_b.dataframe = input_dataframe_b
    input_graphframe_b.graph = input_graph_b

    # expected graphframe output
    expected_nodes = [Node(callpath_tuple=None, parent=None) for _ in range(4)]
    expected_nodes[0].callpath = ('main',)
    expected_nodes[0].parent = None
    expected_nodes[0].children = [expected_nodes[1], expected_nodes[2]]
    expected_nodes[1].callpath = ('main', 'foo')
    expected_nodes[1].parent = expected_nodes[0]
    expected_nodes[1].children = []
    expected_nodes[2].callpath = ('main', 'bar')
    expected_nodes[2].parent = expected_nodes[0]
    expected_nodes[2].children = [expected_nodes[3]]
    expected_nodes[3].callpath = ('main', 'bar', 'baz')
    expected_nodes[3].parent = expected_nodes[2]
    expected_nodes[3].children = []
    expected_graph = Graph(roots=None)
    expected_graph.roots = [expected_nodes[0]]
    expected_data = [[142, 0, 'foo', expected_nodes[1]],
                     [1842, 1, 'main', expected_nodes[0]]]
    expected_columns = ['count', 'mpi.rank', 'path', 'node']
    expected_dataframe = pd.DataFrame(data=expected_data,
                                      columns=expected_columns)
    expected_dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    expected_graphframe = GraphFrame()
    expected_graphframe.dataframe = expected_dataframe
    expected_graphframe.graph = expected_graph

    # computed graphframe output
    computed_graphframe = input_graphframe_a.union(input_graphframe_b)

    # test graphframe equalities
    assert computed_graphframe.dataframe.equals(expected_graphframe.dataframe)
    assert computed_graphframe.graph.roots == expected_graphframe.graph.roots
    for root_a, root_b in zip(computed_graphframe.graph.roots,
                              expected_graphframe.graph.roots):
        assert list(root_a.traverse()) == list(root_b.traverse())
