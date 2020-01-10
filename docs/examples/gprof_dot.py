#!/usr/bin/env python
#
# Copyright 2017-2020 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from __future__ import print_function

import hatchet as ht


if __name__ == "__main__":
    gf = ht.GraphFrame.from_gprof_dot(
        "../../hatchet/tests/data/gprof2dot-cpi/callgrind.dot.64042.0.1"
    )

    print(gf.dataframe)
    print("\n")

    print(gf.tree(threshold=0.0))
