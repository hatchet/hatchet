from __future__ import annotations
from contextlib import (
    ContextDecorator,
    contextmanager,
)
from optparse import OptionError
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    NamedTuple,
    cast,
)
import warnings


# holds registered option metadata
# _registered_options: dict[str, RegisteredOption] = {}
_registered_options: dict[str, Any] = {}

# holds the current values for registered options
_global_config: dict[str, Any] = {}

# In these dicts we want colormap, invertcolormap, depth
_registered_options = {colormap: "RdYlGn", invert_colormap: False, depth: 10000}
_global_config = _registered_options


def _get_option(key: str) -> Any:
    if len(key) == 0:  # Or key is invalid
        raise OptionError("No such keys(s)")
    else:
        return _global_config[key]


def _reset_option(key: str, silent: bool = False) -> None:
    if len(key) == 0:  # Or key is invalid
        raise OptionError("No such keys(s)")
    # Need to check if its "all" or a specific key
    if key == "all":
        _global_config = _registered_options
    elif len(key) > 1 and _registered_options.has_key(key):
        # If it's a specific key and its valid
        _global_config[key] = _registered_options[key]
    else:
        raise ValueError(
            "You must specify a valid key. Or, use the special keyword "
            '"all" to reset all the options to their default value'
        )


# def _set_option(*args, **kwargs) -> None:
def _set_option(key: str, val: Any) -> None:
    if len(key) == 0:  # Or key is invalid
        raise OptionError("No such keys(s)")
    # Also need to check if val is valid for that specific key
    # Some keys take strings, others take bools, others take ints
    # Do we need bounds for some of the values? (Ex. Can only be between 1 and 500)
    
    # set_validators(key, val)
    # If its valid, update the key, value pair
    _global_config[key] = val


def set_validators(key, value):
    if key == "colormap":
        return str_validator(key, value)
    elif key == "invert_colormap":
        return bool_validator(key, value)
    elif key == "depth":
        return int_validator(key, value)
    else:
        raise OptionError("No such keys(s)")


def bool_validator(key, value):
    if not isinstance(value, bool):
        raise TypeError(
            'Error loading configuration: The Value "{}" for Configuration "{}" must be of type bool'.format(
                value, key
            )
        )
    else:
        return True


def str_validator(key, value):
    if not isinstance(value, str):
        raise TypeError(
            'Error loading configuration: The Value "{}" for Configuration "{}" must be of type string'.format(
                value, key
            )
        )
    else:
        return True


def int_validator(key, value):
    if not isinstance(value, int):
        raise TypeError(
            'Error loading configuration: The Value "{}" for Configuration "{}" must be of type int'.format(
                value, key
            )
        )
    else:
        return True


def float_validator(key, value):
    if not isinstance(value, float):
        raise TypeError(
            'Error loading configuration: The Value "{}" for Configuration "{}" must be of type float'.format(
                value, key
            )
        )
    else:
        return True
