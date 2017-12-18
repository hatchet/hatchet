##############################################################################
# Copyright (c) 2017, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# Written by Abhinav Bhatele <bhatele@llnl.gov>.
# LLNL-CODE-741008. All rights reserved.
#
# This file is part of Hatchet. For details, see:
# https://github.com/LLNL/hatchet
# Please also read the LICENSE file for the MIT License notice.
##############################################################################

#!/usr/bin/env python

from hatchet import *

if __name__ == "__main__":
    dirname = sys.argv[1]

    cct = CCTree(dirname, 'hpctoolkit')
    cct.print_tree(cct.root, _unicode=True, _color=True)
