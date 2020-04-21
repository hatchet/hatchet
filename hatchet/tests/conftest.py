# Copyright 2017-2020 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

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
    return os.path.join(parent, "data")


def make_mock_metric_db(
    parent, name, nprocs, nnodes, nthreads=1, nmetrics=2, values=[0.0, 1.0]
):
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
        raise ValueError("values must have length equal to nmetrics")

    # TODO: implement threads correctly.  For now, fail for threaded runs.
    assert nthreads == 1

    for p, t in np.ndindex(nprocs, nthreads):
        # TODO: generate pid and other identifiers in the filename, as well
        filename = "1.%s-%06d-%03d-a8c00270-160795-0.metric-db" % (name, p, t)
        path = os.path.join(parent, filename)

        with open(path, "wb") as f:
            f.write("HPCPROF-metricdb")  # 16 bytes
            f.write("__00.10")  # 2 bytes + 5 byte version
            f.write("b")  # 1 byte endian

            # TODO: is this really padding or is there more to
            # TODO: the format?
            f.write(8 * "\0")  # 8 bytes padding

            # write dummy values into file
            for n, m in np.ndindex(nnodes, nmetrics):
                f.write(struct.pack(">f8", values[m]))


@pytest.fixture
def calc_pi_hpct_db(data_dir, tmpdir):
    """Builds a temporary directory containing the calc-pi database."""
    hpct_db_dir = os.path.join(data_dir, "hpctoolkit-cpi-database")

    for f in glob(os.path.join(str(hpct_db_dir), "*.metric-db")):
        shutil.copy(f, str(tmpdir))
    shutil.copy(os.path.join(hpct_db_dir, "experiment.xml"), str(tmpdir))

    return tmpdir


@pytest.fixture
def lulesh_caliper_json(data_dir, tmpdir):
    """Builds a temporary directory containing the lulesh JSON file."""
    cali_json_dir = os.path.join(data_dir, "caliper-lulesh-json")
    cali_json_file = os.path.join(
        cali_json_dir, "lulesh-sample-annotation-profile.json"
    )

    shutil.copy(cali_json_file, str(tmpdir))
    tmpfile = os.path.join(str(tmpdir), "lulesh-sample-annotation-profile.json")

    return tmpfile


@pytest.fixture
def sample_caliper_raw_cali(data_dir, tmpdir):
    """Builds a temporary directory containing the raw cali file."""
    cali_dir = os.path.join(data_dir, "caliper-cali")
    cali_file = os.path.join(cali_dir, "caliper-ex.cali")

    shutil.copy(cali_file, str(tmpdir))
    tmpfile = os.path.join(str(tmpdir), "caliper-ex.cali")

    return tmpfile


@pytest.fixture
def sample_caliper_json(data_dir, tmpdir):
    """Builds a temporary directory containing the sample cali-query JSON file."""
    cali_dir = os.path.join(data_dir, "caliper-cali")
    cali_file = os.path.join(cali_dir, "caliper-ex.json")

    shutil.copy(cali_file, str(tmpdir))
    tmpfile = os.path.join(str(tmpdir), "caliper-ex.json")

    return tmpfile


@pytest.fixture
def calc_pi_callgrind_dot(data_dir, tmpdir):
    """Builds a temporary directory containing the calc-pi callgrind DOT file."""
    gprof_dot_dir = os.path.join(data_dir, "gprof2dot-cpi")
    gprof_dot_file = os.path.join(gprof_dot_dir, "callgrind.dot.64042.0.1")

    shutil.copy(gprof_dot_file, str(tmpdir))
    tmpfile = os.path.join(str(tmpdir), "callgrind.dot.64042.0.1")

    return tmpfile


@pytest.fixture
def mock_graph_literal():
    """ Creates a mock tree

    Metasyntactic variables: https://www.ietf.org/rfc/rfc3092.txt
    """
    graph_dict = [
        {
            "name": "foo",
            "metrics": {"time (inc)": 130.0, "time": 0.0},
            "children": [
                {
                    "name": "bar",
                    "metrics": {"time (inc)": 20.0, "time": 5.0},
                    "children": [
                        {"name": "baz", "metrics": {"time (inc)": 5.0, "time": 5.0}},
                        {
                            "name": "grault",
                            "metrics": {"time (inc)": 10.0, "time": 10.0},
                        },
                    ],
                },
                {
                    "name": "qux",
                    "metrics": {"time (inc)": 60.0, "time": 0.0},
                    "children": [
                        {
                            "name": "quux",
                            "metrics": {"time (inc)": 60.0, "time": 5.0},
                            "children": [
                                {
                                    "name": "corge",
                                    "metrics": {"time (inc)": 55.0, "time": 10.0},
                                    "children": [
                                        {
                                            "name": "bar",
                                            "metrics": {
                                                "time (inc)": 20.0,
                                                "time": 5.0,
                                            },
                                            "children": [
                                                {
                                                    "name": "baz",
                                                    "metrics": {
                                                        "time (inc)": 5.0,
                                                        "time": 5.0,
                                                    },
                                                },
                                                {
                                                    "name": "grault",
                                                    "metrics": {
                                                        "time (inc)": 10.0,
                                                        "time": 10.0,
                                                    },
                                                },
                                            ],
                                        },
                                        {
                                            "name": "grault",
                                            "metrics": {
                                                "time (inc)": 10.0,
                                                "time": 10.0,
                                            },
                                        },
                                        {
                                            "name": "garply",
                                            "metrics": {
                                                "time (inc)": 15.0,
                                                "time": 15.0,
                                            },
                                        },
                                    ],
                                }
                            ],
                        }
                    ],
                },
                {
                    "name": "waldo",
                    "metrics": {"time (inc)": 50.0, "time": 0.0},
                    "children": [
                        {
                            "name": "fred",
                            "metrics": {"time (inc)": 35.0, "time": 5.0},
                            "children": [
                                {
                                    "name": "plugh",
                                    "metrics": {"time (inc)": 5.0, "time": 5.0},
                                },
                                {
                                    "name": "xyzzy",
                                    "metrics": {"time (inc)": 25.0, "time": 5.0},
                                    "children": [
                                        {
                                            "name": "thud",
                                            "metrics": {
                                                "time (inc)": 25.0,
                                                "time": 5.0,
                                            },
                                            "children": [
                                                {
                                                    "name": "baz",
                                                    "metrics": {
                                                        "time (inc)": 5.0,
                                                        "time": 5.0,
                                                    },
                                                },
                                                {
                                                    "name": "garply",
                                                    "metrics": {
                                                        "time (inc)": 15.0,
                                                        "time": 15.0,
                                                    },
                                                },
                                            ],
                                        }
                                    ],
                                },
                            ],
                        },
                        {
                            "name": "garply",
                            "metrics": {"time (inc)": 15.0, "time": 15.0},
                        },
                    ],
                },
            ],
        },
        {
            "name": "waldo",
            "metrics": {"time (inc)": 30.0, "time": 10.0},
            "children": [
                {
                    "name": "bar",
                    "metrics": {"time (inc)": 20.0, "time": 5.0},
                    "children": [
                        {"name": "baz", "metrics": {"time (inc)": 5.0, "time": 5.0}},
                        {
                            "name": "grault",
                            "metrics": {"time (inc)": 10.0, "time": 10.0},
                        },
                    ],
                }
            ],
        },
    ]

    return graph_dict


@pytest.fixture
def mock_dag_literal1():
    """Creates a mock DAG."""
    dag_ldict = [
        {
            "name": "A",
            "metrics": {"time (inc)": 130.0, "time": 0.0},
            "children": [
                {
                    "name": "B",
                    "metrics": {"time (inc)": 20.0, "time": 5.0},
                    "children": [
                        {
                            "name": "C",
                            "metrics": {"time (inc)": 5.0, "time": 5.0},
                            "children": [
                                {
                                    "name": "D",
                                    "metrics": {"time (inc)": 8.0, "time": 1.0},
                                }
                            ],
                        }
                    ],
                },
                {
                    "name": "E",
                    "metrics": {"time (inc)": 55.0, "time": 10.0},
                    "children": [
                        {"name": "F", "metrics": {"time (inc)": 1.0, "time": 9.0}}
                    ],
                },
            ],
        }
    ]

    return dag_ldict


@pytest.fixture
def mock_dag_literal2():
    """Creates a mock DAG."""
    dag_ldict = [
        {
            "name": "A",
            "metrics": {"time (inc)": 130.0, "time": 0.0},
            "children": [
                {
                    "name": "B",
                    "metrics": {"time (inc)": 20.0, "time": 5.0},
                    "children": [
                        {
                            "name": "C",
                            "metrics": {"time (inc)": 5.0, "time": 5.0},
                            "children": [
                                {
                                    "name": "D",
                                    "metrics": {"time (inc)": 8.0, "time": 1.0},
                                }
                            ],
                        }
                    ],
                },
                {
                    "name": "E",
                    "metrics": {"time (inc)": 55.0, "time": 10.0},
                    "children": [
                        {"name": "H", "metrics": {"time (inc)": 1.0, "time": 9.0}}
                    ],
                },
            ],
        }
    ]

    return dag_ldict


@pytest.fixture
def small_mock1():
    ldict = [
        {
            "name": "A",
            "metrics": {"time (inc)": 130.0, "time": 0.0},
            "children": [
                {
                    "name": "B",
                    "metrics": {"time (inc)": 20.0, "time": 5.0},
                    "children": [
                        {"name": "C", "metrics": {"time (inc)": 5.0, "time": 5.0}}
                    ],
                },
                {
                    "name": "E",
                    "metrics": {"time (inc)": 55.0, "time": 10.0},
                    "children": [
                        {"name": "F", "metrics": {"time (inc)": 1.0, "time": 9.0}}
                    ],
                },
                {"name": "H", "metrics": {"time (inc)": 55.0, "time": 10.0}},
            ],
        }
    ]

    return ldict


@pytest.fixture
def small_mock2():
    ldict = [
        {
            "name": "A",
            "metrics": {"time (inc)": 130.0, "time": 0.0},
            "children": [
                {
                    "name": "B",
                    "metrics": {"time (inc)": 20.0, "time": 5.0},
                    "children": [
                        {"name": "C", "metrics": {"time (inc)": 5.0, "time": 5.0}},
                        {"name": "D", "metrics": {"time (inc)": 5.0, "time": 5.0}},
                    ],
                },
                {
                    "name": "E",
                    "metrics": {"time (inc)": 55.0, "time": 10.0},
                    "children": [
                        {"name": "F", "metrics": {"time (inc)": 1.0, "time": 9.0}},
                        {"name": "G", "metrics": {"time (inc)": 1.0, "time": 9.0}},
                    ],
                },
            ],
        }
    ]

    return ldict


@pytest.fixture
def small_mock3():
    ldict = [
        {
            "name": "A",
            "metrics": {"time (inc)": 130.0, "time": 0.0},
            "children": [
                {"name": "B", "metrics": {"time (inc)": 20.0, "time": 5.0}},
                {
                    "name": "E",
                    "metrics": {"time (inc)": 55.0, "time": 10.0},
                    "children": [
                        {"name": "F", "metrics": {"time (inc)": 1.0, "time": 9.0}}
                    ],
                },
            ],
        }
    ]

    return ldict


@pytest.fixture
def mock_dag_literal_module():
    """Creates a mock DAG."""
    dag_ldict = [
        {
            "name": "A",
            "metrics": {"time (inc)": 130.0, "time": 0.0, "module": "main"},
            "children": [
                {
                    "name": "B",
                    "metrics": {"time (inc)": 20.0, "time": 5.0, "module": "foo"},
                    "children": [
                        {
                            "name": "C",
                            "metrics": {
                                "time (inc)": 5.0,
                                "time": 5.0,
                                "module": "graz",
                            },
                        }
                    ],
                },
                {
                    "name": "E",
                    "metrics": {"time (inc)": 55.0, "time": 10.0, "module": "bar"},
                    "children": [
                        {
                            "name": "F",
                            "metrics": {
                                "time (inc)": 1.0,
                                "time": 9.0,
                                "module": "baz",
                            },
                        }
                    ],
                },
            ],
        }
    ]

    return dag_ldict


@pytest.fixture
def mock_dag_literal_module_complex():
    """Creates a mock DAG."""
    dag_ldict = [
        {
            "name": "A",
            "metrics": {"time (inc)": 130.0, "time": 1.0, "module": "main"},
            "children": [
                {
                    "name": "B",
                    "metrics": {"time (inc)": 20.0, "time": 1.0, "module": "foo"},
                    "children": [
                        {
                            "name": "C",
                            "metrics": {
                                "time (inc)": 6.0,
                                "time": 1.0,
                                "module": "graz",
                            },
                            "children": [
                                {
                                    "name": "D",
                                    "metrics": {
                                        "time (inc)": 1.0,
                                        "time": 1.0,
                                        "module": "graz",
                                    },
                                }
                            ],
                        }
                    ],
                },
                {
                    "name": "E",
                    "metrics": {"time (inc)": 55.0, "time": 1, "module": "bar"},
                },
            ],
        }
    ]

    return dag_ldict


@pytest.fixture
def mock_dag_literal_module_more_complex():
    """Creates a mock DAG."""
    dag_ldict = [
        {
            "name": "A",
            "metrics": {"time (inc)": 130.0, "time": 0.0, "module": "main"},
            "children": [
                {
                    "name": "B",
                    "metrics": {"time (inc)": 20.0, "time": 5.0, "module": "foo"},
                    "children": [
                        {
                            "name": "C",
                            "metrics": {
                                "time (inc)": 5.0,
                                "time": 5.0,
                                "module": "graz",
                            },
                            "children": [
                                {
                                    "name": "D",
                                    "metrics": {
                                        "time (inc)": 8.0,
                                        "time": 1.0,
                                        "module": "graz",
                                    },
                                }
                            ],
                        }
                    ],
                },
                {
                    "name": "E",
                    "metrics": {"time (inc)": 55.0, "time": 10.0, "module": "bar"},
                    "children": [
                        {
                            "name": "F",
                            "metrics": {
                                "time (inc)": 1.0,
                                "time": 1.0,
                                "module": "foo",
                            },
                        }
                    ],
                },
            ],
        }
    ]

    return dag_ldict


@pytest.fixture
def osu_allgather_hpct_db(data_dir, tmpdir):
    """Builds a temporary directory containing the calc-pi database."""
    hpct_db_dir = os.path.join(data_dir, "hpctoolkit-threads-osu-allgather")

    for f in glob(os.path.join(str(hpct_db_dir), "*.metric-db")):
        shutil.copy(f, str(tmpdir))
    shutil.copy(os.path.join(hpct_db_dir, "experiment.xml"), str(tmpdir))

    return tmpdir
