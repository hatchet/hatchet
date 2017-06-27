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
        self.metrics = np.empty([self.numPes, self.numNodes, self.numMetrics])

    def getLoadModuleTable(self):
        return self.LoadModuleTable

    def getFileTable(self):
        return self.FileTable

    def getProcedureTable(self):
        return self.ProcedureTable

    def getCallPathProfile(self):
        return self.CallPathProfile

    def readMetricDBFiles(self):
        mdbfiles = glob.glob(self.dirname + '/*.metric-db')

        for index, filename in enumerate(mdbfiles):
            metricdb = open(filename, "rb")
            metricdb.seek(32)
            arr = np.fromfile(metricdb, dtype=np.dtype('>f8'), count=self.numNodes * self.numMetrics)
            self.metrics[index] = arr.reshape(self.numNodes, self.numMetrics)
            metricdb.close()

        return self.metrics

