##############################################################################
# Copyright (c) 2018, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# Written by Matthew Kotila <kotila1@llnl.gov>.
# LLNL-CODE-741008. All rights reserved.
#
# This file is part of Hatchet. For details, see:
# https://github.com/LLNL/hatchet
# Please also read the LICENSE file for the MIT License notice.
##############################################################################

import pandas as pd
from hatchet import GraphFrame, CaliperReader


def num_nodes(root):
    count = 1
    for child in root.children:
        count = count + num_nodes(child)
    return count


def tree_height(root):
    if len(root.children) == 0:
        return 0
    height = 0
    for child in root.children:
        child_height = tree_height(child)
        if child_height > height:
            height = child_height
    return 1 + height


def test_graphframe(calc_pi_cali_db):
    """Sanity test a GraphFrame object with known data."""

    gf = GraphFrame()
    gf.from_caliper(str(calc_pi_cali_db))

    assert num_nodes(gf.root) == 34
    assert tree_height(gf.root) == 19


def test_dataframe(calc_pi_cali_db):
    """Sanity test a pandas.DataFrame object with known data."""

    (_, dataframe) = CaliperReader(str(calc_pi_cali_db)).create_graph()

    assert isinstance(dataframe, pd.DataFrame)
    assert len(dataframe.groupby('source.line#cali.sampler.pc')) == 7
    assert len(dataframe.groupby('source.file#cali.sampler.pc')) == 7
    assert len(dataframe.groupby('source.function#callpath.address')) == 8
