#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import hatchet as ht


if __name__ == "__main__":
    # Define a literal GraphFrame
    #gf = ht.GraphFrame.from_papi("/home/fwinkler/applications/papi_hybrid/papi_hl_output")
    gf = ht.GraphFrame.from_papi("/home/fwinkler/applications/papi_hybrid/papi_hl_output/rank_000000.json")
    #gf = ht.GraphFrame.from_papi("/home/fwinkler/applications/papi_simple/papi_hl_output/huhu")

    # Printout the DataFrame component of the GraphFrame.
    #print(gf.dataframe.to_string())
    print(gf.dataframe)

    # Printout the graph component of the GraphFrame.
    #print(gf.tree(metric_column="PAPI_TOT_CYC", rank=0, thread=0))
    print(gf.tree(metric_column="real_time_nsec", rank=0, thread=0))
    print(gf.tree(metric_column="perf::TASK-CLOCK", rank=0, thread=0))