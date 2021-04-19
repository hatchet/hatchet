#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import hatchet as ht


if __name__ == "__main__":
    # Define a literal GraphFrame
    gf = ht.GraphFrame.from_papi("../../../hatchet/tests/data/papi_hl_output")

    # Printout the DataFrame component of the GraphFrame.
    print(gf.dataframe)

    # Printout the graph component of the GraphFrame.
    # Use "PAPI_FP_OPS" as the metric column to be displayed
    print(gf.tree(metric_column="PAPI_FP_OPS"))