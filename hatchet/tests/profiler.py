import pstats
import os
from hatchet.util.profiler import Profiler


def f():
    for i in range(1000):
        for j in range(1000):
            i * j


def test_start():
    prf = Profiler()
    prf.start()
    prf.end()
    t_1 = prf.getRuntime()

    prf.start()
    f()
    prf.end()
    t_2 = prf.getRuntime()
    assert t_1 != t_2


def test_end():
    prf = Profiler()
    prf.start()
    f()
    prf.end()
    t_1 = pstats.Stats(prf.prf).__dict__["total_tt"]
    t_2 = pstats.Stats(prf.prf).__dict__["total_tt"]
    assert t_1 == t_2


def test_reset():
    prf = Profiler()
    prf.start()
    f()
    prf.end()
    prf.reset()

    assert {} == prf.prf.__dict__


def test_getters():
    runs = 3

    prf = Profiler()
    for i in range(runs):
        prf.start()
        f()
        prf.end()

    assert prf.getRuntime() == pstats.Stats(prf.prf).__dict__["total_tt"]
    assert (
        prf.getAverageRuntime(runs) == pstats.Stats(prf.prf).__dict__["total_tt"] / runs
    )
    assert prf.getRuntime() != prf.getAverageRuntime(runs)


def test_f_output():
    runs = 3
    file = "test.txt"
    prf = Profiler()
    global f

    for i in range(runs):
        prf.start()
        f()
        prf.end()

    prf.dumpAverageStats("cumulative", file, runs)
    assert os.path.exists(file)

    with open(file, "r") as f:
        lines = f.readlines()

    assert "Averaged over {} trials".format(runs) in lines[2]

    os.remove(file)
