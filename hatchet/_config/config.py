from __future__ import annotations

from optparse import OptionError
from typing import (
    TYPE_CHECKING,
    Any,
)
import warnings


class GlobalConfig:
    # holds registered option metadata
    # registered_options: dict[str, RegisteredOption] = {}
    # global_config: dict[str, Any] = {}
    registered_options: dict[str, Any] = {
        "colormap": "RdYlGn",
        "invert_colormap": False,
        "depth": 10000,
    }

    # holds the current values for registered options
    # global_config: dict[str, Any] = {}
    global_config: dict[str, Any] = {
        "colormap": "RdYlGn",
        "invert_colormap": False,
        "depth": 10000,
    }

    # In these dicts we want colormap, invertcolormap, depth
    # registered_options = {"colormap": "RdYlGn", "invert_colormap": False, "depth": 10000}
    # global_config = registered_options

    def get_option(self, key: str) -> Any:
        if len(key) == 0:  # Or key is invalid
            raise OptionError("No such keys(s)")
        else:
            return self.global_config[key]

    def reset_option(self, key: str, silent: bool = False) -> None:
        if len(key) == 0:  # Or key is invalid
            raise OptionError("No such keys(s)")
        # Need to check if its "all" or a specific key
        if key == "all":
            global_config = self.registered_options
        elif self.registered_options.has_key(key):
            # If it's a specific key and its valid
            global_config[key] = self.registered_options[key]
        else:
            raise ValueError(
                "You must specify a valid key. Or, use the special keyword "
                '"all" to reset all the options to their default value'
            )

    def set_option(self, key: str, val: Any) -> None:
        if len(key) == 0:  # Or key is invalid
            raise OptionError("No such keys(s)")
        # Also need to check if val is valid for that specific key
        # Some keys take strings, others take bools, others take ints
        # Do we need bounds for some of the values? (Ex. Can only be between 1 and 500)

        # set_validators(key, val)
        # If its valid, update the key, value pair
        self.global_config[key] = val

    def set_validators(self, key, value):
        if key == "colormap":
            return self.str_validator(key, value)
        elif key == "invert_colormap":
            return self.bool_validator(key, value)
        elif key == "depth":
            return self.int_validator(key, value)
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
