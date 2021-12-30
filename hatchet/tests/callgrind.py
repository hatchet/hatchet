# Copyright 2017-2021 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import numpy as np

from hatchet import GraphFrame
from hatchet.readers.gprof_dot_reader import GprofDotReader
from hatchet.external.console import ConsoleRenderer

roots = [
    "psm_no_lock",
    "(below main)",
    "0x0000000000000ff0",
    "_dl_catch_error'2",
    "hwloc_topology_load",
    "ibv_get_device_list",
    "psm_allocate_vbufs",
]


def test_graphframe(calc_pi_callgrind_dot):
    """Sanity test a GraphFrame object with known data."""
    gf = GraphFrame.from_gprof_dot(str(calc_pi_callgrind_dot))

    assert len(gf.dataframe.groupby("name")) == 105

    for col in gf.dataframe.columns:
        if col in ("time (inc)", "time"):
            assert gf.dataframe[col].dtype == np.float64
        elif col in ("name", "module", "node"):
            assert gf.dataframe[col].dtype == np.object

    # TODO: add tests to confirm values in dataframe


def test_read_calc_pi_database(calc_pi_callgrind_dot):
    """Sanity check the GprofDot reader by examining a known input."""
    reader = GprofDotReader(str(calc_pi_callgrind_dot))

    list_roots = reader.create_graph()
    root_names = []
    for root in list_roots:
        root_names.append(root.frame.attrs["name"])

    assert all(rt in root_names for rt in roots)


def test_tree(calc_pi_callgrind_dot):
    gf = GraphFrame.from_gprof_dot(str(calc_pi_callgrind_dot))

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
        colormap="RdYlGn",
        invert_colormap=False,
    )

    assert "0.580 MPIR_Request_complete" in output
    assert "1.400 malloc_consolidate" in output
    assert "0.080 MPIR_Reduce_impl" in output
