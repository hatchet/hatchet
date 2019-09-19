# Copyright 2017-2019 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import numpy as np

from hatchet import GraphFrame
from hatchet.readers.hpctoolkit_reader import HPCToolkitReader

modules = [
    "cpi",
    "/collab/usr/global/tools/hpctoolkit/chaos_5_x86_64_ib/"
    "hpctoolkit-2017-03-16/lib/hpctoolkit/ext-libs/libmonitor.so.0.0.0",
    "/usr/local/tools/mvapich2-intel-debug-2.2/lib/libmpi.so.12.0.5",
    "/lib64/libc-2.12.so",
    "/usr/lib64/libpsm_infinipath.so.1.14",
]

src_files = [
    "./src/cpi.c",
    "<unknown file>",
    "/tmp/dpkg-mkdeb.gouoc49UG7/src/mvapich/src/build/../src/mpi/" "init/init.c",
    "/tmp/dpkg-mkdeb.gouoc49UG7/src/mvapich/src/build/../src/mpi/" "init/initthread.c",
    "/tmp/dpkg-mkdeb.gouoc49UG7/src/mvapich/src/build/../src/mpid/"
    "ch3/src/mpid_init.c",
    "/tmp/dpkg-mkdeb.gouoc49UG7/src/mvapich/src/build/../src/mpid/"
    "ch3/channels/psm/src/mpidi_calls.c",
    "/tmp/dpkg-mkdeb.gouoc49UG7/src/mvapich/src/build/../src/mpid/"
    "ch3/channels/psm/src/psm_entry.c",
    "/tmp/dpkg-mkdeb.gouoc49UG7/src/mvapich/src/build/../src/mpi/" "init/finalize.c",
    "/tmp/dpkg-mkdeb.gouoc49UG7/src/mvapich/src/build/../src/mpid/"
    "ch3/src/mpid_finalize.c",
    "/tmp/dpkg-mkdeb.gouoc49UG7/src/mvapich/src/build/../src/mpid/"
    "ch3/channels/psm/src/psm_exit.c",
    "interp.c",
    "<unknown file>",
]

procedures = [
    "main",
    "<program root>",
    "MPI_Init",
    "pthread_create",
    "MPI_Finalize",
    "PMPI_Init",
    "MPIR_Init_thread",
    "MPID_Init",
    "MPIDI_CH3_Init",
    "MPIDI_CH3_Finalize",
    "psm_doinit",
    "PMPI_Finalize",
    "MPID_Finalize",
    "psm_dofinalize",
    "__GI_sched_yield",
    "<unknown procedure>",
]


def test_graphframe(calc_pi_hpct_db):
    """Sanity test a GraphFrame object with known data."""
    gf = GraphFrame.from_hpctoolkit(str(calc_pi_hpct_db))

    assert len(gf.dataframe.groupby("module")) == 5
    assert len(gf.dataframe.groupby("file")) == 11
    assert len(gf.dataframe.groupby("name")) == 20

    for col in gf.dataframe.columns:
        if col in ("time (inc)", "time"):
            assert gf.dataframe[col].dtype == np.float64
        elif col in ("nid", "rank", "line"):
            assert gf.dataframe[col].dtype == np.int64
        elif col in ("name", "type", "file", "module", "node"):
            assert gf.dataframe[col].dtype == np.object

    # TODO: add tests to confirm values in dataframe


def test_read_calc_pi_database(calc_pi_hpct_db):
    """Sanity check the HPCT database reader by examining a known input."""
    reader = HPCToolkitReader(str(calc_pi_hpct_db))
    reader.fill_tables()

    assert len(reader.load_modules) == 5
    assert len(reader.src_files) == 12
    assert len(reader.procedure_names) == 16
    assert all(lm in reader.load_modules.values() for lm in modules)
    assert all(sf in reader.src_files.values() for sf in src_files)
    assert all(pr in reader.procedure_names.values() for pr in procedures)
