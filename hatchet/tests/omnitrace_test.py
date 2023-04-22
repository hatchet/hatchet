# Copyright 2020-2023 The Regents of the University of California, through
# Lawrence Berkeley National Laboratory, and other Hatchet Project Developers.
# See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from hatchet import GraphFrame
from hatchet.external.console import ConsoleRenderer

import pytest

perfetto_avail = True
try:
    # add noqa to line below because we need to disable these tests
    # for python < 3.6 because perfetto is not available. we do
    # not use this import locally because it is used inside
    # the PerfettoReader
    import perfetto  # noqa: F401
except ImportError:
    perfetto_avail = False


@pytest.mark.skipif(not perfetto_avail, reason="perfetto package not available")
def test_graphframe_python_source(omnitrace_python_source):
    """Validation test a GraphFrame object with known single rank, single thread data."""

    gf = GraphFrame.from_omnitrace(omnitrace_python_source)

    assert len(gf.dataframe) == 59

    gf = gf.squash()

    assert len(gf.dataframe) == 9


@pytest.mark.skipif(not perfetto_avail, reason="perfetto package not available")
def test_graphframe_mpi_aggregate(omnitrace_mpi_aggregate):
    """Validation test a GraphFrame object with multiple rank, multiple thread data in single file."""

    gf = GraphFrame.from_omnitrace(
        omnitrace_mpi_aggregate,
        include_category=["host", "pthread", "mpi"],
        exclude_category=["pthread", "mpi"],
        verbose=3,
        report=["all"],
    )

    assert len(gf.dataframe) == 32

    gf = gf.squash()

    assert len(gf.dataframe) == 8


@pytest.mark.skipif(not perfetto_avail, reason="perfetto package not available")
def test_graphframe_mpi_single(omnitrace_mpi_single):
    """Validation test a GraphFrame object with single rank, multiple thread data."""

    gf = GraphFrame.from_omnitrace(
        omnitrace_mpi_single, include_category=["host"], verbose=3, report=["none"]
    )

    assert len(gf.dataframe) == 672

    gf = gf.squash()

    assert len(gf.dataframe) == 74


@pytest.mark.skipif(not perfetto_avail, reason="perfetto package not available")
def test_graphframe_mpi_group(omnitrace_mpi_group):
    """Validation test a GraphFrame object with multiple rank, multiple thread data where data for each rank is in a separate file."""

    gf = GraphFrame.from_omnitrace(
        omnitrace_mpi_group, include_category=["host"], verbose=0, report=["all"]
    )

    assert len(gf.dataframe) == 8640

    gf = gf.squash()

    assert len(gf.dataframe) == 1088


@pytest.mark.skipif(not perfetto_avail, reason="perfetto package not available")
def test_sampling_mpi_group(omnitrace_mpi_group):
    """Validate sampling data is preserved (each file has variable number of gotcha_wrap instances)"""

    gf = GraphFrame.from_omnitrace(
        omnitrace_mpi_group,
        include_category=["timer_sampling"],
        verbose=0,
        report=["all"],
    )

    output = ConsoleRenderer(unicode=True, color=False).render(
        gf.graph.roots,
        gf.dataframe,
        metric_column="time.inc",
        precision=3,
        name_column="name",
        expand_name=True,
        context_column="file",
        rank=0,
        thread=0,
        depth=10000,
        highlight_name=False,
        colormap="RdYlGn",
        invert_colormap=False,
    )

    output_v = "{}".format(output).split("\n")
    matching_lines = [x.strip() if "gotcha_wrap" in x else None for x in output_v]
    matching_count = sum([1 if x is not None else 0 for x in matching_lines])

    print(
        "matching 'gotcha_wrap' lines (n={}):\n    {}".format(
            matching_count, "\n    ".join([x for x in matching_lines if x is not None])
        )
    )

    assert matching_count == 385


@pytest.mark.skipif(not perfetto_avail, reason="perfetto package not available")
def test_tree_python_source(omnitrace_python_source):
    """Sanity test a GraphFrame object with known data."""
    gf = GraphFrame.from_omnitrace(omnitrace_python_source)

    print(gf.tree("time.inc"))
    gf.calculate_exclusive_metrics()

    output = ConsoleRenderer(unicode=True, color=False).render(
        gf.graph.roots,
        gf.dataframe,
        metric_column="time",
        precision=3,
        name_column="name",
        expand_name=False,
        context_column="file",
        rank=0,
        thread=0,
        depth=10000,
        highlight_name=False,
        colormap="RdYlGn",
        invert_colormap=False,
    )

    print(output)


@pytest.mark.skipif(not perfetto_avail, reason="perfetto package not available")
def test_tree_mpi_aggregate(omnitrace_mpi_aggregate):
    """Sanity test a GraphFrame object with known data."""
    gf = GraphFrame.from_omnitrace(
        omnitrace_mpi_aggregate, include_category=["host"], verbose=0, report=["none"]
    )
    gf = gf.squash()
    gf.calculate_exclusive_metrics()

    print(gf.tree("time.inc"))

    output = ConsoleRenderer(unicode=True, color=False).render(
        gf.graph.roots,
        gf.dataframe,
        metric_column="time",
        precision=3,
        name_column="name",
        expand_name=False,
        context_column="file",
        rank=0,
        thread=0,
        depth=10000,
        highlight_name=False,
        colormap="RdYlGn",
        invert_colormap=False,
    )

    print(output)


@pytest.mark.skipif(not perfetto_avail, reason="perfetto package not available")
def test_tree_mpi_group(omnitrace_mpi_group):
    """Sanity test a GraphFrame object with known data."""
    gf = GraphFrame.from_omnitrace(
        omnitrace_mpi_group, include_category=["host"], verbose=0, report=["none"]
    )

    print(gf.tree("time.inc"))
    gf.calculate_exclusive_metrics()

    output = ConsoleRenderer(unicode=True, color=False).render(
        gf.graph.roots,
        gf.dataframe,
        metric_column="time",
        precision=3,
        name_column="name",
        expand_name=False,
        context_column="file",
        rank=0,
        thread=0,
        depth=10000,
        highlight_name=False,
        colormap="RdYlGn",
        invert_colormap=False,
    )

    print(output)


@pytest.mark.skipif(not perfetto_avail, reason="perfetto package not available")
def test_read_attribute_mpi_group(omnitrace_mpi_group):
    """Generate a graphframe with only host data and then re-read but include mpi and pthread category data"""
    gf = GraphFrame.from_omnitrace(
        omnitrace_mpi_group,
        include_category=["host"],
    )

    assert gf.selected_categories() == ["host"]
    assert gf.available_categories() == [
        "host",
        "mpi",
        "pthread",
        "timer_sampling",
    ]

    gf = gf.read(include_category=["host", "mpi", "pthread"]).squash()

    assert gf.selected_categories() == ["host", "mpi", "pthread"]

    assert len(gf.dataframe) == 1856


@pytest.mark.skipif(not perfetto_avail, reason="perfetto package not available")
def test_read_attribute_mpi_aggregate(omnitrace_mpi_aggregate):
    """Test the addition of "read" function attribute. ensure data is retained and works after garbage collection"""
    import gc

    gf = GraphFrame.from_omnitrace(
        omnitrace_mpi_aggregate, include_category=["host"], verbose=0, report=["none"]
    )

    assert gf.selected_categories() == ["host"]
    assert gf.available_categories() == [
        "host",
        "mpi",
        "overflow_sampling",
        "pthread",
        "timer_sampling",
    ]

    old_gf = gf.deepcopy()

    assert old_gf.selected_categories() == ["host"]
    assert old_gf.available_categories() == [
        "host",
        "mpi",
        "overflow_sampling",
        "pthread",
        "timer_sampling",
    ]

    gf = gf.read()
    gc.collect()  # make sure gf is still valid after garbage collection

    assert gf.selected_categories() == ["host"]
    assert gf.available_categories() == [
        "host",
        "mpi",
        "overflow_sampling",
        "pthread",
        "timer_sampling",
    ]
    assert len(gf.dataframe) == 32

    gf = gf.squash()
    gc.collect()
    gf.calculate_exclusive_metrics()

    assert len(gf.dataframe) == 8

    output = ConsoleRenderer(unicode=True, color=False).render(
        gf.graph.roots,
        gf.dataframe,
        metric_column="time",
        precision=3,
        name_column="name",
        expand_name=False,
        context_column="file",
        rank=0,
        thread=0,
        depth=10000,
        highlight_name=False,
        colormap="RdYlGn",
        invert_colormap=False,
    )

    print(output)


@pytest.mark.skipif(not perfetto_avail, reason="perfetto package not available")
def test_graphframe_to_literal(omnitrace_mpi_aggregate):
    """Test support for to_literal"""
    gf = GraphFrame.from_omnitrace(
        omnitrace_mpi_aggregate,
        exclude_category=["overflow_sampling", "timer_sampling"],
    ).squash()

    graph_literal = gf.to_literal()
    assert len(graph_literal) == len(gf.graph.roots)


@pytest.mark.skipif(not perfetto_avail, reason="perfetto package not available")
def test_default_metric(omnitrace_mpi_single):
    """Validation test for GraphFrame object using default metric field and to_{dot,flamegraph}"""
    gf = GraphFrame.from_omnitrace(
        omnitrace_mpi_single, exclude_category=["timer_sampling"]
    )

    for func in ["tree", "to_dot", "to_flamegraph"]:
        lhs = "{}\n{}".format(func, getattr(gf, func)(gf.default_metric))
        rhs = "{}\n{}".format(func, getattr(gf, func)())
        assert lhs == rhs
