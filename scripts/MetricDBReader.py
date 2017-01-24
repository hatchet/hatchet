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

import glob
import struct
import numpy as np
# np.set_printoptions(threshold=np.inf)

# Read all .metric-db files in the current directory
mdbfiles = glob.glob('*.metric-db')
numPes = len(mdbfiles)

# Read header from one of the .metric-db files
metricdb = open(mdbfiles[0], "rb")

tag = metricdb.read(18)
version = metricdb.read(5)
endian = metricdb.read(1)

# Big endian
if endian == 'b':
    numNodes = struct.unpack('>i', metricdb.read(4))[0]
    numMetrics = struct.unpack('>i', metricdb.read(4))[0]
# TODO: complete for litte endian

metricdb.close()

print "Tag: %s Version: %s Endian: %s" % (tag, version, endian)
print "Files: %d Nodes: %d Metrics: %d" % (numPes, numNodes, numMetrics)

# Create a single metrics array
metrics = np.empty([numPes, numNodes, numMetrics])

for index, filename in enumerate(mdbfiles):
    metricdb = open(filename, "rb")
    # skip header of 32 bytes
    metricdb.seek(32)
    # currently assumes a big endian binary and reads all the metrics at once
    # into a numpy array
    arr = np.fromfile(metricdb, dtype=np.dtype('>f8'), count=numNodes*numMetrics)
    metrics[index] = arr.reshape(numNodes, numMetrics)
    # alternate method of reading the file one metric at a time
    # for i in range(0, numNodes):
    #     for j in range(0, numMetrics):
    #         print struct.unpack('>d', metricdb.read(8))[0],
    #     print ""
    metricdb.close()

# print metrics[numPes-1]
