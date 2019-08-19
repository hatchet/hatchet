##############################################################################
# Copyright (c) 2019, University of Maryland.
#
# This file is part of Hatchet.
# Created by Abhinav Bhatele <bhatele@cs.umd.edu>.
# LLNL-CODE-741008. All rights reserved.
#
# For details, see: https://github.com/LLNL/hatchet
# Please also read the LICENSE file for the MIT License notice.
##############################################################################

from hatchet import GraphFrame


def test_copy(mock_graph_literal):
    gf = GraphFrame()
    gf.from_literal(mock_graph_literal)

    other = gf.copy()

    assert gf.graph == other.graph

