#!/usr/bin/env python
##############################################################################
# Copyright (c) 2017-2018, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# This file is part of Hatchet.
# Created by Abhinav Bhatele <bhatele@llnl.gov>.
# LLNL-CODE-741008. All rights reserved.
#
# For details, see: https://github.com/LLNL/hatchet
# Please also read the LICENSE file for the MIT License notice.
##############################################################################

from __future__ import print_function

import pandas as pd

import hatchet as ht

pd.set_option("display.width", 500)
pd.set_option("display.max_colwidth", 30)


if __name__ == "__main__":
    gf = ht.GraphFrame()
    gf.from_gprof_dot("hatchet/tests/data/gprof2dot-cpi/callgrind.dot.64042.0.1")

    print(gf.dataframe)
    print("\n")

    print(gf.graph.to_string(gf.graph.roots, gf.dataframe, threshold=0.0))
