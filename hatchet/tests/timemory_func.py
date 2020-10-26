# Copyright 2017-2020 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import numpy as np
from timemory.profiler import Profiler
from timemory.trace import Tracer
from timemory.component import WallClock, CpuClock

components = [WallClock.id(), CpuClock.id()]
ncnt = 0


def eval_func(arr, tol):
    """Dummy tolerance-checking function for profiling which introduces some arbitrary branching"""
    global ncnt
    max = np.max(arr)
    if ncnt % 3 != 0:
        avg = np.mean(arr)
    else:
        avg = max
    ncnt = ncnt + 1
    return True if avg < tol and max < tol else False


@Profiler(components)
def prof_func(arr, tol):
    """Dummy function for profiling"""
    while not eval_func(arr, tol):
        arr = arr - np.power(arr, 3)


@Tracer(components)
def trace_func(arr, tol):
    """Dummy function for tracing"""
    while not eval_func(arr, tol):
        arr = arr - np.power(arr, 3)
