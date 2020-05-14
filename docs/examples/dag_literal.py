#!/usr/bin/env python

import hatchet as ht


if __name__ == "__main__":
    gf = ht.GraphFrame.from_literal(
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
            },
            {
                "name": "ほげ (hoge)",
                "metrics": {"time (inc)": 30.0, "time": 0.0},
                "children": [
                    {
                        "name": "(ぴよ (piyo)",
                        "metrics": {"time (inc)": 15.0, "time": 5.0},
                        "children": [
                            {
                                "name": "ふが (fuga)",
                                "metrics": {"time (inc)": 5.0, "time": 5.0},
                            },
                            {
                                "name": "ほげら (hogera)",
                                "metrics": {"time (inc)": 5.0, "time": 5.0},
                            },
                        ],
                    },
                    {
                        "name": "ほげほげ (hogehoge)",
                        "metrics": {"time (inc)": 15.0, "time": 15.0},
                    },
                ],
            },
        ]
    )

    print(gf.dataframe)
    print("\n")

    print(gf.tree(threshold=0.0))
