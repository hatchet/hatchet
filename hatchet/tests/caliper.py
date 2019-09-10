# Copyright 2017-2019 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import subprocess

import pytest

from hatchet import GraphFrame
from hatchet.readers.caliper_reader import CaliperReader
from hatchet.util.executable import which

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
    gf = GraphFrame.from_caliper_json(str(lulesh_caliper_json))

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


@pytest.mark.skipif(not which("cali-query"), reason="needs cali-query to be in path")
def test_sample_cali(sample_caliper_raw_cali):
    """Sanity check the Caliper reader ingesting a .cali file."""
    grouping_attribute = "function"
    default_metric = "sum(sum#time.duration),inclusive_sum(sum#time.duration)"
    query = "select function,%s group by %s format json-split" % (
        default_metric,
        grouping_attribute,
    )

    gf = GraphFrame.from_caliper(str(sample_caliper_raw_cali), query)

    assert len(gf.dataframe.groupby("name")) == 18


@pytest.mark.skipif(not which("cali-query"), reason="needs cali-query to be in path")
def test_json_string_literal(sample_caliper_raw_cali):
    """Sanity check the Caliper reader ingesting a JSON string literal."""
    cali_query = which("cali-query")
    grouping_attribute = "function"
    default_metric = "sum(sum#time.duration),inclusive_sum(sum#time.duration)"
    query = "select function,%s group by %s format json-split" % (
        default_metric,
        grouping_attribute,
    )

    cali_json = subprocess.Popen(
        [cali_query, "-q", query, sample_caliper_raw_cali], stdout=subprocess.PIPE
    )

    gf = GraphFrame.from_caliper_json(cali_json.stdout)

    assert len(gf.dataframe.groupby("name")) == 18


def test_sample_json(sample_caliper_json):
    """Sanity check the Caliper reader ingesting a JSON string literal."""
    gf = GraphFrame.from_caliper_json(str(sample_caliper_json))

    assert len(gf.dataframe.groupby("name")) == 18


def test_filter_squash_calc_unify_pi_database(lulesh_caliper_json):
    gf = GraphFrame.from_caliper_json(str(lulesh_caliper_json))

    orig_graph = gf.graph.copy()

    filtered = gf.filter(lambda x: x["name"].startswith("Calc"))
    assert filtered.graph is gf.graph
    assert filtered.graph == orig_graph

    gf2 = GraphFrame.from_caliper_json(str(lulesh_caliper_json))

    assert gf.graph is not gf2.graph

    filtered2 = gf2.filter(lambda x: x["name"].startswith("Calc"))
    assert filtered2.graph is gf2.graph

    squashed_gf = filtered.squash()
    squashed_gf2 = filtered2.squash()

    squashed_gf.unify(squashed_gf2)
    assert squashed_gf.graph is squashed_gf2.graph
    assert all(
        squashed_gf.dataframe["node"].apply(id)
        == squashed_gf2.dataframe["node"].apply(id)
    )
    assert all(squashed_gf.dataframe.index == squashed_gf2.dataframe.index)
