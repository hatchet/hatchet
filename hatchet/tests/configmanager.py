# Copyright 2023-2024 University of Maryland and other Hatchet Project
# Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import hatchet as ht

from hatchet import GraphFrame
from hatchet.external.console import ConsoleRenderer
import pytest


def test_get_option():
    """Sanity test get_option() before changing values."""
    colormap = ht.get_option("colormap")
    invert_colormap = ht.get_option("invert_colormap")
    depth = ht.get_option("depth")

    assert colormap == "RdYlGn"
    assert invert_colormap is False
    assert depth == 10000


def test_get_default_value():
    """Sanity test get_default_value()."""
    colormap = ht.get_default_value("colormap")
    invert_colormap = ht.get_default_value("invert_colormap")
    depth = ht.get_default_value("depth")

    assert colormap == "RdYlGn"
    assert invert_colormap is False
    assert depth == 10000


def test_set_option():
    """Sanity test set_option()."""
    ht.set_option("invert_colormap", True)
    ht.set_option("depth", 25)
    ht.set_option("colormap", "PRGn")

    assert ht.get_option("colormap") == "PRGn"
    assert ht.get_option("invert_colormap") is True
    assert ht.get_option("depth") == 25


def test_reset_option():
    """Sanity test reset_option()."""
    ht.set_option("invert_colormap", True)
    ht.set_option("depth", 25)
    ht.set_option("colormap", "PRGn")

    ht.reset_option("colormap")
    ht.reset_option("invert_colormap")
    ht.reset_option("depth")

    assert ht.get_option("colormap") == "RdYlGn"
    assert ht.get_option("invert_colormap") is False
    assert ht.get_option("depth") == 10000


def test_reset_option_all():
    """Test the 'all' option of reset_option() after changing all values."""
    ht.set_option("invert_colormap", True)
    ht.set_option("depth", 13)
    ht.set_option("colormap", "PRGn")
    ht.reset_option("all")

    assert ht.get_option("colormap") == "RdYlGn"
    assert ht.get_option("invert_colormap") is False
    assert ht.get_option("depth") == 10000


# Tests for correct errors getting raised with an incorrect/invalid input.
def test_reset_option_with_invalid_key():
    with pytest.raises(ValueError, match="You must specify a valid key."):
        ht.reset_option("invalid")


def test_get_option_with_invalid_key():
    with pytest.raises(ValueError):
        ht.get_option("invalid")


def test_set_option_with_invalid_value1():
    with pytest.raises(TypeError):
        ht.set_option("colormap", 9)


def test_set_option_with_invalid_value2():
    with pytest.raises(TypeError):
        ht.set_option("depth", "RDYL")


def test_set_option_with_invalid_value3():
    with pytest.raises(TypeError):
        ht.set_option("invert_colormap", 17)


def test_set_option_with_invalid_value4():
    with pytest.raises(TypeError):
        ht.set_option("colormap", False)


def test_set_option_with_invalid_colormap():
    with pytest.raises(ValueError, match=r".*not a valid colormap.*"):
        ht.set_option("colormap", "Green")


def test_tree_set_option_depth(calc_pi_hpct_db):
    """Test functionalities on gf and make sure they output correctly."""
    gf = GraphFrame.from_hpctoolkit(str(calc_pi_hpct_db))

    output1 = ConsoleRenderer(unicode=True, color=False).render(
        gf.graph.roots,
        gf.dataframe,
        metric_column="time",
        precision=3,
        name_column="name",
        expand_name=False,
        context_column="file",
        rank=0,
        thread=0,
        depth=3,
        highlight_name=False,
        colormap="RdYlGn",
        invert_colormap=False,
    )

    ht.set_option("depth", 20)
    output2 = gf.tree()
    assert output1 != output2

    ht.set_option("depth", 3)
    output2 = gf.tree()
    assert output1 == output2

    output3 = ConsoleRenderer(unicode=True, color=False).render(
        gf.graph.roots,
        gf.dataframe,
        metric_column="time",
        precision=3,
        name_column="name",
        expand_name=False,
        context_column="file",
        rank=0,
        thread=0,
        depth=10,
        highlight_name=False,
        colormap="RdYlGn",
        invert_colormap=False,
    )

    ht.set_option("depth", 10)
    output4 = gf.tree()
    assert output3 == output4

    ht.set_option("depth", 3)
    output4 = gf.tree()
    assert output3 != output4
