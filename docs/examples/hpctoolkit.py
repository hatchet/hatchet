#!/usr/bin/env python

import hatchet as ht


if __name__ == "__main__":
    dirname = "../../hatchet/tests/data/hpctoolkit-cpi-database"
    gf = ht.GraphFrame.from_hpctoolkit(dirname)

    print(gf.dataframe)
    print("\n")

    print(gf.tree(threshold=0.0))
