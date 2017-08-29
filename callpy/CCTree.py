#!/usr/bin/env python

##############################################################################
# Copyright (c) 2017, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# Written by:
#     Abhinav Bhatele <bhatele@llnl.gov>
#
# LLNL-CODE-XXXXXX. All rights reserved.
##############################################################################

from HPCTDBReader import *
from CCNode import *

class CCTree:

    def __init__(self, dirname):
        dbr = HPCTDBReader(dirname)

        self.numPes = dbr.numPes
        self.numNodes = dbr.numNodes
        self.numMetrics = dbr.numMetrics

        self.loadModules = {}
        self.files = {}
        self.procedures = {}

        # create dicts of load modules, files and procedures
        for loadm in (dbr.getLoadModuleTable()).iter('LoadModule'):
            self.loadModules[loadm.get('i')] = loadm.get('n')

        for filename in (dbr.getFileTable()).iter('File'):
            self.files[filename.get('i')] = filename.get('n')

        for procedure in (dbr.getProcedureTable()).iter('Procedure'):
            self.procedures[procedure.get('i')] = procedure.get('n')

        self.metrics = dbr.readMetricDBFiles()
        # print np.shape(self.metrics)
        self.metmin = np.amin(self.metrics, axis=2)
        self.metavg = np.mean(self.metrics, axis=2)
        self.metmax = np.amax(self.metrics, axis=2)

        # parse the ElementTree to generate a calling context tree
        root = dbr.getCallPathProfile().findall('PF')[0]
        nid = int(root.get('i'))
        val = np.empty([self.numMetrics, 3])
        for i in range(0, self.numMetrics):
            val[i][0] = self.metmin[i][nid-1]
            val[i][1] = self.metavg[i][nid-1]
            val[i][2] = self.metmax[i][nid-1]

        self.root = CCNode(nid, root.get('s'), root.get('l'), val, root.get('n'), root.get('lm'), root.get('f'))

        # start tree construction at the root
        self.parseXMLChildren(root, self.root)
        print "Tree created"


    # parse all children of an XML node
    def parseXMLChildren(self, xmlNode, ccNode):
        for xmlChild in xmlNode.getchildren():
            if xmlChild.tag != 'M':
                self.parseXMLNode(xmlChild, ccNode)


    # parse an XML node and its children recursively
    def parseXMLNode(self, xmlNode, ccParent):
        nid = int(xmlNode.get('i'))
        val = np.empty([self.numMetrics, 3])
        for i in range(0, self.numMetrics):
            val[i][0] = self.metmin[i][nid-1]
            val[i][1] = self.metavg[i][nid-1]
            val[i][2] = self.metmax[i][nid-1]

        xmltag = xmlNode.tag
        if xmltag == 'PF':
            ccNode = CCNode(nid, xmlNode.get('s'), xmlNode.get('l'), val, name=xmlNode.get('n'), loadm=xmlNode.get('lm'), filen=xmlNode.get('f'))
        elif xmltag == 'Pr':
            ccNode = CCNode(nid, xmlNode.get('s'), xmlNode.get('l'), val, name=xmlNode.get('n'), loadm=xmlNode.get('lm'), filen=xmlNode.get('f'))
        elif xmltag == 'C':
            ccNode = CCNode(nid, xmlNode.get('s'), xmlNode.get('l'), val)
        elif xmltag == 'L':
            ccNode = CCNode(nid, xmlNode.get('s'), xmlNode.get('l'), val, filen=xmlNode.get('f'))
        elif xmltag == 'S':
            ccNode = CCNode(nid, xmlNode.get('s'), xmlNode.get('l'), val)

        ccParent.add_child(ccNode)
        self.parseXMLChildren(xmlNode, ccNode)

