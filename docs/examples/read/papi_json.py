#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import hatchet as ht


if __name__ == "__main__":
    # Define a literal GraphFrame using a list of dicts.
    gf = ht.GraphFrame.from_papi([])

    # Printout the DataFrame component of the GraphFrame.
    #print(gf.dataframe.to_string())

    # Printout the graph component of the GraphFrame.
    # Because no metric parameter is specified, ``time`` is used by default.
    #print(gf.tree(metric_column="region_count", rank=0, thread=0))
