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


@total_ordering
class Frame:
    """The frame index for a node. The node only stores its frame.

    Args:
       attrs (dict): Dictionary of attributes and values.
    """

    def __init__(self, attrs_dict):
        self.attrs = attrs_dict
        self._tuple_repr = None

    def __eq__(self, other):
        return self.tuple_repr == other.tuple_repr

    def __lt__(self, other):
        return self.tuple_repr < other.tuple_repr

    def __gt__(self, other):
        return self.tuple_repr > other.tuple_repr

    def __hash__(self):
        return hash(self.tuple_repr)

    def __str__(self):
        return str(self.attrs)

    @property
    def tuple_repr(self):
        """Make a tuple of attributes and values based on reader."""
        if not self._tuple_repr:
            self._tuple_repr = tuple((k, self.attrs[k]) for k in sorted(self.attrs))
        return self._tuple_repr
