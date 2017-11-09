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

    def __init__(self, cct_id, flat_id, line, metrics, node_type, name=None,
                 load_module=None, src_file=None):
        self.cct_id = cct_id    # (i)d: unique identifier for cross referencing
        self.flat_id = flat_id  # (s)tatic scope id
        self.line = line        # (l)ine range: "beg-end" (inclusive range)
        self.metrics = metrics  # (v)ma-range-set: "{[beg-end), [beg-end)...}"
        self.node_type = node_type  # PF/Pr/L/C/S

        # not all nodes have this information
        self.name = name          # (n)ame: a string or an id in ProcedureTable
        # (lm) load module: string or id in LoadModuleTable
        self.load_module = load_module
        self.src_file = src_file  # (f)ile name: string or id in FileTable

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

