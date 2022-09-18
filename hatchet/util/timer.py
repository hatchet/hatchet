# Copyright 2017-2022 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from collections import OrderedDict
from contextlib import contextmanager
from datetime import datetime
from io import StringIO
import statistics


class Timer(object):
    """Simple phase timer with a context manager."""

    def __init__(self):
        self._phase = None
        self._start_time = None
        self._times = OrderedDict()

    def start_phase(self, phase):
        now = datetime.now()
        delta = None

        if self._phase:
            delta = now - self._start_time
            self._times[self._phase] = delta

        self._phase = phase
        self._start_time = now
        return delta

    def end_phase(self):
        assert self._phase and self._start_time

        now = datetime.now()
        delta = now - self._start_time
        if self._times.get(self._phase):
            self._times[self._phase] = self._times.get(self._phase) + delta
        else:
            self._times[self._phase] = delta

        self._phase = None
        self._start_time = None

    def __str__(self):
        out = StringIO()
        out.write("Times:\n")
        for phase, delta in self._times.items():
            out.write("    %-20s %.2fs\n" % (phase + ":", delta.total_seconds()))
        return out.getvalue()

    def get_time(self, phase):
        """Returns time for given phase."""
        return self._times.get(phase).total_seconds()

    def get_phases(self, time, precision=None):
        """Returns a list of phases whose time values are equal to the given time.
        Inputs:
         - time: The time value of the desired phases.
         - precision (optional): The number of decimal places to which the phase times should be compared with the given time.
        Output:
         - List of phases with the given time, adjusted for given precision.
        """
        time = str(float(time))
        if precision:
            precision = int(precision)
        phases = []
        for p, t in self._times.items():
            t = str(t.total_seconds())
            if (
                int(float(time)) == int(t.split(".")[0])
                and (time.split(".")[1] + "0" * precision)[:precision]
                == t.split(".")[1][:precision]
            ):
                phases.append(p)
        return phases

    def max_time(self):
        """Returns greatest time of all phases."""
        return max(self._times.values()).total_seconds()

    def min_time(self):
        """Returns smallest time of all phases."""
        return min(self._times.values()).total_seconds()

    def total_time(self):
        """Returns total time from all phases."""
        total_time = 0
        for time in self._times.values():
            total_time += time.total_seconds()
        return total_time

    def average(self):
        """Returns average time of all phases."""
        return self.total_time() / len(self._times.values())

    @contextmanager
    def phase(self, name):
        self.start_phase(name)
        yield
        self.end_phase()
