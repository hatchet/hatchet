# MIT License
#
# Copyright (c) 2018, The Regents of the University of California,
# through Lawrence Berkeley National Laboratory (subject to receipt of any
# required approvals from the U.S. Dept. of Energy).  All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import numpy as np

from hatchet import GraphFrame
from hatchet.external.console import ConsoleRenderer

import pytest

timemory_avail = True
try:
    import timemory
except ImportError:
    timemory_avail = False


@pytest.mark.skipif(not timemory_avail, reason="timemory package not available")
def test_graphframe(timemory_json_data):
    """Sanity test a GraphFrame object with known data."""
    import timemory
    from timemory.component import WallClock

    wc_s = WallClock.id()  # string identifier
    wc_v = WallClock.index()  # enumeration id
    gf = GraphFrame.from_timemory(timemory_json_data, [wc_s])

    assert len(gf.dataframe) == timemory.size([wc_v])[wc_v]

    for col in gf.dataframe.columns:
        if col in ("sum.inc", "sum"):
            assert gf.dataframe[col].dtype == np.float64
        elif col in ("nid", "rank"):
            assert gf.dataframe[col].dtype == np.int64
        elif col in ("name", "node"):
            assert gf.dataframe[col].dtype == np.object


@pytest.mark.skipif(not timemory_avail, reason="timemory package not available")
def test_tree(timemory_json_data):
    """Sanity test a GraphFrame object with known data."""

    gf = GraphFrame.from_timemory(timemory_json_data)

    print(gf.tree("sum"))

    output = ConsoleRenderer(unicode=True, color=False).render(
        gf.graph.roots,
        gf.dataframe,
        metric_column="sum",
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

    print(output)

    output = ConsoleRenderer(unicode=True, color=False).render(
        gf.graph.roots,
        gf.dataframe,
        metric_column="sum.inc",
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

    print(output)


@pytest.mark.skipif(not timemory_avail, reason="timemory package not available")
def test_graphframe_to_literal(timemory_json_data):
    """Sanity test a GraphFrame object with known data."""
    gf = GraphFrame.from_timemory(timemory_json_data)
    graph_literal = gf.to_literal()

    assert len(graph_literal) == len(gf.graph.roots)
