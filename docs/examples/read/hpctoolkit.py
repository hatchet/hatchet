#!/usr/bin/env python

import hatchet as ht


if __name__ == "__main__":
    # Path to HPCToolkit database directory.
    dirname = "../../hatchet/tests/data/hpctoolkit-cpi-database"

    # Use hatchet's ``from_hpctoolkit`` API to read in the HPCToolkit database.
    # The result is stored into Hatchet's GraphFrame.
    gf = ht.GraphFrame.from_hpctoolkit(dirname)

    # Printout the DataFrame component of the GraphFrame.
    print(gf.dataframe)
    print("\n")

    # Printout the graph component of the GraphFrame. Specifically, enable
    # coloring, and only show those nodes with a positive ``time`` value.
    # Because no metric parameter is specified, ``time`` is used by default.
    print(gf.tree(color=True, threshold=0.0))
