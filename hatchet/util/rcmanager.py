try:
    from collections.abc import MutableMapping
except ImportError:
    from collections import MutableMapping
import os.path as path
import yaml


class RcManager(MutableMapping, dict):
    """
    A runtime configurations class; modeled after the RcParams class in matplotlib.
    The benifit of this class over a dictonary is validation of set item and formatting
    of output.
    """

    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    def __setitem__(self, key, val):
        """
        We can put validation of configs here.
        """
        return dict.__setitem__(self, key, val)

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
