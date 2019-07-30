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

from hatchet import GraphFrame


def test_filter(mock_graph_literal):
    """Test the filter operation with a foo-bar tree."""

    gf = GraphFrame()
    gf.from_literal(mock_graph_literal)

    filtered_gf = gf.filter(lambda x: x["time"] > 5.0)
    assert len(filtered_gf.dataframe) == 9
