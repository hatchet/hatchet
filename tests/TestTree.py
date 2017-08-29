##############################################################################
# Copyright (c) 2017, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# Written by:
#     Abhinav Bhatele <bhatele@llnl.gov>
#
# LLNL-CODE-XXXXXX. All rights reserved.
##############################################################################

#!/usr/bin/env python

import sys
from callpy import *

if __name__ == "__main__":
    dirname = sys.argv[1]
    cct = CCTree(dirname)

