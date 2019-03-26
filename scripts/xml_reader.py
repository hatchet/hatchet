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

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

tree = ET.parse('experiment.xml')
root = tree.getroot()

# Root
print root.tag, root.attrib

# Root[0] - Header
print "\t", root[0].tag, root[0].attrib
for child in root[0]:
    print "\t\t", child.tag, child.attrib

# Root[0][0] - Info (empty)
# for elem in root[0][0].iter():
#     print elem.tag, elem.attrib

# Root[1] - SecCallPathProfile
print "\t", root[1].tag, root[1].attrib
for child in root[1]:
    print "\t\t", child.tag, child.attrib
print ""

# Root[1][0] - SecHeader
# Children - MetricTable, MetricDBTable, TraceDBTable, LoadModuleTable,
#            FileTable, ProcedureTable
for loadm in root[1][0][3].iter('LoadModule'):
    print loadm.attrib
print ""

for filename in root[1][0][4].iter('File'):
    print filename.attrib
print ""

for procedure in root[1][0][5].iter('Procedure'):
    print procedure.attrib
print ""

# Root[1][1] - SecCallPathProfileData
for elem in root[1][1].iter():
    print elem.tag, elem.attrib
