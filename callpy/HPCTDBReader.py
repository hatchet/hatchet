##############################################################################
# Copyright (c) 2017, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# Written by:
#     Abhinav Bhatele <bhatele@llnl.gov>
#
# LLNL-CODE-XXXXXX. All rights reserved.
##############################################################################

import glob
import struct
import numpy as np

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


class HPCTDBReader:
    """
    Read in the various sections of an HPCToolkit experiment.xml file
    and metric-db files
    """

    def __init__(self, dirname):
        self.dirname = dirname

        root = ET.parse(self.dirname + '/experiment.xml').getroot()
        self.LoadModuleTable = root.iter('LoadModuleTable').next()
        self.FileTable = root.iter('FileTable').next()
        self.ProcedureTable = root.iter('ProcedureTable').next()
        self.CallPathProfile = root.iter('SecCallPathProfileData').next()

        mdbfiles = glob.glob(self.dirname + '/*.metric-db')
        self.numPes = len(mdbfiles)

        metricdb = open(mdbfiles[0], "rb")
        tag = metricdb.read(18)
        version = metricdb.read(5)
        endian = metricdb.read(1)

        if endian == 'b':
            self.numNodes = struct.unpack('>i', metricdb.read(4))[0]
            self.numMetrics = struct.unpack('>i', metricdb.read(4))[0]

        metricdb.close()
        self.metrics = np.empty([self.numMetrics, self.numNodes, self.numPes])

    def readMetricDBFiles(self):
        mdbfiles = glob.glob(self.dirname + '/*.metric-db')

        # assumes that glob returns a sorted order
        for pe, filename in enumerate(mdbfiles):
            metricdb = open(filename, "rb")
            metricdb.seek(32)
            arr = np.fromfile(metricdb, dtype=np.dtype('>f8'),
                              count=self.numNodes * self.numMetrics)
            # inclusive time
            metric1 = arr[0::2]
            # exclusive time
            metric2 = arr[1::2]
            for i in range(0, len(metric1)):
                self.metrics[0][i][pe] = metric1[i]
                self.metrics[1][i][pe] = metric2[i]
            metricdb.close()

        return self.metrics

