##############################################################################
# Copyright (c) 2017-2019, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# This file is part of Hatchet.
# Created by Abhinav Bhatele <bhatele@llnl.gov>.
# LLNL-CODE-741008. All rights reserved.
#
# For details, see: https://github.com/LLNL/hatchet
# Please also read the LICENSE file for the MIT License notice.
##############################################################################

from hatchet import GraphFrame, CaliperReader

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
