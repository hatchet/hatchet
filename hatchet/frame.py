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
import sys

from functools import total_ordering
from .util.lang import memoized


@total_ordering
class Frame:
    """ The frame index for a node. The node only stores its frame.

        Args:
            attrs (dict): Dictionary of attributes and values.
            index_attrs (list): List of index attributes.
    """

    def __init__(self, attrs_dict, index_list):
        # Check that all index attributes are in attribute dictionary
        if not all(k in attrs_dict for k in index_list):
            raise KeyError("Invalid index attribute(s)")

        self.attrs = attrs_dict
        self.index_attrs = index_list

    def __eq__(self, other):
        return (self._cmp_key() == other._cmp_key())

    def __lt__(self, other):
        return (self._cmp_key() < other._cmp_key())

    def __gt__(self, other):
        return (self._cmp_key() > other._cmp_key())

    def __str__(self):
        ret = {}
        for i in self.index_attrs:
            if i in self.attrs:
                ret[i] = self.attrs[i]
        return str(ret)

    @memoized
    def _cmp_key(self):
        """ Make a tuple of attributes and values based on reader
        """
        return tuple((k, self.attrs[k]) for k in sorted(self.index_attrs))
