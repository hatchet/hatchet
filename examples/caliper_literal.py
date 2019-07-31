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
import subprocess

pd.set_option("display.width", 1500)
pd.set_option("display.max_colwidth", 20)
pd.set_option("display.max_rows", None)


if __name__ == "__main__":
    cali_file = "hatchet/tests/data/caliper-cali/caliper-ex.cali"

    cali_query = "/usr/gapps/spot/caliper/bin/cali-query"
    grouping_attribute = "function"
    default_metric = "sum(sum#time.duration),inclusive_sum(sum#time.duration)"
    query = "select function,%s group by %s format json-split" % (
        default_metric,
        grouping_attribute,
    )

    gf = GraphFrame()

    if sys.version_info >= (3, 0, 0):
        cali_json = subprocess.run(
            [cali_query, "-q", query, cali_file],
            check=True,
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )
        gf.from_caliper(cali_json.stdout, "literal")
    else:
        cali_json = subprocess.check_output(
            [cali_query, "-q", query, cali_file], universal_newlines=True
        )
        gf.from_caliper(cali_json, "literal")

    print(gf.dataframe)
    print("\n")

    print(gf.graph.to_string(gf.graph.roots, gf.dataframe))
