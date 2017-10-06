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
from hatchet import *

if __name__ == "__main__":
    dirname = sys.argv[1]
    dbr = HPCTDBReader(dirname)

    for loadm in (dbr.LoadModuleTable).iter('LoadModule'):
        print loadm.attrib
    print ""

    for filename in (dbr.FileTable).iter('File'):
        print filename.attrib
    print ""

    for procedure in (dbr.ProcedureTable).iter('Procedure'):
        print procedure.attrib
    print ""

    for elem in (dbr.CallPathProfile).iter():
        print elem.attrib
    print ""

    metrics = dbr.readMetricDBFiles()

    print metrics
