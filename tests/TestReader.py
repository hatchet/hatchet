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
    filename = sys.argv[1]
    dbr = HPCTDBReader(filename)

    for loadm in (dbr.getLoadModuleTable()).iter('LoadModule'):
	print loadm.attrib
    print ""

    for filename in (dbr.getFileTable()).iter('File'):
	print filename.attrib
    print ""

    for procedure in (dbr.getProcedureTable()).iter('Procedure'):
	print procedure.attrib
    print ""

    for elem in (dbr.getCallPathProfile()).iter():
	print elem.attrib
    print ""

    metrics = dbr.readMetricDBFiles()

    print metrics[0]
