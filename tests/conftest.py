##############################################################################
# Copyright (c) 2017, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# Written by Abhinav Bhatele <bhatele@llnl.gov>.
# LLNL-CODE-741008. All rights reserved.
#
# This file is part of Hatchet. For details, see:
# https://github.com/LLNL/hatchet
# Please also read the LICENSE file for the MIT License notice.
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
        parent (str): parent (database) directory for metric DB
        name (str): name of the experiment (e.g., lulesh2.0)
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
def calc_pi_hpct_db(data_dir, tmpdir):
    """Builds a temporary directory containing the calc-pi database."""
    hpct_db_dir = os.path.join(data_dir, 'hpctoolkit-cpi-database')

    for f in glob(os.path.join(str(hpct_db_dir), '*.metric-db')):
        shutil.copy(f, str(tmpdir))
    shutil.copy(os.path.join(hpct_db_dir, 'experiment.xml'), str(tmpdir))

    return tmpdir


@pytest.fixture
def calc_pi_cali_db(data_dir, tmpdir):
    """Builds a temporary directory containing the calc-pi database."""
    cali_db_dir = os.path.join(data_dir, 'caliper-cpi-json')
    cali_db_file = os.path.join(cali_db_dir, 'cpi-sample-callpathprofile.json')

    shutil.copy(cali_db_file, str(tmpdir))
    tmpfile = os.path.join(str(tmpdir), 'cpi-sample-callpathprofile.json')

    return tmpfile
