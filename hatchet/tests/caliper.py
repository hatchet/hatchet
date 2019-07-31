# Copyright 2017-2019 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import subprocess
import sys

from hatchet import GraphFrame
from hatchet.readers.caliper_reader import CaliperReader


annotations = [
    "main",
    "LagrangeLeapFrog",
    "LagrangeElements",
    "ApplyMaterialPropertiesForElems",
    "EvalEOSForElems",
    "CalcEnergyForElems",
    "CalcPressureForElems",
    "CalcSoundSpeedForElems",
    "UpdateVolumesForElems",
    "CalcTimeConstraintsForElems",
    "CalcCourantConstraintForElems",
    "CalcHydroConstraintForElems",
    "TimeIncrement",
    "LagrangeNodal",
    "CalcForceForNodes",
    "CalcVolumeForceForElems",
    "IntegrateStressForElems",
    "CalcHourglassControlForElems",
    "CalcFBHourglassForceForElems",
    "CalcLagrangeElements",
    "CalcKinematicsForElems",
    "CalcQForElems",
    "CalcMonotonicQGradientsForElems",
    "CalcMonotonicQRegionForElems",
]


def test_graphframe(lulesh_caliper_json):
    """Sanity test a GraphFrame object with known data."""
    gf = GraphFrame()
    gf.from_caliper(str(lulesh_caliper_json))

    assert len(gf.dataframe.groupby("name")) == 24

    # TODO: add tests for dataframe


def test_read_calc_pi_database(lulesh_caliper_json):
    """Sanity check the Caliper reader by examining a known input."""
    reader = CaliperReader(str(lulesh_caliper_json))
    reader.read_json_sections()

    assert len(reader.json_data) == 200
    assert len(reader.json_cols) == 4
    assert len(reader.json_cols_mdata) == 4
    assert len(reader.json_nodes) == 24

    reader.create_graph()
    assert all(an in reader.idx_to_label.values() for an in annotations)


def test_json_string_literal(caliper_raw_cali):
    """Sanity check the Caliper reader ingesting a JSON string literal."""
    cali_query = "/usr/gapps/spot/caliper/bin/cali-query"
    grouping_attribute = "function"
    default_metric = "sum(sum#time.duration),inclusive_sum(sum#time.duration)"
    query = "select function,%s group by %s format json-split" % (
        default_metric,
        grouping_attribute,
    )

    gf = GraphFrame()

    if sys.version_info >= (3, 0, 0):
        cali_json = subprocess.run(
            [cali_query, "-q", query, str(caliper_raw_cali)],
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )
        gf.from_caliper(cali_json.stdout, "literal")
    else:
        cali_json = subprocess.check_output(
            [cali_query, "-q", query, str(caliper_raw_cali)], universal_newlines=True
        )
        gf.from_caliper(cali_json, "literal")

    assert len(gf.dataframe.groupby("name")) == 18
