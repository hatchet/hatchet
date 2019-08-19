#!/usr/bin/env python
#
# Copyright 2017-2019 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from __future__ import print_function

import pandas as pd

import hatchet as ht

pd.set_option("display.width", 500)
pd.set_option("display.max_colwidth", 30)


if __name__ == "__main__":
    gf = ht.GraphFrame()
    gf.from_literal(
        [
            {
                "name": "foo",
                "metrics": {"time (inc)": 130.0, "time": 0.0},
                "children": [
                    {
                        "name": "bar",
                        "metrics": {"time (inc)": 20.0, "time": 5.0},
                        "children": [
                            {
                                "name": "baz",
                                "metrics": {"time (inc)": 5.0, "time": 5.0},
                            },
                            {
                                "name": "grault",
                                "metrics": {"time (inc)": 10.0, "time": 10.0},
                            },
                        ],
                    },
                    {
                        "name": "qux",
                        "metrics": {"time (inc)": 60.0, "time": 0.0},
                        "children": [
                            {
                                "name": "quux",
                                "metrics": {"time (inc)": 60.0, "time": 5.0},
                                "children": [
                                    {
                                        "name": "corge",
                                        "metrics": {"time (inc)": 55.0, "time": 10.0},
                                        "children": [
                                            {
                                                "name": "bar",
                                                "metrics": {
                                                    "time (inc)": 20.0,
                                                    "time": 5.0,
                                                },
                                                "children": [
                                                    {
                                                        "name": "baz",
                                                        "metrics": {
                                                            "time (inc)": 5.0,
                                                            "time": 5.0,
                                                        },
                                                    },
                                                    {
                                                        "name": "grault",
                                                        "metrics": {
                                                            "time (inc)": 10.0,
                                                            "time": 10.0,
                                                        },
                                                    },
                                                ],
                                            },
                                            {
                                                "name": "grault",
                                                "metrics": {
                                                    "time (inc)": 10.0,
                                                    "time": 10.0,
                                                },
                                            },
                                            {
                                                "name": "garply",
                                                "metrics": {
                                                    "time (inc)": 15.0,
                                                    "time": 15.0,
                                                },
                                            },
                                        ],
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "name": "waldo",
                        "metrics": {"time (inc)": 50.0, "time": 0.0},
                        "children": [
                            {
                                "name": "fred",
                                "metrics": {"time (inc)": 35.0, "time": 5.0},
                                "children": [
                                    {
                                        "name": "plugh",
                                        "metrics": {"time (inc)": 5.0, "time": 5.0},
                                    },
                                    {
                                        "name": "xyzzy",
                                        "metrics": {"time (inc)": 25.0, "time": 5.0},
                                        "children": [
                                            {
                                                "name": "thud",
                                                "metrics": {
                                                    "time (inc)": 25.0,
                                                    "time": 5.0,
                                                },
                                                "children": [
                                                    {
                                                        "name": "baz",
                                                        "metrics": {
                                                            "time (inc)": 5.0,
                                                            "time": 5.0,
                                                        },
                                                    },
                                                    {
                                                        "name": "garply",
                                                        "metrics": {
                                                            "time (inc)": 15.0,
                                                            "time": 15.0,
                                                        },
                                                    },
                                                ],
                                            }
                                        ],
                                    },
                                ],
                            },
                            {
                                "name": "garply",
                                "metrics": {"time (inc)": 15.0, "time": 15.0},
                            },
                        ],
                    },
                ],
            }
        ]
    )

    print(gf.dataframe)
    print("\n")

    print(gf.graph.to_string(gf.graph.roots, gf.dataframe, threshold=0.0))
