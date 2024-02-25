# Copyright 2024 University of Maryland and other Hatchet Project Developers.
# See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import numpy as np

from hatchet import GraphFrame
from hatchet.readers.gprof_dot_reader import GprofDotReader

roots = ["20", "37", "38", "48", "49", "51"]


def test_graphframe(gprof_dot):
    """Sanity test a GraphFrame object with known data."""
    gf = GraphFrame.from_gprof_dot(str(gprof_dot))

    assert len(gf.dataframe.groupby("name")) == 44

    for col in gf.dataframe.columns:
        if col in ("time (inc)", "time"):
            assert gf.dataframe[col].dtype == np.float64
        elif col in ("name", "module", "node"):
            assert gf.dataframe[col].dtype == object

        if col == "module":
            assert (gf.dataframe[col].isna()).all()

    # TODO: add tests to confirm values in dataframe


def test_read_gprof_dot_sample_data(gprof_dot):
    """Sanity check the GprofDot reader by examining a known input."""
    reader = GprofDotReader(str(gprof_dot))

    list_roots = reader.create_graph()
    root_names = []
    for root in list_roots:
        root_names.append(root.frame.attrs["name"])

    assert all(rt in root_names for rt in roots), root_names
