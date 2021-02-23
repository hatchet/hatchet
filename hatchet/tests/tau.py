# Copyright 2020 University of Maryland and other Hatchet Project
# Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import numpy as np

from hatchet import GraphFrame
from hatchet.external.console import ConsoleRenderer


def test_graphframe(tau_profile_dir):
    """Sanity test a GraphFrame object with known data."""
    gf = GraphFrame.from_tau(str(tau_profile_dir))

    for col in gf.dataframe.columns:
        if col in ("time (inc)", "time"):
            assert gf.dataframe[col].dtype == np.float64
        elif col in ("thread"):
            assert gf.dataframe[col].dtype == np.int64
        elif col in ("name", "node"):
            assert gf.dataframe[col].dtype == np.object

    # TODO: add tests to confirm values in dataframe


def test_tree(tau_profile_dir):
    """Sanity test a GraphFrame object with known data."""
    gf = GraphFrame.from_tau(str(tau_profile_dir))

    output = ConsoleRenderer(unicode=True, color=False).render(
        gf.graph.roots,
        gf.dataframe,
        metric_column="time",
        precision=3,
        name_column="name",
        expand_name=False,
        context_column="",
        rank=0,
        thread=0,
        depth=10000,
        highlight_name=False,
        invert_colormap=False,
    )
    assert ".TAU application" in output
