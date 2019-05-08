#!/usr/bin/env python
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

from __future__ import print_function
from hatchet import *
import sys
import pandas as pd

pd.set_option('display.width', 500)
pd.set_option('display.max_colwidth', 30)


if __name__ == "__main__":
    dirname = 'tests/data/hpctoolkit-cpi-database'

    gf = GraphFrame()
    gf.from_hpctoolkit(dirname)

    print(gf.dataframe.xs(0, level='rank'))
    print("\n")

    print(gf.graph.to_string(gf.graph.roots, gf.dataframe))
