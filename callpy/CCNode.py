#!/usr/bin/env python

##############################################################################
# Copyright (c) 2017, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# Written by:
#     Abhinav Bhatele <bhatele@llnl.gov>
#
# LLNL-CODE-XXXXXX. All rights reserved.
##############################################################################

class CCNode:

    def __init__(self, id, sid, line, val, name=None, loadm=None, filen=None):
        self.id = id        # (i)d: unique identifier for cross referencing
        self.sid = sid      # (s)tatic scope id
        self.line = line    # (l)ine range: "beg-end" (inclusive range)
        self.val = val      # (v)ma-range-set: "{[beg-end), [beg-end)...}"

        # not all nodes have this information
        self.name = name    # (n)ame: a string or an id in ProcedureTable
        self.loadm = loadm  # (lm) load module: string or id in LoadModuleTable
        self.filen = filen  # (f)ile name: string or id in FileTable

        self.children = []


    # add a child to this node
    def add_child(self, node):
        assert isinstance(node, CCNode)
        self.children.append(node)

