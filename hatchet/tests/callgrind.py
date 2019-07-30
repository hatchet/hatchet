# Copyright 2017-2019 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from hatchet import GraphFrame
from hatchet.readers.gprof_dot_reader import GprofDotReader

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
    gf = GraphFrame()
    gf.from_gprof_dot(str(calc_pi_callgrind_dot))

    assert len(gf.dataframe.groupby("name")) == 105

    # TODO: add tests for dataframe


def test_read_calc_pi_database(calc_pi_callgrind_dot):
    """Sanity check the GprofDot reader by examining a known input."""
    reader = GprofDotReader(str(calc_pi_callgrind_dot))

    list_roots = reader.create_graph()
    root_names = []
    for root in list_roots:
        root_names.append(root.frame.attrs["name"])

    assert all(rt in root_names for rt in roots)
