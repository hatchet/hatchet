#!/usr/bin/env python

import subprocess
import hatchet as ht


if __name__ == "__main__":
    cali_file = "../../hatchet/tests/data/caliper-cali/caliper-ex.cali"

    cali_query = "cali-query"
    grouping_attribute = "function"
    default_metric = "sum(sum#time.duration),inclusive_sum(sum#time.duration)"
    query = "select function,%s group by %s format json-split" % (
        default_metric,
        grouping_attribute,
    )

    cali_json = subprocess.Popen(
        [cali_query, "-q", query, cali_file], stdout=subprocess.PIPE
    )

    gf = ht.GraphFrame.from_caliper_json(cali_json.stdout)

    print(gf.dataframe)
    print(gf.tree(metric_column="time (inc)"))
