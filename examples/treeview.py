##############################################################################
# Copyright (c) 2017, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# Written by Abhinav Bhatele <bhatele@llnl.gov>.
# LLNL-CODE-741008. All rights reserved.
#
# This file is part of Hatchet. For details, see:
# https://github.com/LLNL/hatchet
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

    cct = CCTree()
    cct.from_hpctoolkit(dirname)

    grouped_df = cct.treeframe.groupby('module')
    for key, item in grouped_df:
        print grouped_df.get_group(key), "\n\n"

    print cct.tree_as_text(cct.root, threshold=0.0)
