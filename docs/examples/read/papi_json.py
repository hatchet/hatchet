#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import hatchet as ht


if __name__ == "__main__":
    # Define a literal GraphFrame
    #gf = ht.GraphFrame.from_papi("/home/fwinkler/applications/papi_hybrid/papi_hl_output")
    gf = ht.GraphFrame.from_papi("/home/fwinkler/rank_000000.json", ['kokkosp_parallel_for', 'kokkosp_deep_copy', 'kokkosp_parallel_scan', 'kokkosp_parallel_reduce'])

    # Printout the DataFrame component of the GraphFrame.
    #print(gf.dataframe.to_string())
    print(gf.dataframe)

    # Printout the graph component of the GraphFrame.
    # for rank in range(0, 2):
    #   for thread in range(0, 2):
    #     print("\nrank={}, thread={}".format(rank, thread))
    #     print(gf.tree(metric_column="real_time_nsec", rank=rank, thread=thread))

    print(gf.tree(metric_column="real_time_nsec"))
    # print(gf.tree(metric_column="PAPI_TOT_INS"))
    # print(gf.tree(metric_column="PAPI_TOT_CYC"))
    # print(gf.tree(metric_column="PAPI_FP_INS"))
    # print(gf.tree(metric_column="rocm:::TCC_HIT_sum:device=0"))
    # print(gf.tree(metric_column="rocm:::TCC_MISS_sum:device=0"))
    # print(gf.tree(metric_column="rocm:::L2CacheHit:device=0"))