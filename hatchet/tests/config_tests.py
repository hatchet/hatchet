import hatchet as ht
import pandas as pd

import pytest


# Test 'get_option' function
def test_get_option():
    colormap = ht.get_option("colormap")
    invert_colormap = ht.get_option("invert_colormap")
    depth = ht.get_option("depth")

    assert colormap == "RdYlGn"
    assert invert_colormap is False
    assert depth == 10000


# Test 'get_default_value' function
def test_get_default_value():
    colormap = ht.get_default_value("colormap")
    invert_colormap = ht.get_default_value("invert_colormap")
    depth = ht.get_default_value("depth")

    assert colormap == "RdYlGn"
    assert invert_colormap is False
    assert depth == 10000


def test_set_option():
    ht.set_option("invert_colormap", True)
    ht.set_option("depth", 25)
    ht.set_option("colormap", "PRGn")

    assert ht.get_option("colormap") == "PRGn"
    assert ht.get_option("invert_colormap") is True
    assert ht.get_option("depth") == 25


def test_reset_option():
    ht.reset_option("colormap")
    ht.reset_option("invert_colormap")
    ht.reset_option("depth")

    assert ht.get_option("colormap") == "RdYlGn"
    assert ht.get_option("invert_colormap") is False
    assert ht.get_option("depth") == 10000


def test_reset_option_all():
    ht.set_option("invert_colormap", True)
    ht.set_option("depth", 13)
    ht.set_option("colormap", "PRGn")
    ht.reset_option("all")

    assert ht.get_option("colormap") == "RdYlGn"
    assert ht.get_option("invert_colormap") is False
    assert ht.get_option("depth") == 10000


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
