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


def test_drop_index_levels(calc_pi_hpct_db):
    gf = GraphFrame()
    gf.from_hpctoolkit(str(calc_pi_hpct_db))
    num_nodes = len(gf.graph)

    gf.drop_index_levels()
    num_rows = len(gf.dataframe.index)

    assert num_nodes == num_rows
