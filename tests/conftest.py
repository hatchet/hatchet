##############################################################################
# Copyright (c) 2017, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# Written by:
#     Abhinav Bhatele <bhatele@llnl.gov>
#
# LLNL-CODE-XXXXXX. All rights reserved.
##############################################################################
import os
import shutil
import struct
from glob import glob

import pytest
import numpy as np


@pytest.fixture
def data_dir():
    """Return path to the top-level data directory for tests."""
    parent = os.path.dirname(__file__)
    return os.path.join(parent, 'data')


def make_mock_metric_db(parent, name, nprocs, nnodes, nthreads=1,
                        nmetrics=2, values=[0.0, 1.0]):
    """Create a set of mocked-up metric DB files.

    Args:
        parent (str): parent (experiment) directory for metric DB
        name (str): name of the experiemnt (e.g., lulesh2.0)
        nprocs (int): number of processes in the fake experiment
        nthreads (int): number of threads per process
        nmetrics (int): number of metrics in the metric DB
        values (list): list of float values to fill in for metric values
            on nodes

    Creates a set of ``nprocs`` x ``nthreads`` metric DB files under
    ``parent``.
    """
    if len(values) != nmetrics:
        raise ValueError('values must have length equal to nmetrics')

    # TODO: implement threads correctly.  For now, fail for threaded runs.
    assert nthreads == 1

    for p, t in np.ndindex(nprocs, nthreads):
        # TODO: generate pid and other identifiers in the filename, as well
        filename = "1.%s-%06d-%03d-a8c00270-160795-0.metric-db" % (name, p, t)
        path = os.path.join(parent, filename)

        with open(path, 'wb') as f:
            f.write('HPCPROF-metricdb')  # 16 bytes
            f.write('__00.10')           # 2 bytes + 5 byte version
            f.write('b')                 # 1 byte endian

            # TODO: is this really padding or is there more to
            # TODO: the format?
            f.write(8 * '\0')            # 8 bytes padding

            # write dummy values into file
            for n, m in np.ndindex(nnodes, nmetrics):
                f.write(struct.pack('>f8', values[m]))


@pytest.fixture
def lulesh_experiment_dir(data_dir, tmpdir):
    """Builds a temporary directory containing LULESH experiment data."""
    exp_dir = os.path.join(data_dir, 'lulesh-experiment')

    make_mock_metric_db(str(tmpdir), 'lulesh2.0', 8, 1643)
    shutil.copy(os.path.join(exp_dir, 'experiment.xml'), str(tmpdir))

    return tmpdir
