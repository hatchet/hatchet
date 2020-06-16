#!/usr/bin/env python

import subprocess
import hatchet as ht


if __name__ == "__main__":
    # Path to caliper json-split file.
    json_file = "../../hatchet/tests/data/caliper-cpi-json/cpi-sample-callpathprofile.json"

    # Use hatchet's ``from_caliper_json`` API with the resulting json-split.
    # The result is stored into Hatchet's GraphFrame.
    gf = ht.GraphFrame.from_caliper_json(json_file)

    # Printout the DataFrame component of the GraphFrame.
    print(gf.dataframe)
    print("\n")

    # Printout the graph component of the GraphFrame. Specifically, enable
    # coloring, and only show those nodes with a positive ``time (inc)`` value.
    print(gf.tree(color=True, threshold=0.0, metric="time (inc)"))
