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

filename = 0


class CCTree:
    """ A single tree that includes the root node and other performance data
        associated with this tree.
    """

    def __init__(self, dirname):
        dbr = HPCTDBReader(dirname)

        self.numPes = dbr.numPes
        self.numNodes = dbr.numNodes
        self.numMetrics = dbr.numMetrics

        self.loadModules = {}
        self.files = {}
        self.procedures = {}

        # create dicts of load modules, files and procedures
        for loadm in (dbr.LoadModuleTable).iter('LoadModule'):
            self.loadModules[loadm.get('i')] = loadm.get('n')

        for filename in (dbr.FileTable).iter('File'):
            self.files[filename.get('i')] = filename.get('n')

        for procedure in (dbr.ProcedureTable).iter('Procedure'):
            self.procedures[procedure.get('i')] = procedure.get('n')

        self.metrics = dbr.readMetricDBFiles()
        # print np.shape(self.metrics)
        self.metmin = np.amin(self.metrics, axis=2)
        self.metavg = np.mean(self.metrics, axis=2)
        self.metmax = np.amax(self.metrics, axis=2)

        # parse the ElementTree to generate a calling context tree
        root = dbr.CallPathProfile.findall('PF')[0]
        nid = int(root.get('i'))
        metrics = np.empty([self.numMetrics, 3])
        for i in range(0, self.numMetrics):
            metrics[i][0] = self.metmin[i][nid-1]
            metrics[i][1] = self.metavg[i][nid-1]
            metrics[i][2] = self.metmax[i][nid-1]

        self.root = CCNode(nid, root.get('s'), root.get('l'), metrics, 'PF',
                           root.get('n'), root.get('lm'), root.get('f'))

        # start tree construction at the root
        self.parseXMLChildren(root, self.root)
        print "Tree created"

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

    def getNodeName(self, ccNode):
        """ Returns a string to be displayed in the ETE tree.
        """
        if ccNode.node_type == 'PF' or ccNode.node_type == 'Pr':
            return self.procedures[ccNode.name]
        elif ccNode.node_type == 'L':
            return "Loop@" + (self.files[ccNode.src_file]).rpartition('/')[2] + ":" + ccNode.line
        elif ccNode.node_type == 'S':
            return (self.files[ccNode.src_file]).rpartition('/')[2] + ":" + ccNode.line

    def traverse(self, ccnode):
        """Traverse the tree depth-first and yield each node."""
        yield ccnode

        for child in ccnode.children:
            for rc in self.traverse(child):
                yield rc
