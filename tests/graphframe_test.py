

def test_graft():
    """Sanity test GraphFrame.graft()."""
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
    data = [[23, 0, 'MPI_Send', nodes[1]],
            [8236, 0, 'descendant_a', nodes[2]],
            [131, 0, 'descendant_b', nodes[3]],
            [None, None, 'MPI_Recv', nodes[4]],
            [None, None, 'descendant_a', nodes[5]],
            [4452, 0, 'descendant_a_a', nodes[6]]]
    columns = ['count', 'mpi.rank', 'path', 'node']
    dataframe = pd.DataFrame(data=data, columns=columns)
    dataframe.set_index(['node', 'mpi.rank'], drop=False, inplace=True)

    # hard-coded graphframe
    graphframe = GraphFrame()
    graphframe.dataframe = dataframe
    graphframe.graph = graph

    # graft the pre-filtered graphframe
    result = graphframe.graft()

    # update original graph to (hopefully) match result
    for node in nodes[1:]:
        node.callpath = node.callpath[1:]

    # hard-coded result graph roots
    result_roots = [nodes[4], nodes[1]]

    # test graph equalities
    for root_a, root_b in zip(result.graph.roots, result_roots):
        for node_a, node_b in zip(root_a.traverse(), root_b.traverse()):
            assert node_a.callpath == node_b.callpath

    # test dataframe equalities
    assert result.dataframe.equals(dataframe)
