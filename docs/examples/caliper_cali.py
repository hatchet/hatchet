#!/usr/bin/env python

import hatchet as ht


if __name__ == "__main__":
    cali_file = "../../hatchet/tests/data/caliper-cali/caliper-ex.cali"

    grouping_attribute = "function"
    default_metric = "sum(sum#time.duration),inclusive_sum(sum#time.duration)"
    query = "select function,%s group by %s format json-split" % (
        default_metric,
        grouping_attribute,
    )

    gf = ht.GraphFrame.from_caliper(cali_file, query)

    print(gf.dataframe)
    print(gf.tree(metric_column="time (inc)"))
