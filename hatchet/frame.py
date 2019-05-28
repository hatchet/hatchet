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
import sys


@total_ordering
class FrameIndex:
    """ The frame index for a node. The node only stores its frame.
    """

    def __init__(self, attrs_dict, attrs_list):
        """ Maybe this function could just take a dict and create the list
            based on values that have been modified (i.e., not None).
        """
        self.attrs = {
            "function" : None,
            "statement": None,
            "linenum"  : None,
            "filename" : None,
            "module"   : None
        }

        self.index_attrs = attrs_list

        # Modify attrs dict with appropriate values. If the reader specifies a
        # key not in the attrs dict, return an error.
        for k,v in attrs_dict.items():
            if k in self.attrs:
                self.attrs[k] = v
            else:
                print("\"" + k + "\"" + ": Invalid attribute")
                sys.exit()

    def __eq__(self, other):
        return (self.index_attrs == other.index_attrs)

    def __lt__(self, other):
        return (self.index_attrs < other.index_attrs)

    def make_frame(self):
        """ Make a tuple of attributes and values based on reader
        """
        return tuple((k, self.attrs[k]) for k in sorted(self.index_attrs))
