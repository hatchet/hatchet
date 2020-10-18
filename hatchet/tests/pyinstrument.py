# Copyright 2017-2020 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import numpy as np

from hatchet import GraphFrame
from hatchet.external.console import ConsoleRenderer


def test_graphframe(pyinstrument_json_file):
    gf = GraphFrame.from_pyinstrument(pyinstrument_json_file)

    assert len(gf.dataframe.groupby("name")) == 44

    gf.dataframe.reset_index(inplace=True)

    for col in gf.dataframe.columns:
        if col in ("time (inc)", "time"):
            assert gf.dataframe[col].dtype == np.float64
        elif col in ("line"):
            assert gf.dataframe[col].dtype == np.int64
        elif col in ("is_application_code"):
            assert gf.dataframe[col].dtype == bool
        elif col in ("name", "type", "file", "node"):
            assert gf.dataframe[col].dtype == np.object


def test_tree(pyinstrument_json_file):
    gf = GraphFrame.from_pyinstrument(pyinstrument_json_file)

    output = ConsoleRenderer(unicode=True, color=False).render(
        gf.graph.roots,
        gf.dataframe,
        metric_column="time",
        precision=3,
        name_column="name",
        expand_name=False,
        context_column="file",
        rank=0,
        thread=0,
        depth=10000,
        highlight_name=False,
        invert_colormap=False,
    )
    assert "0.000 <module> examples.py" in output
    assert "0.025 read hatchet/readers/caliper_reader.py" in output

    output = ConsoleRenderer(unicode=True, color=False).render(
        gf.graph.roots,
        gf.dataframe,
        metric_column="time (inc)",
        precision=3,
        name_column="name",
        expand_name=False,
        context_column="file",
        rank=0,
        thread=0,
        depth=10000,
        highlight_name=False,
        invert_colormap=False,
    )
    assert "0.478 <module> examples.py" in output
    assert "0.063 from_caliper_json hatchet/graphframe.py" in output


def test_graphframe_to_literal(pyinstrument_json_file):
    """Sanity test a GraphFrame object with known data."""
    gf = GraphFrame.from_pyinstrument(pyinstrument_json_file)
    graph_literal = gf.to_literal()

    assert len(graph_literal) == len(gf.graph.roots)
