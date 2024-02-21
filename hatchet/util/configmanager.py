# Copyright 2023-2024 University of Maryland and other Hatchet Project
# Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

# from __future__ import annotations
from optparse import OptionError
from typing import Any, Dict


# holds default values of registered options
_registered_options: Dict[str, Any] = {
    "colormap": "RdYlGn",
    "invert_colormap": False,
    "depth": 10000,
}

# holds the current values of each option
_global_config: Dict[str, Any] = {
    "colormap": "RdYlGn",
    "invert_colormap": False,
    "depth": 10000,
}

# list of available color maps in hatchet/util/colormaps.py
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


def get_option(key: str) -> Any:
    """ This function returns the current value of the specified key."""
    if len(key) == 0 or key not in _registered_options:
        raise ValueError("No such keys(s)")
    else:
        return _global_config[key]


def get_default_value(key: str) -> Any:
    """ This function returns the default value of the specified key."""
    if len(key) == 0 or key not in _registered_options:
        raise ValueError("No such keys(s)")
    else:
        return _registered_options[key]


def set_option(key: str, val: Any):
    """ This function updates the value of the specified key in the
        _global_config dictionary.
    """
    if len(key) == 0 or key not in _registered_options:
        raise ValueError("No such keys(s)")

    # Also need to check if val is valid for that specific key. Some keys take
    # strings, others take bools, others take ints
    if set_validators(key, val):
        # If its valid, update the key, value pair
        _global_config[key] = val
    # If its not valid, an error will be thrown by one of the validator functions


def reset_option(key: str) -> None:
    """ This function resets the value specified key back to its default value.
        If 'all' is passed in, it resets the values of all keys.
    """
    if len(key) == 0:
        raise OptionError("No such keys(s)")

    # Need to check if its "all" or a specific key
    if key in _registered_options:
        # If it's a specific key and its valid
        _global_config[key] = _registered_options[key]
    elif key == "all":
        for k, v in _registered_options.items():
            _global_config[k] = v
    else:
        raise ValueError(
            "You must specify a valid key. Or, use the special keyword "
            '"all" to reset all the options to their default value'
        )


def set_validators(key, value):
    """ Function to check the specifified key enetered. It sends the value to
        the corresponding validator depending on key entered.
    """
    if key == "colormap":
        if str_validator(key, value):
            return is_valid_colormap(key, value)
    elif key == "invert_colormap":
        return bool_validator(key, value)
    elif key == "depth":
        return int_validator(key, value)
    else:
        raise ValueError("No such keys(s)")


def bool_validator(key, value):
    """ Validator to check if the value entered is of type bool."""
    if type(value) is not bool:
        raise TypeError(
            'Error loading configuration: The Value "{}" for Configuration "{}" must be of type Bool'.format(
                value, key
            )
        )
    else:
        return True


def str_validator(key, value):
    """ Validator to check if the value entered is of type string"""
    if type(value) is not str:
        raise TypeError(
            'Error loading configuration: The Value "{}" for Configuration "{}" must be of type string'.format(
                value, key
            )
        )
    else:
        return True


def int_validator(key, value):
    """ Validator to check if the value entered is of type int"""
    if type(value) is not int:
        raise TypeError(
            'Error loading configuration: The Value "{}" for Configuration "{}" must be of type int'.format(
                value, key
            )
        )
    if key == "depth" and value < 1:
        raise ValueError("Depth must be greater than 1")
    return True


def float_validator(key, value):
    """ Validator to check if the value entered is of type float"""
    if type(value) is not float:
        raise TypeError(
            'Error loading configuration: The Value "{}" for Configuration "{}" must be of type float'.format(
                value, key
            )
        )
    else:
        return True


def is_valid_colormap(key, colormap_name):
    """ Validator to check if the colormap specfied exists and is valid"""
    if colormap_name in colormaps:
        return True
    else:
        raise ValueError(
            'Error setting ColorMap: The value "{}" for Configuration "{}" is not a valid colormap'.format(
                colormap_name, key
            )
        )
