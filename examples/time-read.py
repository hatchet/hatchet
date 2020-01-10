#!/usr/bin/env python
#
# Copyright 2017-2020 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from __future__ import print_function
import argparse

from hatchet import GraphFrame


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="print timings for reading an HPCToolkit database"
    )
    parser.add_argument(
        "directory", metavar="DIRECTORY", action="store", help="directory to read"
    )
    args = parser.parse_args()

    reader = GraphFrame.from_hpctoolkit(args.directory)
