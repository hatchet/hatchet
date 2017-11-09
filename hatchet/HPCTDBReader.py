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
from CCNode import *

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

filename = 0


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
        self.metmin = np.empty([self.numMetrics, self.numNodes])
        self.metavg = np.empty([self.numMetrics, self.numNodes])
        self.metmax = np.empty([self.numMetrics, self.numNodes])

    def fillTables(self):
        loadModules = {}
        files = {}
        procedures = {}

        # create dicts of load modules, files and procedures
        for loadm in (self.LoadModuleTable).iter('LoadModule'):
            loadModules[loadm.get('i')] = loadm.get('n')

        for filename in (self.FileTable).iter('File'):
            files[filename.get('i')] = filename.get('n')

        for procedure in (self.ProcedureTable).iter('Procedure'):
            procedures[procedure.get('i')] = procedure.get('n')

        return loadModules, files, procedures

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

        # Also calculate min, avg, max metrics for each node
        self.metmin = np.amin(self.metrics, axis=2)
        self.metavg = np.mean(self.metrics, axis=2)
        self.metmax = np.amax(self.metrics, axis=2)

        return self.metrics

    def createCCTree(self):
        # parse the ElementTree to generate a calling context tree
        root = self.CallPathProfile.findall('PF')[0]
        nid = int(root.get('i'))

        metrics = np.empty([self.numMetrics, 3])
        for i in range(0, self.numMetrics):
            metrics[i][0] = self.metmin[i][nid-1]
            metrics[i][1] = self.metavg[i][nid-1]
            metrics[i][2] = self.metmax[i][nid-1]

        cct_root = CCNode(nid, root.get('s'), root.get('l'), metrics, 'PF',
                          root.get('n'), root.get('lm'), root.get('f'))

        # start tree construction at the root
        self.parseXMLChildren(root, cct_root)
        return cct_root

    def parseXMLChildren(self, xmlNode, ccNode):
        """ Parses all children of an XML node.
        """
        for xmlChild in xmlNode.getchildren():
            if xmlChild.tag != 'M':
                self.parseXMLNode(xmlChild, ccNode)

    def parseXMLNode(self, xmlNode, ccParent):
        """ Parses an XML node and its children recursively.
        """
        nid = int(xmlNode.get('i'))

        metrics = np.empty([self.numMetrics, 3])
        for i in range(0, self.numMetrics):
            metrics[i][0] = self.metmin[i][nid-1]
            metrics[i][1] = self.metavg[i][nid-1]
            metrics[i][2] = self.metmax[i][nid-1]

        global filename
        xmltag = xmlNode.tag

        if xmltag == 'PF':
            ccNode = CCNode(nid, xmlNode.get('s'), xmlNode.get('l'), metrics,
                            xmltag, xmlNode.get('n'), xmlNode.get('lm'),
                            xmlNode.get('f'))
            filename = xmlNode.get('f')
        elif xmltag == 'Pr':
            ccNode = CCNode(nid, xmlNode.get('s'), xmlNode.get('l'), metrics,
                            xmltag, xmlNode.get('n'), xmlNode.get('lm'),
                            xmlNode.get('f'))
            filename = xmlNode.get('f')
        elif xmltag == 'L':
            ccNode = CCNode(nid, xmlNode.get('s'), xmlNode.get('l'), metrics,
                            xmltag, src_file=xmlNode.get('f'))
            filename = xmlNode.get('f')
        # elif xmltag == 'C':
            # ccNode = CCNode(nid, xmlNode.get('s'), xmlNode.get('l'), metrics,
            #                 xmltag)
        elif xmltag == 'S':
            ccNode = CCNode(nid, xmlNode.get('s'), xmlNode.get('l'), metrics,
                            xmltag, src_file=filename)

        if xmltag == 'C' or (xmltag == 'Pr' and
                             self.procedures[xmlNode.get('n')] == ""):
            # do not add a node to the tree
            self.parseXMLChildren(xmlNode, ccParent)
        else:
            ccParent.add_child(ccNode)
            self.parseXMLChildren(xmlNode, ccNode)

