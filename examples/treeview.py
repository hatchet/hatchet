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

#!/usr/bin/env python

from hatchet import *
import sys

import pandas as pd
pd.set_option('display.width', 500)
pd.set_option('display.max_colwidth', 30)


if __name__ == "__main__":
    dirname = sys.argv[1]

    gf = GraphFrame()
    gf.from_hpctoolkit(dirname)

    grouped_df = gf.dataframe.groupby('module')
    for key, item in grouped_df:
        print grouped_df.get_group(key), "\n\n"

    print gf.graph.to_string(gf.graph.roots, gf.dataframe, threshold=0.0)
