#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import hatchet as ht


if __name__ == "__main__":
    # Define a literal GraphFrame using a list of dicts.
    gf = ht.GraphFrame.from_papi([])

    # Printout the DataFrame component of the GraphFrame.
    #print(gf.dataframe.to_string())
    print(gf.dataframe)

    # Printout the graph component of the GraphFrame.
    print(gf.tree(metric_column="perf::TASK-CLOCK", rank=0, thread=0))