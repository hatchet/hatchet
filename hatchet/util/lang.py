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
import functools

def memoized(func):
    """Decorator that caches the results of a function, storing them in
    an attribute of that function.
    """
    func.cache = {}

    @functools.wraps(func)
    def _memoized_function(*args):
        if not isinstance(args, collections.Hashable):
            # Not hashable, so just call the function.
            return func(*args)

        if args not in func.cache:
            func.cache[args] = func(*args)

        return func.cache[args]

    return _memoized_function
