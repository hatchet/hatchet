##############################################################################
# Copyright (c) 2017-2019, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# This file is part of Hatchet.
# Created by Abhinav Bhatele <bhatele@llnl.gov>.
# LLNL-CODE-741008. All rights reserved.
#
# For details, see: https://github.com/LLNL/hatchet
# Please also read the LICENSE file for the MIT License notice.
##############################################################################
from functools import total_ordering


class FrameID:
    """ The frame ID for a node. The node only stores its frame.
    """

    def __init__(self, fields_tuple):
        self.fields = {"function": None, "statement": None, "line number": None, "filename": None, "module": None}
        self.curr_fields = tuple(sorted(fields_tuple))

    def __eq__(self, other):
        return (self.nid == other.nid)

    def __lt__(self, other):
        return (self.callpath < other.callpath)

     #dep_tuple = tuple((d.spec.name, hash(d.spec), tuple(sorted(d.deptypes))) for name, d in sorted(self._dependencies.items()))
