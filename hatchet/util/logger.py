import inspect
import os
import json
from datetime import datetime
import hatchet


class Log(object):
    def __init__(self, filename="hatchet.log", active=True):
        self._log_file = filename
        self._active = active
        self._nested = False  # ensures we only log user called commands

    def set_output_file(self, filename=""):
        self._log_file = filename

    def set_active(self):
        self._active = True

    def set_inactive(self):
        self._active = False

    def read(self):
        logs = []
        with open(self._log_file, "r") as f:
            for line in f.readlines():
                logs.append(json.loads(line))
            print(logs)

    def append_to_file(self, log):
        """Manages the opening and writing of log information to a file."""
        with open(self._log_file, "a") as f:
            f.write(json.dumps(log)+'\n')

    def loggable(self, function):
        """A decrator which logs calls to hatchet functions"""

        def inner(*args, **kwargs):
            # turn on logger
            if "logging" in kwargs and kwargs["logging"] is True:
                self._active = True
            elif "logging" in kwargs and kwargs["logging"] is False:
                self._active = False

            # if logger is on and user called function
            if self._active and self._nested is False:
                log_dict = {}
                arg_list = []

                log_dict["function"] = function.__name__

                for i, arg in enumerate(args):
                    if inspect.isfunction(arg):
                        # log functions passed (eg. lambda passed to filter) as source code
                        arg_source = inspect.getsource(arg)
                        arg_list.append(arg_source)

                    elif isinstance(arg, hatchet.GraphFrame):
                        # log a graphframe as a dictionary of metadata
                        graphframe_metadata = {}

                        graphframe_metadata["object"] = arg.__class__.__name__
                        graphframe_metadata["id"] = id(arg)
                        graphframe_metadata["rows"] = arg.dataframe.shape[0]
                        graphframe_metadata["nodes"] = len(arg.graph)

                        arg_list.append(graphframe_metadata)
                    else:
                        # log everything else
                        arg_list.append(arg)

                log_dict["args"] = tuple(arg_list)
                log_dict["start"] = datetime.now().isoformat()

                self._nested = True
                holder = function(*args, **kwargs)
                self._nested = False

                log_dict["end"] = datetime.now().isoformat()
                log_dict["kwargs"] = kwargs

                self.append_to_file(log_dict)

                return holder
            else:
                return function(*args, **kwargs)

        return inner


Logger = Log()
