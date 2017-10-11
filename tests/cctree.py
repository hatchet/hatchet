##############################################################################
# Copyright (c) 2017, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# Written by:
#     Abhinav Bhatele <bhatele@llnl.gov>
#
# LLNL-CODE-XXXXXX. All rights reserved.
##############################################################################
from hatchet import CCTree, HPCTDBReader

modules = ['cpi',
           '/collab/usr/global/tools/hpctoolkit/chaos_5_x86_64_ib/'
           'hpctoolkit-2017-03-16/lib/hpctoolkit/ext-libs/libmonitor.so.0.0.0',
           '/usr/local/tools/mvapich2-intel-debug-2.2/lib/libmpi.so.12.0.5',
           '/lib64/libc-2.12.so',
           '/usr/lib64/libpsm_infinipath.so.1.14']

src_files = ['./src/cpi.c',
             '<unknown file>',
             '/tmp/dpkg-mkdeb.gouoc49UG7/src/mvapich/src/build/../src/mpi/'
             'init/init.c',
             '/tmp/dpkg-mkdeb.gouoc49UG7/src/mvapich/src/build/../src/mpi/'
             'init/initthread.c',
             '/tmp/dpkg-mkdeb.gouoc49UG7/src/mvapich/src/build/../src/mpid/'
             'ch3/src/mpid_init.c',
             '/tmp/dpkg-mkdeb.gouoc49UG7/src/mvapich/src/build/../src/mpid/'
             'ch3/channels/psm/src/mpidi_calls.c',
             '/tmp/dpkg-mkdeb.gouoc49UG7/src/mvapich/src/build/../src/mpid/'
             'ch3/channels/psm/src/psm_entry.c',
             '/tmp/dpkg-mkdeb.gouoc49UG7/src/mvapich/src/build/../src/mpi/'
             'init/finalize.c',
             '/tmp/dpkg-mkdeb.gouoc49UG7/src/mvapich/src/build/../src/mpid/'
             'ch3/src/mpid_finalize.c',
             '/tmp/dpkg-mkdeb.gouoc49UG7/src/mvapich/src/build/../src/mpid/'
             'ch3/channels/psm/src/psm_exit.c',
             'interp.c',
             '<unknown file>']

procedures = ['main',
              '<program root>',
              'MPI_Init',
              'pthread_create',
              'MPI_Finalize',
              'PMPI_Init',
              'MPIR_Init_thread',
              'MPID_Init',
              'MPIDI_CH3_Init',
              'MPIDI_CH3_Finalize',
              'psm_doinit',
              'PMPI_Finalize',
              'MPID_Finalize',
              'psm_dofinalize',
              '__GI_sched_yield',
              '<unknown procedure>']


def test_cctree(calc_pi_hpct_db):
    """Sanity test a CCTree object wtih known data."""

    tree = CCTree(str(calc_pi_hpct_db))

    assert len(tree.loadModules) == 5
    assert len(tree.files) == 12
    assert len(tree.procedures) == 16
    assert all(lm in tree.loadModules.values() for lm in modules)
    assert all(sf in tree.files.values() for sf in src_files)
    assert all(pr in tree.procedures.values() for pr in procedures)

    # make sure every node has dummy data.
    # for node in tree.traverse():
    #    assert node.metrics == [0.0, 1.0]

def test_read_calc_pi_database(calc_pi_hpct_db):
    """Sanity check the HPCT database reader by examining a known input."""
    dbr = HPCTDBReader(str(calc_pi_hpct_db))

    dbr_modules = [
        x.attrib['n'] for x in dbr.LoadModuleTable.iter('LoadModule')]
    dbr_files = [x.attrib['n'] for x in dbr.FileTable.iter('File')]
    dbr_procs = [x.attrib['n'] for x in dbr.ProcedureTable.iter('Procedure')]

    assert len(dbr_modules) == 5
    assert len(dbr_files) == 12
    assert len(dbr_procs) == 16
    assert all(lm in dbr_modules for lm in modules)
    assert all(sf in dbr_files for sf in src_files)
    assert all(pr in dbr_procs for pr in procedures)
