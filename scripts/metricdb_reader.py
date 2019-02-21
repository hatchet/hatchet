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

#!/usr/bin/env python

import glob
import struct
import numpy as np
# np.set_printoptions(threshold=np.inf)

# Read all .metric-db files in the current directory
mdbfiles = glob.glob('*.metric-db')
num_pes = len(mdbfiles)

# Read header from one of the .metric-db files
metricdb = open(mdbfiles[0], "rb")

tag = metricdb.read(18)
version = metricdb.read(5)
endian = metricdb.read(1)

# Big endian
if endian == 'b':
    num_nodes = struct.unpack('>i', metricdb.read(4))[0]
    num_metrics = struct.unpack('>i', metricdb.read(4))[0]
# TODO: complete for litte endian

metricdb.close()

print "Tag: %s Version: %s Endian: %s" % (tag, version, endian)
print "Files: %d Nodes: %d Metrics: %d" % (num_pes, num_nodes, num_metrics)

# Create a single metrics array
metrics = np.empty([num_pes, num_nodes, num_metrics])

for index, filename in enumerate(mdbfiles):
    metricdb = open(filename, "rb")
    # skip header of 32 bytes
    metricdb.seek(32)
    # currently assumes a big endian binary and reads all the metrics at once
    # into a numpy array
    arr = np.fromfile(metricdb, dtype=np.dtype('>f8'),
                      count = num_nodes * num_metrics)
    metrics[index] = arr.reshape(num_nodes, num_metrics)
    # alternate method of reading the file one metric at a time
    # for i in range(0, num_nodes):
    #     for j in range(0, num_metrics):
    #         print struct.unpack('>d', metricdb.read(8))[0],
    #     print ""
    metricdb.close()

# print metrics[num_pes-1]
