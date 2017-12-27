##############################################################################
# Copyright (c) 2017, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# Written by Abhinav Bhatele <bhatele@llnl.gov>.
# LLNL-CODE-741008. All rights reserved.
#
# This file is part of Hatchet. For details, see:
# https://github.com/LLNL/hatchet
# Please also read the LICENSE file for the MIT License notice.
##############################################################################


class CCNode:
    """ A node in the tree.
    """

    def __init__(self, _cct_id, _flat_id, _line, _metrics, _node_type, _name,
                 _src_file, _load_module=None):
        self.cct_id = _cct_id    # (i)d: unique identifier for cross referencing
        self.flat_id = _flat_id  # (s)tatic scope id
        self.line = _line        # (l)ine range: "beg-end" (inclusive range)
        self.metrics = _metrics  # (v)ma-range-set: "{[beg-end), [beg-end)...}"
        self.node_type = _node_type  # PF/Pr/L/C/S
        self.name = _name            # (n)ame: string or id in ProcedureTable
        self.src_file = _src_file    # (f)ile name: string or id in FileTable

        # not all nodes have a (lm) load module: string or id in LoadModuleTable
        self.load_module = _load_module

        self.children = []

    def add_child(self, node):
        """ Adds a child to this node.
        """
        assert isinstance(node, CCNode)
        self.children.append(node)

    def __iter__(self):
        """Traverse the tree depth-first and yield each node.
        """
        for child in self.children:
            for item in child:
                yield item

        yield self
