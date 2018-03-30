

def test_graft_a():
    """Sanity test GraphFrame.graft()."""
    # graphframe input
    input_nodes = [Node(callpath_tuple=None, parent=None) for _ in range(3)]
    input_nodes[0].callpath = ('main',)
    input_nodes[0].parent = None
    input_nodes[0].children = [input_nodes[1], input_nodes[2]]
    input_nodes[1].callpath = ('main', 'foo')
    input_nodes[1].parent = input_nodes[0]
    input_nodes[1].children = []
    input_nodes[2].callpath = ('main', 'bar')
    input_nodes[2].parent = input_nodes[0]
    input_nodes[2].children = []
    input_graph = Graph(roots=None)
    input_graph.roots = [input_nodes[0]]
    input_data = [[54, 0, 'foo', input_nodes[1]],
            [27, 0, 'bar', input_nodes[2]]]
    input_columns = ['count', 'mpi.rank', 'path', 'node']
    input_dataframe = pd.DataFrame(data=input_data, columns=input_columns)
    input_dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    input_graphframe = GraphFrame()
    input_graphframe.dataframe = input_dataframe
    input_graphframe.graph = input_graph

    # expected graphframe output
    expected_nodes = [Node(callpath_tuple=None, parent=None) for _ in range(2)]
    expected_nodes[0].callpath = ('foo',)
    expected_nodes[0].parent = None
    expected_nodes[0].children = []
    expected_nodes[1].callpath = ('bar',)
    expected_nodes[1].parent = None
    expected_nodes[1].children = []
    expected_graph = Graph(roots=None)
    expected_graph.roots = [expected_nodes[0], expected_nodes[1]]
    expected_data = [[54, 0, 'foo', expected_nodes[0]],
                     [27, 0, 'bar', expected_nodes[1]]]
    expected_columns = ['count', 'mpi.rank', 'path', 'node']
    expected_dataframe = pd.DataFrame(data=expected_data,
                                      columns=expected_columns)
    expected_dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    expected_graphframe = GraphFrame()
    expected_graphframe.dataframe = expected_dataframe
    expected_graphframe.graph = expected_graph

    # computed graphframe output
    computed_graphframe = input_graphframe.graft()

    # test graphframe equalities
    assert computed_graphframe.dataframe.equals(expected_graphframe.dataframe)
    assert computed_graphframe.graph.roots == expected_graphframe.graph.roots
    for root_a, root_b in zip(computed_graphframe.graph.roots,
                              expected_graphframe.graph.roots):
        assert list(root_a.traverse()) == list(root_b.traverse())


def test_graft_b():
    """Sanity test GraphFrame.graft()."""
    # graphframe input
    input_nodes = [Node(callpath_tuple=None, parent=None) for _ in range(7)]
    input_nodes[0].callpath = ('main',)
    input_nodes[0].parent = None
    input_nodes[0].children = [input_nodes[1], input_nodes[3]]
    input_nodes[1].callpath = ('main', 'foo')
    input_nodes[1].parent = input_nodes[0]
    input_nodes[1].children = [input_nodes[2]]
    input_nodes[2].callpath = ('main', 'foo', 'a')
    input_nodes[2].parent = input_nodes[1]
    input_nodes[2].children = []
    input_nodes[3].callpath = ('main', 'bar')
    input_nodes[3].parent = input_nodes[0]
    input_nodes[3].children = [input_nodes[4]]
    input_nodes[4].callpath = ('main', 'bar', 'foo')
    input_nodes[4].parent = input_nodes[3]
    input_nodes[4].children = [input_nodes[5], input_nodes[6]]
    input_nodes[5].callpath = ('main', 'bar', 'foo', 'a')
    input_nodes[5].parent = input_nodes[4]
    input_nodes[5].children = []
    input_nodes[6].callpath = ('main', 'bar', 'foo', 'b')
    input_nodes[6].parent = input_nodes[4]
    input_nodes[6].children = []
    input_graph = Graph(roots=None)
    input_graph.roots = [input_nodes[0]]
    input_data = [[19, 0, 'foo', input_nodes[1]],
                  [27, 0, 'a', input_nodes[2]],
                  [43, 0, 'foo', input_nodes[4]],
                  [65, 0, 'a', input_nodes[5]],
                  [17, 0, 'b', input_nodes[6]]]
    input_columns = ['count', 'mpi.rank', 'path', 'node']
    input_dataframe = pd.DataFrame(data=input_data, columns=input_columns)
    input_dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    input_graphframe = GraphFrame()
    input_graphframe.dataframe = input_dataframe
    input_graphframe.graph = input_graph

    # expected graphframe output
    expected_nodes = [Node(callpath_tuple=None, parent=None) for _ in range(3)]
    expected_nodes[0].callpath = ('foo',)
    expected_nodes[0].parent = None
    expected_nodes[0].children = [expected_nodes[1], expected_nodes[2]]
    expected_nodes[1].callpath = ('foo', 'a')
    expected_nodes[1].parent = expected_nodes[0]
    expected_nodes[1].children = []
    expected_nodes[2].callpath = ('foo', 'b')
    expected_nodes[2].parent = expected_nodes[0]
    expected_nodes[2].children = []
    expected_graph = Graph(roots=None)
    expected_graph.roots = [expected_nodes[0]]
    expected_data = [[19, 0, 'foo', expected_nodes[0]],
                     [27, 0, 'a', expected_nodes[1]],
                     [43, 0, 'foo', expected_nodes[0]],
                     [65, 0, 'a', expected_nodes[1]],
                     [17, 0, 'b', expected_nodes[2]]]
    expected_columns = ['count', 'mpi.rank', 'path', 'node']
    expected_dataframe = pd.DataFrame(data=expected_data,
                                      columns=expected_columns)
    expected_dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)
    expected_graphframe = GraphFrame()
    expected_graphframe.dataframe = expected_dataframe
    expected_graphframe.graph = expected_graph

    # computed graphframe output
    computed_graphframe = input_graphframe.graft()

    # test graphframe equalities
    assert computed_graphframe.dataframe.equals(expected_graphframe.dataframe)
    assert computed_graphframe.graph.roots == expected_graphframe.graph.roots
    for root_a, root_b in zip(computed_graphframe.graph.roots,
                              expected_graphframe.graph.roots):
        assert list(root_a.traverse()) == list(root_b.traverse())
