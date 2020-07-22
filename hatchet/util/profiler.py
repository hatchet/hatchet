# Copyright 2017-2020 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from collections import OrderedDict
from contextlib import contextmanager
from datetime import datetime
from io import StringIO

import cProfile
import pstats
import io


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

    @contextmanager
    def phase(self, name):
        self.start_phase(name)
        yield
        self.end_phase()


# class for profiling
class Profiler:
    def __init__(self, prf=cProfile.Profile()):
        self.prf = prf
        self.running_total = 0

    def start(self):
        """
            Description: Place before the block of code to be profiled.
        """
        self.prf.enable()

    def end(self):
        """
            Description: Place at the end of the block of code being profiled.
            Return: The total runtime of the last profile attempt
        """
        self.prf.disable()
        return self.getLastRuntime()

    def reset(self):
        """
            Description: If profiling across multiple different files or different
            functionalities in one program run, this must be called between
            profile instances to clear out data from prior start-stop block.
        """
        self.prf = cProfile.Profile()
        self.running_total = 0

    def getLastRuntime(self):
        """
            Description: Retrieves the last runtime from a sequence of profiles if
            profiling in a loop to get average statistics.
        """
        last = pstats.Stats(self.prf).__dict__["total_tt"] - self.running_total
        self.running_total += last
        return last

    def getRuntime(self):
        """
            Description: Get the total cumulative runtime logged by this profilier.
            Reset by calls to .reset().
        """
        return pstats.Stats(self.prf).__dict__["total_tt"]

    def getStats(self):
        """
            Description: Get stats as a pstats output.
        """
        s = io.StringIO()
        return pstats.Stats(self.prf, stream=s)

    def getAverageRuntime(self, num_of_runs):
        """
            Description: Get average runtime over a number of trials. Takes the cumulative
            runtime and divides by the number of trials attempted.
        """
        return pstats.Stats(self.prf).__dict__["total_tt"] / num_of_runs

    # sorting options
    # 'calls', 'cumulative', 'filename', 'ncalls', 'pcalls', 'line', 'name', 'nfl' (name file line), 'stdname', 'time'
    def dumpSortedStats(self, sortby="cumulative", filename="prof.txt"):
        """
            Description: Dump the total statistics from this current profile to a
            file. Cleared by calls to reset. If running profile over multiple trials,
            this dumps cumulative runtime across all trials: use dumpAverageStats()
            instead.
        """
        with open(filename, "w") as f:
            sts = pstats.Stats(self.prf, stream=f)
            sts.sort_stats(sortby)
            sts.print_stats()

    def calcAvgStatsHelper(self, obj, num_of_runs):
        for stat in obj:
            lst = []
            for val in range(0, 4):
                if val < 2:
                    var = int(obj[stat][val]) // num_of_runs
                    lst.append(var)
                else:
                    lst.append(obj[stat][val] / num_of_runs)
            if len(obj[stat]) > 4:
                lst.append(obj[stat][4])

            obj[stat] = tuple(lst)
            if len(obj[stat]) > 4 and obj[stat][4] is not {}:
                self.calcAvgStatsHelper(obj[stat][4], num_of_runs)

    def dumpAverageStats(
        self, sortby="cumulative", filename="avg_prof.txt", num_of_runs=1
    ):
        """
            Description: Dump the average runtime statistics from this current profile to a
            file. Cleared by calls to reset. All runtimes and statistics for every function call
            is averaged over num_of_runs.
        """
        with open(filename, "w") as f:
            f.write("\n\n Averaged over {} trials \n\n".format(num_of_runs))
            sts = pstats.Stats(self.prf, stream=f)
            if num_of_runs != 1:
                self.calcAvgStatsHelper(sts.__dict__["stats"], num_of_runs)
                sts.__dict__["total_tt"] = sts.__dict__["total_tt"] / num_of_runs
                sts.__dict__["total_calls"] = sts.__dict__["total_calls"] // num_of_runs
                sts.__dict__["prim_calls"] = sts.__dict__["prim_calls"] // num_of_runs
            sts.sort_stats(sortby)
            sts.print_stats()

    # collect data like max/min/median for output


# TODO: function for calling profile n times with a particular endpoint
# TODO: output data for later visualization


# profile wrapper
def profile(funct):
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()

        ret = funct(*args, **kwargs)

        pr.disable()
        s = io.StringIO()
        sortby = "cumulative"
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())

        return ret

    return wrapper
