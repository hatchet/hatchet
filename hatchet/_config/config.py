from __future__ import annotations

import sys
import traceback

from collections import defaultdict

from ..util.colormaps import ColorMaps
from optparse import OptionError
from typing import (
    TYPE_CHECKING,
    Any,
)
import warnings


# class GlobalConfig:
# holds registered option default data
registered_options: dict[str, Any] = {
    "colormap": "RdYlGn",
    "invert_colormap": False,
    "depth": 10000,
}

# holds the current values for registered options
global_config: dict[str, Any] = {
    "colormap": "RdYlGn",
    "invert_colormap": False,
    "depth": 10000,
}

colormaps = [
    "RdYlGn",
    "BrBG",
    "PiYG",
    "PRGn",
    "PuOr",
    "RdBu",
    "RdGy",
    "RdYlBu",
    "Spectral",
]


# This function returns the current value of the specified key
def get_option(key: str) -> Any:
    if len(key) == 0 or key not in registered_options:
        raise ValueError("No such keys(s)")
    else:
        return global_config[key]


# This function returns the default value of the specified key
def get_default_value(key: str) -> Any:
    if len(key) == 0 or key not in registered_options:
        raise ValueError("No such keys(s)")
    else:
        return registered_options[key]


# This function updates the value of the specified key in the global_config dictionary.
def set_option(key: str, val: Any):
    if len(key) == 0 or key not in registered_options:
        raise ValueError("No such keys(s)")
    # Also need to check if val is valid for that specific key. Some keys take strings, others take bools, others take ints
    if set_validators(key, val):
        # If its valid, update the key, value pair
        global_config[key] = val
    # If its not valid, an error will be thrown by one of the validator functions


# This function resets the value specified key back to its default value.
# If 'all' is passed in, it resets the values of all keys.
def reset_option(key: str) -> None:
    if len(key) == 0:
        raise OptionError("No such keys(s)")
    # Need to check if its "all" or a specific key
    if key in registered_options:
        # If it's a specific key and its valid
        global_config[key] = registered_options[key]
    elif key == "all":
        for k, v in registered_options.items():
            global_config[k] = v
    else:
        raise ValueError(
            "You must specify a valid key. Or, use the special keyword "
            '"all" to reset all the options to their default value'
        )


# Function to check the specifified key enetered. It sends the value to the corresponding validator depending on key enetered.
def set_validators(key, value):
    if key == "colormap":
        # return str_validator(key, value)
        if str_validator(key, value):
            return is_valid_colormap(key, value)
    elif key == "invert_colormap":
        return bool_validator(key, value)
    elif key == "depth":
        return int_validator(key, value)
    else:
        raise ValueError("No such keys(s)")


# Validator to check if the value entered is of type bool
def bool_validator(key, value):
    if type(value) is not bool:
        raise TypeError(
            'Error loading configuration: The Value "{}" for Configuration "{}" must be of type Bool'.format(
                value, key
            )
        )
    else:
        return True


# Validator to check if the value entered is of type string
def str_validator(key, value):
    if type(value) is not str:
        raise TypeError(
            'Error loading configuration: The Value "{}" for Configuration "{}" must be of type string'.format(
                value, key
            )
        )
    else:
        return True


# Validator to check if the value entered is of type int
def int_validator(key, value):
    if type(value) is not int:
        raise TypeError(
            'Error loading configuration: The Value "{}" for Configuration "{}" must be of type int'.format(
                value, key
            )
        )
    if key == "depth" and value < 1:
        raise ValueError("Depth must be greater than 1")
    return True


# Validator to check if the value entered is of type float
def float_validator(key, value):
    if type(value) is not float:
        raise TypeError(
            'Error loading configuration: The Value "{}" for Configuration "{}" must be of type float'.format(
                value, key
            )
        )
    else:
        return True


# Validator to check if the colormap specfied exists and is valid
def is_valid_colormap(key, colormap_name):
    if colormap_name in colormaps:
        return True
    else:
        raise ValueError(
            'Error setting ColorMap: The value "{}" for Configuration "{}" is not a valid colormap'.format(
                colormap_name, key
            )
        )
