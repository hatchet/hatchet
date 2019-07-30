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


def test_graph_equal(mock_graph_literal):
    gf = GraphFrame()
    gf.from_literal(mock_graph_literal)

    other = GraphFrame()
    other.from_literal(mock_graph_literal)

    assert gf.graph == other.graph


def test_graph_not_equal(mock_graph_literal, calc_pi_hpct_db):
    gf = GraphFrame()
    gf.from_literal(mock_graph_literal)

    other = GraphFrame()
    other.from_hpctoolkit(str(calc_pi_hpct_db))

    assert gf.graph != other.graph


def test_dag_not_equal(mock_dag_literal1, mock_dag_literal2):
    gf = GraphFrame()
    gf.from_literal(mock_dag_literal1)

    other = GraphFrame()
    other.from_literal(mock_dag_literal2)

    assert gf.graph != other.graph
