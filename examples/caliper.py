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
from hatchet import *
import sys
import pandas as pd

pd.set_option('display.width', 1500)
pd.set_option('display.max_colwidth', 20)
pd.set_option('display.max_rows', None)


if __name__ == "__main__":
    filename = 'tests/data/caliper-lulesh-json/lulesh-sample-annotation-profile.json'

    gf = GraphFrame()
    gf.from_caliper(filename)

    print(gf.dataframe)
    print("\n")

    print(gf.graph.to_string(gf.graph.roots, gf.dataframe))
    with open("test.dot", "w") as fileh:
        fileh.write(gf.graph.to_dot(gf.graph.roots, gf.dataframe))
