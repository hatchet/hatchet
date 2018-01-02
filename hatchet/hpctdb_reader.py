##############################################################################
# Copyright (c) 2017, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# Written by Abhinav Bhatele <bhatele@llnl.gov>.
# LLNL-CODE-741008. All rights reserved.
#
# This file is part of Hatchet. For details, see:
# https://github.com/LLNL/hatchet
# Please also read the LICENSE file for the MIT License notice.
##############################################################################

import glob
import struct
import numpy as np
import pandas as pd

from ccnode import CCNode

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

src_file = 0


class HPCTDBReader:
    """
    Read in the various sections of an HPCToolkit experiment.xml file
    and metric-db files
    """

    def __init__(self, dir_name):
        self.dir_name = dir_name

        root = ET.parse(self.dir_name + '/experiment.xml').getroot()
        self.loadmodule_table = root.iter('LoadModuleTable').next()
        self.file_table = root.iter('FileTable').next()
        self.procedure_table = root.iter('ProcedureTable').next()
        self.metricdb_table = root.iter('MetricDBTable').next()
        self.callpath_profile = root.iter('SecCallPathProfileData').next()

        metricdb_files = glob.glob(self.dir_name + '/*.metric-db')
        self.num_pes = len(metricdb_files)

        metricdb = open(metricdb_files[0], "rb")
        tag = metricdb.read(18)
        version = metricdb.read(5)
        endian = metricdb.read(1)

        if endian == 'b':
            self.num_nodes = struct.unpack('>i', metricdb.read(4))[0]
            self.num_metrics = struct.unpack('>i', metricdb.read(4))[0]

        metricdb.close()

        self.metrics = np.empty([self.num_metrics,
                                 self.num_nodes,
                                 self.num_pes])
        self.metrics_avg = np.empty([self.num_metrics, self.num_nodes])

        self.load_modules = {}
        self.src_files = {}
        self.procedure_names = {}
        self.metric_names = {}

    def fill_tables(self):
        # create dicts of load modules, src_files and procedure_names
        for loadm in (self.loadmodule_table).iter('LoadModule'):
            self.load_modules[loadm.get('i')] = loadm.get('n')

        for filename in (self.file_table).iter('File'):
            self.src_files[filename.get('i')] = filename.get('n')

        for procedure in (self.procedure_table).iter('Procedure'):
            self.procedure_names[procedure.get('i')] = procedure.get('n')

        for metric in (self.metricdb_table).iter('MetricDB'):
            self.metric_names[metric.get('i')] = metric.get('n')

        return self.load_modules, self.src_files, self.procedure_names, self.metric_names

    def read_metricdb(self):
        metricdb_files = glob.glob(self.dir_name + '/*.metric-db')

        # assumes that glob returns a sorted order
        for pe, filename in enumerate(metricdb_files):
            metricdb = open(filename, "rb")
            metricdb.seek(32)
            arr1d = np.fromfile(metricdb, dtype=np.dtype('>f8'),
                              count=self.num_nodes * self.num_metrics)

            arr2d = arr1d.reshape(self.num_nodes, self.num_metrics)

            for i in range(0, self.num_metrics):
                for j in range(0, self.num_nodes):
                    self.metrics[i][j][pe] = arr2d[j][i]
            metricdb.close()

        # Also calculate avg metric per pe for each node
        self.metrics_avg = np.mean(self.metrics, axis=2)

        return self.metrics

    def create_cctree(self):
        self.fill_tables()
        self.read_metricdb()

        # parse the ElementTree to generate a calling context tree
        root = self.callpath_profile.findall('PF')[0]
        nid = int(root.get('i'))

        node_callpath = []
        node_callpath.append(self.procedure_names[root.get('n')])
        node_dict = {'name': self.procedure_names[root.get('n')], 'type': 'PF', 'file': self.src_files[root.get('f')], 'line': root.get('l'), 'module': self.load_modules[root.get('lm')]}
        for i in range(0, self.num_metrics):
            node_dict[self.metric_names[str(i)]] = self.metrics_avg[i][nid-1]

        cct_root = CCNode(tuple(node_callpath), None)
        list_index = []
        list_dict = []
        list_index.append(cct_root.callpath)
        list_dict.append(node_dict)

        # start tree construction at the root
        self.parse_xml_children(root, cct_root, list(node_callpath), list_index, list_dict)
        treeframe = pd.DataFrame(data=list_dict, index=list_index)
        return cct_root, treeframe

    def parse_xml_children(self, xml_node, ccnode, parent_callpath, list_index, list_dict):
        """ Parses all children of an XML node.
        """
        for xml_child in xml_node.getchildren():
            if xml_child.tag != 'M':
                self.parse_xml_node(xml_child, ccnode, parent_callpath, list_index, list_dict)

    def parse_xml_node(self, xml_node, cc_parent, parent_callpath, list_index, list_dict):
        """ Parses an XML node and its children recursively.
        """
        nid = int(xml_node.get('i'))

        global src_file
        xml_tag = xml_node.tag

        if xml_tag == 'PF' or xml_tag == 'Pr':
            name = self.procedure_names[xml_node.get('n')]
            src_file = xml_node.get('f')

            node_callpath = parent_callpath
            node_callpath.append(self.procedure_names[xml_node.get('n')])
            node_dict = {'name': name, 'type': xml_tag, 'file': self.src_files[src_file], 'line': xml_node.get('l'), 'module': self.load_modules[xml_node.get('lm')]}
            for i in range(0, self.num_metrics):
                node_dict[self.metric_names[str(i)]] = self.metrics_avg[i][nid-1]

            ccnode = CCNode(tuple(node_callpath), cc_parent)
        elif xml_tag == 'L':
            src_file = xml_node.get('f')
            line = xml_node.get('l')
            name = 'Loop@' + (self.src_files[src_file]).rpartition('/')[2] + ':' + line

            node_callpath = parent_callpath
            node_callpath.append(name)
            node_dict = {'name': name, 'type': xml_tag, 'file': self.src_files[src_file], 'line': line, 'module': None}
            for i in range(0, self.num_metrics):
                node_dict[self.metric_names[str(i)]] = self.metrics_avg[i][nid-1]

            ccnode = CCNode(tuple(node_callpath), cc_parent)
        elif xml_tag == 'S':
            line = xml_node.get('l')
            name = 'Stmt@' + (self.src_files[src_file]).rpartition('/')[2] + ':' + line

            node_callpath = parent_callpath
            node_callpath.append(name)
            node_dict = {'name': name, 'type': xml_tag, 'file': self.src_files[src_file], 'line': line, 'module': None}
            for i in range(0, self.num_metrics):
                node_dict[self.metric_names[str(i)]] = self.metrics_avg[i][nid-1]

            ccnode = CCNode(tuple(node_callpath), cc_parent)

        if xml_tag == 'C' or (xml_tag == 'Pr' and
                              self.procedure_names[xml_node.get('n')] == ''):
            # do not add a node to the tree
            self.parse_xml_children(xml_node, cc_parent, parent_callpath, list_index, list_dict)
        else:
            list_index.append(ccnode.callpath)
            list_dict.append(node_dict)
            cc_parent.add_child(ccnode)
            self.parse_xml_children(xml_node, ccnode, list(node_callpath), list_index, list_dict)
