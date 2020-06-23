from hatchet.util.profiler import Profiler
import os
import pstats


def test_start():
    y = 0
    prf = Profiler()
    prf.start()

    for x in range(0, 100):
        y += x

    prf.end()

    t2 = pstats.Stats(prf.prf).__dict__["total_tt"]
    t3 = pstats.Stats(prf.prf).__dict__["total_tt"]

    assert t2 == t3


def test_reset():
    y = 0
    prf = Profiler()

    prf.start()
    for x in range(0, 100):
        y += x
    prf.end()
    t0 = pstats.Stats(prf.prf).__dict__["total_tt"]

    prf.reset()

    prf.start()
    for x in range(0, 5000):
        y += x
    prf.end()
    t1 = pstats.Stats(prf.prf).__dict__["total_tt"]

    assert t0 != t1


def test_get_runtime():
    y = 0
    prf = Profiler()
    prf.start()
    for x in range(0, 100):
        y += x
    prf.end()

    t0 = pstats.Stats(prf.prf).__dict__["total_tt"]
    t1 = prf.getRuntime()

    assert t0 == t1


def test_get_average_runtime():
    y = 0
    numtrials = 5
    prf = Profiler()
    for x in range(0, numtrials):
        prf.start()
        for x in range(0, 100):
            y += x
        prf.end()

    t0 = pstats.Stats(prf.prf).__dict__["total_tt"] / numtrials
    t1 = prf.getAverageRuntime(numtrials)

    assert t0 == t1


def test_dump_sorted_stats():
    y = 0
    prf = Profiler()
    prf.start()
    for x in range(0, 100):
        y += x
    prf.end()

    prf.dumpSortedStats("cumulative", "profiler_test.txt")

    assert os.path.exists("profiler_test.txt")
    os.remove("profiler_test.txt")


def test_dump_average_stats():
    y = 0
    numtrials = 5
    prf = Profiler()
    for x in range(0, numtrials):
        prf.start()
        for x in range(0, 100):
            y += x
        prf.end()

    prf.dumpAverageStats("cumulative", "profiler_test.txt", numtrials)

    assert os.path.exists("profiler_test.txt")
    os.remove("profiler_test.txt")
