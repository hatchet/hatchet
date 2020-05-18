#!/usr/bin/env python

import hatchet as ht


if __name__ == "__main__":
    gf = ht.GraphFrame.from_gprof_dot(
        "../../hatchet/tests/data/gprof2dot-cpi/callgrind.dot.64042.0.1"
    )

    print(gf.dataframe)
    print(gf.tree())
