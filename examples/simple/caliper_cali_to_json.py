#!/usr/bin/env python

import subprocess
import hatchet as ht


if __name__ == "__main__":
    # Path to caliper cali file.
    cali_file = "../../hatchet/tests/data/caliper-cali/caliper-ex.cali"

    # Setup desired cali query.
    cali_query = "cali-query"
    grouping_attribute = "function"
    default_metric = "sum(sum#time.duration),inclusive_sum(sum#time.duration)"
    query = "select function,%s group by %s format json-split" % (
        default_metric,
        grouping_attribute,
    )

    # Use ``cali-query`` here to produce the json-split stream.
    cali_json = subprocess.Popen(
        [cali_query, "-q", query, cali_file], stdout=subprocess.PIPE
    )

    # Use hatchet's ``from_caliper_json`` API with the resulting json-split.
    # The result is stored into Hatchet's GraphFrame.
    gf = ht.GraphFrame.from_caliper_json(cali_json.stdout)

    # Printout the DataFrame component of the GraphFrame.
    print(gf.dataframe)
    print("\n")

    # Printout the graph component of the GraphFrame. Specifically, enable
    # coloring, and only show those nodes with a positive ``time (inc)`` value.
    print(gf.tree(color=True, threshold=0.0, metric="time (inc)"))
