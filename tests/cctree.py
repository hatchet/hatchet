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

modules = [
    '/g/g92/bhatele1/llnl/hpctoolkit/lulesh/lulesh2.0',
    '/collab/usr/global/tools/hpctoolkit/chaos_5_x86_64_ib/'
    'hpctoolkit-2017-03-16/lib/hpctoolkit/ext-libs/libmonitor.so.0.0.0',
    '/usr/local/tools/mvapich2-intel-debug-2.2/lib/libmpi.so.12.0.5',
    '/lib64/libc-2.12.so',
    '/usr/lib64/libpsm_infinipath.so.1.14',
    '/usr/lib64/libinfinipath.so.4.0']

sources = ['./src/g/g92/bhatele1/llnl/hpctoolkit/lulesh/lulesh-comm.cc',
           './src/g/g92/bhatele1/llnl/hpctoolkit/lulesh/lulesh.cc',
           './src/g/g92/bhatele1/llnl/hpctoolkit/lulesh/lulesh.h']

procedures = ['CalcMonotonicQForElems(Domain&, double*)',
              'ApplyMaterialPropertiesForElems(Domain&, double*)',
              'UpdateVolumesForElems(Domain&, double*, double, int)',
              'CalcTimeConstraintsForElems(Domain&)']


def test_tree(lulesh_experiment_dir):
    """Sanity test a CCTree object wtih known data."""

    tree = CCTree(str(lulesh_experiment_dir))

    assert len(tree.loadModules) == 6
    assert all(f in tree.loadModules.values() for f in modules)
    assert all(s in tree.files.values() for s in sources)
    assert all(p in tree.procedures.values() for p in procedures)

    # make sure every node has dummy data.
    for node in tree.traverse():
        assert node.metrics == [0.0, 1.0]

def test_read_lulesh_data(lulesh_experiment_dir):
    """Sanity check the reader by examining a known input."""
    dbr = HPCTDBReader(str(lulesh_experiment_dir))

    load_modules = [
        x.attrib['n'] for x in dbr.LoadModuleTable.iter('LoadModule')]
    file_names = [x.attrib['n'] for x in dbr.FileTable.iter('File')]
    procs = [x.attrib['n'] for x in dbr.ProcedureTable.iter('Procedure')]

    assert len(load_modules) == 6
    assert all(f in load_modules for f in modules)
    assert all(s in file_names for s in sources)
    assert all(p in procs for p in procedures)
