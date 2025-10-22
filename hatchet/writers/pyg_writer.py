# Copyright 2024-2025 University of Maryland and other Hatchet Project
# Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT


class PyGWriter:
    """Create PyTorch Geometric Data graph object from a GraphFrame.

    Creates a node for each nid in the GraphFrame. Uses an encoding of the
    node name as the value for each node. Also includes metric values in the
    encoding.
    """

    def __init__(self):
        pass

    def _build_node_representation(self, node, metric_columns, dataframe, encoder):
        embedding = dataframe.loc[node, metric_columns].values.tolist()
        if encoder:
            name = dataframe.loc[node, "name"]
            encoding = encoder(name)
            embedding.extend(encoding)
        return embedding

    def _build_graph(
        self, node, visited, nodes, edges, metric_columns, dataframe, encoder
    ):
        node_id = node._hatchet_nid

        embedding = self._build_node_representation(
            node, metric_columns, dataframe, encoder
        )
        nodes[node_id] = embedding

        visited.append(node)
        for child in node.children:
            child_id = child._hatchet_nid
            if child not in visited:
                self._build_graph(
                    child, visited, nodes, edges, metric_columns, dataframe, encoder
                )
            edges.append((node_id, child_id))

    def write(self, gf, metrics=["time", "time (inc)"], encoder=None, **kwargs):
        """Return a PyG Data object from a GraphFrame."""
        import torch
        from torch_geometric.data import Data

        gf = gf.deepcopy()

        if any([metric not in gf.dataframe.columns for metric in metrics]):
            raise ValueError(
                f"Some metrics in {metrics} are missing from the dataframe."
            )

        # check if 'rank' or 'thread' are in the index
        if "rank" in gf.dataframe.index.names or "thread" in gf.dataframe.index.names:
            # TODO -- add support for rank and thread
            raise ValueError(
                "PyGWriter does not support 'rank' or 'thread' in the index."
            )

        # assert that if encoder is not None/False, then it must be callable
        if encoder and not callable(encoder):
            raise ValueError("encoder must be callable")

        nodes = [None] * len(gf.dataframe)
        edges = []
        weights = None  # TODO -- use call information to weight edges

        visited = []
        for root in gf.graph.roots:
            self._build_graph(
                root, visited, nodes, edges, metrics, gf.dataframe, encoder
            )

        nodes = torch.tensor(nodes, dtype=torch.float)
        edges = torch.tensor(edges, dtype=torch.long).t().contiguous()
        return Data(x=nodes, edge_index=edges, edge_attr=weights)
