try:
    from collections.abc import MutableMapping
except ImportError:
    from collections import MutableMapping
import os.path as path
import yaml


class ConfigValidator:
    def __init__(self):
        self._validations = {}
        self._set_validators_to_configs()

    def bool_validator(self, key, value):
        if not isinstance(value, bool):
            raise TypeError(
                'Error loading configuration: Configuration "{}" must be of type bool'.format(
                    key
                )
            )
        else:
            return value

    def str_validator(self, key, value):
        if not isinstance(value, str):
            raise TypeError(
                'Error loading configuration: Configuration "{}" must be of type string'.format(
                    key
                )
            )
        else:
            return value

    def int_validator(self, key, value):
        if not isinstance(value, int):
            raise TypeError(
                'Error loading configuration: Configuration "{}" must be of type int'.format(
                    key
                )
            )
        else:
            return value

    def float_validator(self, key, value):
        if not isinstance(value, float):
            raise TypeError(
                'Error loading configuration: Configuration "{}" must be of type float'.format(
                    key
                )
            )
        else:
            return value

    def list_validator(self, key, value):
        if not isinstance(value, list):
            raise TypeError(
                'Error loading configuration: Configuration "{}" must be of type list'.format(
                    key
                )
            )
        else:
            return value

    def dict_validator(self, key, value):
        if not isinstance(value, dict):
            raise TypeError(
                'Error loading configuration: Configuration "{}" must be of type dict'.format(
                    key
                )
            )
        else:
            return value

    def validate(self, key, value):
        try:
            return self._validations[key](key, value)
        except TypeError as e:
            raise e
        except KeyError:
            pass

    def _set_validators_to_configs(self):
        # real configurations
        self._validations["logging"] = self.bool_validator
        self._validations["log_directory"] = self.str_validator
        self._validations["highlight_name"] = self.bool_validator
        self._validations["invert_colormap"] = self.bool_validator


class RcManager(MutableMapping, dict):
    """
    A runtime configurations class; modeled after the RcParams class in matplotlib.
    The benifit of this class over a dictonary is validation of set item and formatting
    of output.
    """

    def __init__(self, *args, **kwargs):
        self._validator = ConfigValidator()
        self.update(*args, **kwargs)

    def __setitem__(self, key, val):
        """
        Function loads valid configurations and prints errors for invalid configs.
        """
        try:
            self._validator.validate(key, val)
            return dict.__setitem__(self, key, val)
        except TypeError as e:
            print(e)

    def __getitem__(self, key):
        return dict.__getitem__(self, key)

    def __iter__(self):
        for kv in sorted(dict.__iter__(self)):
            yield kv

    def __str__(self):
        return "\n".join(map("{0[0]}: {0[1]}".format, sorted(self.items())))


def _resolve_conf_file():
    """
    Determines which configuration file to load.
    Uses the precendence order:
        1. $HOME/.config/hatchet/hatchetrc.yaml
        2. $HATCHET_BASE_DIR/hatchetrc.yaml
    """
    home = path.expanduser("~")
    conf_dir = path.join(home, ".config", "hatchet", "hatchetrc.yaml")
    if path.exists(conf_dir):
        return conf_dir
    else:
        my_path = path.abspath(path.dirname(__file__))
        rel_path = path.join(my_path, "..", "..", "hatchetrc.yaml")
        return rel_path


def _read_config_from_file(filepath):
    configs = {}
    with open(filepath, "r") as f:
        configs = yaml.load(f, yaml.FullLoader)
    return configs


filepath = _resolve_conf_file()
configs = _read_config_from_file(filepath)

# Global instance of configurations
RcParams = RcManager(configs)
