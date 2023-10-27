import hatchet as ht
import pandas as pd

# from ..hatchet.hatchet._config.config import get_option, set_option, reset_option, OptionError

from hatchet import GraphFrame
from hatchet._config.config import GlobalConfig
from hatchet import get_option, set_option, reset_option

# from hatchet._config.config import get_option, set_option, reset_option, OptionError

import pytest


# Test 'get_option' function
def test_get_option():
    colormap = get_option("colormap")
    invert_colormap = get_option("invert_colormap")
    depth = get_option("depth")

    assert colormap == "RdYlGn"
    assert invert_colormap is False
    assert depth == 10000


def test_set_option():
    set_option("colormap", "Green")
    set_option("invert_colormap", True)
    set_option("depth", 25)

    assert get_option("colormap") == "Green"
    assert get_option("invert_colormap") is True
    assert get_option("depth") == 25


def test_reset_option():
    reset_option("colormap")
    reset_option("invert_colormap")

    assert get_option("colormap") == "RdYlGn"
    assert get_option("invert_colormap") is False


def test_reset_option_all():
    reset_option("all")

    assert get_option("colormap") == "RdYlGn"
    assert get_option("invert_colormap") is False
    assert get_option("depth") == 10000


# def test_error_handling():
#     with pytest.raises(OptionError):
#         set_option("invalid_key", "value")  # Testing an invalid key

#     with pytest.raises(OptionError):
#         get_option("")  # Testing an empty key
