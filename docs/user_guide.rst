.. Copyright 2017-2019 Lawrence Livermore National Security, LLC and other
   Hatchet Project Developers. See the top-level LICENSE file for details.

   SPDX-License-Identifier: MIT

User Guide
==========

Hatchet is a Python tool that simplifies the process of analyzing hierarchical
performance data such as calling context trees. Hatchet uses pandas dataframes
to store the data on each node of the hierarchy and keeps the graph
relationships between the nodes in a different data structure that is kept
consistent with the dataframe.

Hatchet Data Structures
-----------------------

Hatchet's primary data structure is a ``GraphFrame``, which combines a
structured index in the form of a graph, and a Python pandas dataframe. We
explain these data structures in further detail in the following subsections.

Graphframe
^^^^^^^^^^

``Graphframe`` is the main data structure in Hatchet that stores the
performance data that is read in from an HPCToolkit database, Caliper Json or
Cali file, or gprof/callgrind DOT file. Typically, the raw input data is in the
form of a tree. However, since subsequent operations on the tree can lead to
new edges being created which can turn the tree into a graph, we store the
input data as a directed graph. The graphframe consists of a graph object that
stores the edge relationships between nodes and a dataframe that stores
different metrics (numerical data) and categorical data associated with each
node.

Graph
^^^^^

The graph can be connected or disconnected (multiple roots) and each node in
the graph can have one or more parents and children. The node stores its
frame, which can be defined by the reader. The callpath is derived by
appending the frames from the root to a given node.

Dataframe
^^^^^^^^^

The dataframe holds all the numerical and categorical data associated with each
node. Since typically the call tree data is per process, a multiindex composed
of the node and MPI rank is used to index into the dataframe.

Hatchet Operations
------------------

Dataframe Operations
^^^^^^^^^^^^^^^^^^^^

**Filter**: ``filter`` takes a user-supplied function and applies that
to all rows in the DataFrame. The resulting Series or DataFrame is used to
filter the DataFrame to only return rows that are true. The returned GraphFrame
preserves the original graph provided as input to the filter operation.

Filter is one of the operations that leads to the graph object and DataFrame
object becoming inconsistent. After a filter operation, there are nodes in the
graph that do not return any rows when used to index into the DataFrame.
Typically, the user will perform a squash on the GraphFrame after a filter
operation to make the graph and DataFrame objects consistent again.

**drop_index_levels**: When there is per-MPI process or per-thread
data in the DataFrame, a user might be interested in aggregating the data in
some fashion to analyze the graph at a coarser granularity. This function
allows the user to drop the additional index columns in the hierarchical index
by specifying an aggregation function. Essentially, this performs a
``groupby`` and ``aggregate`` operation on the DataFrame. The user-supplied
function is used to perform the aggregation over all MPI processes or threads
at the per-node granularity.

**update_inclusive_columns**: When a graph is rewired (i.e., the
parent-child connections are modified), all the columns in the DataFrame that
store inclusive values of a metric become inaccurate. This function performs a
post-order traversal of the graph to update all columns that store inclusive
metrics in the DataFrame for each node.

Graph Operations
^^^^^^^^^^^^^^^^

**Squash**: The ``squash`` operation is typically performed by the user after a
``filter`` operation on the DataFrame.  The squash operation removes nodes from
the graph that were previously removed from the DataFrame due to a filter
operation. When one or more nodes on a path are removed from the graph, the
nearest remaining ancestor is connected by an edge to the nearest remaining
child on the path. All call paths in the graph are re-wired in this manner.

A squash operation creates a new DataFrame in addition to the new graph. The
new DataFrame contains all rows from the original DataFrame, but its index
points to nodes in the new graph. Additionally, a squash operation will make
the values in all columns containing inclusive metrics inaccurate, since the
parent-child relationships have changed. Hence, the squash operation also calls
``update_inclusive_columns`` to make all inclusive columns in the DataFrame
accurate again.

**Equal**: The ``==`` operation checks whether two graphs have the same nodes
and edge connectivity when traversing from their roots.  If they are
equivalent, it returns true, otherwise it returns false.

**Union**: The ``union`` function takes two graphs and creates a unified graph,
preserving all edges structure of the original graphs, and merging nodes with
identical context.  When Hatchet performs binary operations on two GraphFrames
with unequal graphs, a union is performed beforehand to ensure that the graphs
are structurally equivalent.  This ensures that operands to element-wise
operations like add and subtract, can be aligned by their respective nodes.

**Tree**: The ``tree`` operation returns the graphframe's graph structure as a
string that can be printed to the console. By default, the tree uses the
``name`` of each node and the associated ``time`` metric as the string
representation. This operation uses automatic color by default, but True or
False can be used to force override.

GraphFrame Operations
^^^^^^^^^^^^^^^^^^^^^

**Copy**: The ``copy`` operation returns a shallow copy of a GraphFrame.  It
creates a new GraphFrame with a copy of the original GraphFrame's DataFrame,
but the same graph.  As mentioned earlier, graphs in Hatchet use immutable
semantics, and they are copied only when they need to be restructured.  This
property allows us to reuse graphs from GraphFrame to GraphFrame if the
operations performed on the GraphFrame do not mutate the graph.

**DeepCopy**: The ``deepcopy`` operation returns a deep copy of a GraphFrame.
It is similar to ``copy``, but returns a new GraphFrame with a copy of the
original GraphFrame's DataFrame and a copy of the original GraphFrame's graph.

**Unify**: ``unify`` operates on GraphFrames, and calls union on the two
graphs, and then reindexes the DataFrames in both GraphFrames to be indexed by
the nodes in the unified graph.  Binary operations on GraphFrames call unify
which in turn calls union on the respective graphs.

**Add**: Assuming the graphs in two GraphFrames are equal, the ``add (+)``
operation computes the element-wise sum of two DataFrames.  In the case where
the two graphs are not identical, ``unify`` (described above) is applied first
to create a unified graph before performing the sum.  The DataFrames are copied
and reindexed by the combined graph, and the add operation returns new
GraphFrame with the result of adding these DataFrames. Hatchet also provides an
in-place version of the add operator: ``+=``.

**Subtract**:  The subtract operation is similar to the add operation in that
it requires the two graphs to be identical.  It applies ``union`` and reindexes
DataFrames if necessary.  Once the graphs are unified, the subtract operation
computes the element-wise difference between the two DataFrames.  The subtract
operation returns a new GraphFrame, or it modifies one of the GraphFrames in
place in the case of the in-place subtraction (``-=``).
