# Copyright 2017-2021 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import pandas as pd
import pandas.api.types as ptypes
import pytest

import hatchet as ht
from hatchet.external.scripts import BoxPlot
from hatchet.util.executable import which

bp_columns = ['name', 'q', 'ocat', 'ometric', 'min', 'max', 'mean', 'var', 'imb', 'kurt', 'skew']


def test_boxplot_tgt(calc_pi_hpct_db):
    gf = ht.GraphFrame.from_hpctoolkit(str(calc_pi_hpct_db))
    metrics = ["time"]
    bp = BoxPlot(cat_column='rank', tgt_gf=gf, bkg_gf=None, metrics=metrics)

    # Check if the format of target is correct.
    assert metrics[0] in list(bp.tgt.keys())
    assert isinstance(bp.tgt[metrics[0]], ht.GraphFrame)
    assert isinstance(bp.tgt[metrics[0]].dataframe, pd.DataFrame)
    assert isinstance(bp.tgt[metrics[0]].graph, ht.graph.Graph)

    # Check if the format of background is correct.
    assert not hasattr(bp, 'bkg')

    df = bp.tgt[metrics[0]].dataframe
    graph = bp.tgt[metrics[0]].graph

    # Check if the required columns are present.
    columns = ['name', 'q', 'ocat', 'ometric', 'min', 'max', 'mean', 'var', 'imb', 'kurt', 'skew']
    assert df.columns.tolist().sort() == columns.sort()

def test_boxplot_bkg(calc_pi_hpct_db):
    tgt_gf = ht.GraphFrame.from_hpctoolkit(str(calc_pi_hpct_db))
    bkg_gf = ht.GraphFrame.from_hpctoolkit(str(calc_pi_hpct_db))
    metrics = ["time"]
    bp = BoxPlot(cat_column='rank', tgt_gf=tgt_gf, bkg_gf=bkg_gf, metrics=metrics)

    # Check if the format of target is correct.
    assert metrics[0] in list(bp.tgt.keys())
    assert isinstance(bp.tgt[metrics[0]], ht.GraphFrame)
    assert isinstance(bp.tgt[metrics[0]].dataframe, pd.DataFrame)
    assert isinstance(bp.tgt[metrics[0]].graph, ht.graph.Graph)

    # Check if the format of background is correct.
    assert metrics[0] in list(bp.bkg.keys())
    assert isinstance(bp.bkg[metrics[0]], ht.GraphFrame)
    assert isinstance(bp.bkg[metrics[0]].dataframe, pd.DataFrame)
    assert isinstance(bp.bkg[metrics[0]].graph, ht.graph.Graph)

    # Check if the required columns are present.
    assert bp.tgt[metrics[0]].dataframe.columns.tolist().sort() == bp_columns.sort()
    assert bp.bkg[metrics[0]].dataframe.columns.tolist().sort() == bp_columns.sort()

def test_output_dtypes(calc_pi_hpct_db):
    gf = ht.GraphFrame.from_hpctoolkit(str(calc_pi_hpct_db))
    metrics = ["time"]
    bp = BoxPlot(cat_column='rank', tgt_gf=gf, bkg_gf=None, metrics=metrics)

    object_dtype = ['name', 'q', 'ocat', 'ometric']
    float_dtype = ['min', 'max', 'mean', 'var', 'imb', 'kurt', 'skew']

    assert all(ptypes.is_float_dtype(bp.tgt['time'].dataframe[col]) for col in float_dtype)
    assert all(ptypes.is_object_dtype(bp.tgt['time'].dataframe[col]) for col in object_dtype)

def test_callsite_count(calc_pi_hpct_db):
    gf = ht.GraphFrame.from_hpctoolkit(str(calc_pi_hpct_db))
    metrics = ["time"]
    bp = BoxPlot(cat_column='rank', tgt_gf=gf, bkg_gf=None, metrics=metrics)

    # assert len(bp.tgt['time'].graph) == len(bp.tgt['time'].dataframe.index.values.tolist())

    # Check if equal number of nodes in graph and dataframe.
    # assert len(bp.tgt[metrics[0]].graph) == len(bp.tgt[metrics[0]].dataframe['name'].unique().tolist())
    # assert len(bp.bkg[metrics[0]].graph) == len(bp.bkg[metrics[0]].dataframe['name'].unique().tolist())
