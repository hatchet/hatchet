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

    def __init__(self, attrs=None, **kwargs):
        """Construt a frame from a dictionary, or from immediate kwargs.

        Arguments:
            attrs (dict, optional): dictionary of attributes for this
                Frame.

        Keyword arguments are optional, but if they are provided, they
        will be used to update the dictionary.  Keys in kwargs take
        precedence over anything in the attrs dictionary.

        So, these are all functionally equivalent::

            Frame({"name": "foo", "file": "bar.c"})
            Frame(name="foo", file="bar.c")
            Frame({"name": "foo"}, file="bar.c")
            Frame({"name": "foo", "file": "baz.h"}, file="bar.c")

        """
        # attributes dictionary
        self.attrs = attrs if attrs else {}

        # add keyword arguments, if any.
        if kwargs:
            self.attrs.update(kwargs)

        if not self.attrs:
            raise ValueError("Frame must be constructed with attributes!")

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

    def copy(self):
        return Frame(self.attrs.copy())

    def __getitem__(self, name):
        return self.attrs[name]

    def get(self, name, default=None):
        return self.attrs.get(name, default)

    def values(self, names):
        """Return a tuple of attribute values from this Frame."""
        if isinstance(names, (list, tuple)):
            return tuple(self.attrs.get(name) for name in names)
        else:
            return self.attrs.get(names)
