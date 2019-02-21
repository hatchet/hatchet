#!/usr/bin/env python
##############################################################################
# Copyright (c) 2017-2019, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# This file is part of Hatchet.
# Created by Abhinav Bhatele <bhatele@llnl.gov>.
# LLNL-CODE-741008. All rights reserved.
#
# For details, see: https://github.com/LLNL/hatchet
# Please also read the LICENSE file for the MIT License notice.
##############################################################################
from __future__ import print_function
import argparse

from hatchet.hpctoolkit_reader import HPCToolkitReader


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='print timings for reading an HPCToolkit database')
    parser.add_argument('directory', metavar='DIRECTORY', action='store',
                        help='directory to read')
    args = parser.parse_args()

    reader = HPCToolkitReader(args.directory)
    reader.create_graph()
    print(str(reader.timer))
