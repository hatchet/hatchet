# Copyright 2017-2020 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

import re
import json

import pandas as pd

from hatchet.graphframe import GraphFrame
from ..node import Node
from ..graph import Graph
from ..frame import Frame
from ..util.timer import Timer
from ..util.config import dot_keywords


class TimemoryReader:
    '''Read in timemory JSON output'''

    def __init__(self, input):
        if isinstance(input, str) and input.endswith('json'):
            with open(input) as f:
                self.graph_dict = json.load(f)
        elif not isinstance(input, str):
            self.graph_dict = json.loads(input.read())
        else:
            self.graph_dict = input
        self.name_to_hnode = {}
        self.name_to_dict = {}
        self.timer = Timer()
        self.metric_cols = []
        self.properties = {}

    def create_graph(self):
        '''Create graph frame
        '''

        list_roots = []
        node_dicts = []
        graph_dict = self.graph_dict

        def remove_keys(_dict, _keys):
            '''Remove keys from dictionary
            '''
            if isinstance(_keys, str):
                if _keys in _dict:
                    del _dict[_keys]
            else:
                for _key in _keys:
                    _dict = remove_keys(_dict, _key)
            return _dict

        def patch_keys(_dict, _extra):
            '''Add a suffix to dictionary keys
            '''
            _tmp = {}
            for key, itr in _dict.items():
                _tmp['{}{}'.format(key, _extra)] = itr
            return _tmp

        def add_metrics(_dict):
            '''Add any keys to metric_cols which don't already
            exist
            '''
            for key, itr in _dict.items():
                if key not in self.metric_cols:
                    self.metric_cols.append(key)

        def get_keys(_prop, _prefix):
            '''Get the standard set of dictionary entries.
            Also, parses the prefix for func-file-line info
            which is typically in the form <FUNC>@<FILE>:<LINE>/...
            '''
            _name = _prop['properties']['id']
            _keys = {'name': _prefix,
                     'metric': _name,
                     'function': 'null',
                     'file': 'null',
                     'line': 'null'}
            _pre = _prefix.split('/')
            if len(_pre) > 0:
                _func = _pre[:1][0]
                _tail = _pre[1:]
                _func = _func.split('@')
                if len(_func) == 2:
                    _func = [_func[0]] + _func[1].split(':')
                _keys['name'] = '/'.join([_func[0]] + _tail)
                _keys['function'] = _func[0]
                if len(_func) == 3:
                    _keys['file'] = _func[1]
                    _keys['line'] = _func[2]
            return _keys

        def get_md_suffix(_obj):
            '''Gets a multi-dimensional suffix
            '''
            _ret = []
            if isinstance(_obj, str):
                _ret = [_obj]
            elif isinstance(_obj, dict):
                for _key, _item in _obj.items():
                    _ret.append(_key.strip().replace(
                        ' ', '-').replace('_', '-'))
            elif isinstance(_obj, list) or isinstance(_obj, tuple):
                for _item in _obj:
                    _ret.append(_item.strip().replace(
                        ' ', '-').replace('_', '-'))
            return _ret

        def get_md_entries(_obj, _suffix):
            '''Gets a multi-dimensional entries
            '''
            _ret = {}
            for _key, _item in _obj.items():
                for i, (k, v) in enumerate(_item.items()):
                    _ret['{}.{}'.format(_key, _suffix[i])] = v
            return _ret

        def parse_node(_key, _dict, _hparent, _rank):
            '''Create node_dict for one node and then call the function
            recursively on all children.
            '''

            # If the hash is zero, that indicates that the node
            # is a dummy for the root or is used for sychronizing data
            # between multiple threads
            if _dict['inclusive']['hash'] == 0:
                if 'children' in _dict:
                    for _child in _dict['children']:
                        parse_node(_key, _child, _hparent, _rank)
                return

            _prop = self.properties[_key]
            _keys = get_keys(_prop, _dict['inclusive']['prefix'])
            _keys['count'] = _dict['inclusive']['stats']['count']
            if _rank is not None:
                _keys['rank'] = _rank
            _keys['tid'] = _dict['inclusive']['tid']
            _labels = None if not 'type' in _prop else _prop['type']
            # if the data is multi-dimensional
            _md = True if not isinstance(_labels, str) else False

            _hnode = Node(Frame(_keys), _hparent)

            _remove = ['cereal_class_version', 'count']
            _inc_stats = remove_keys(_dict['inclusive']['stats'], _remove)
            _exc_stats = remove_keys(_dict['exclusive']['stats'], _remove)

            if _md:
                _suffix = get_md_suffix(_labels)
                _exc_stats = get_md_entries(_exc_stats, _suffix)
                _inc_stats = get_md_entries(_inc_stats, _suffix)

            _inc_stats = patch_keys(_inc_stats, '.inc')
            _exc_stats = patch_keys(_exc_stats, '')

            add_metrics(_exc_stats)
            add_metrics(_inc_stats)

            node_dicts.append(
                dict({'node': _hnode, **_keys}, **_exc_stats, **_inc_stats)
            )

            if _hparent is None:
                list_roots.append(_hnode)
            else:
                _hparent.add_child(_hnode)

            if 'children' in _dict:
                for _child in _dict['children']:
                    parse_node(_key, _child, _hnode, _rank)

        def eval_graph(_key, _dict, _rank):
            '''Evaluate the entry and determine if it has relevant data.
            If the hash is zero, that indicates that the node
            is a dummy for the root or is used for sychronizing data
            between multiple threads
            '''
            _stats = _dict['inclusive']['stats']
            _nchild = len(_dict['children'])
            if _nchild == 0:
                print('Skipping {}...'.format(_key))
                return
            if _rank is not None:
                print('Adding {} for rank {}...'.format(_key, _rank))
            else:
                print('Adding {}...'.format(_key))

            if _dict['inclusive']['hash'] > 0:
                parse_node(_key, _dict, None, _rank)
            elif 'children' in _dict:
                # call for all children
                for child in _dict['children']:
                    parse_node(_key, child, None, _rank)

        def read_graph(_key, _itr, _offset):
            '''The layout of the graph at this stage
            is subject slightly different structures
            based on whether distributed memory parallelism (DMP)
            (e.g. MPI, UPC++) was supported and active
            '''
            _n = len(_itr)
            for i in range(len(_itr)):
                _dict = _itr[i]
                _idx = None if _offset is None else i + _offset
                if isinstance(_dict, list):
                    for j in range(len(_dict)):
                        eval_graph(_key, _dict[j], _idx)
                else:
                    eval_graph(_key, _dict, _idx)

        def read_properties(_dict, _key, _itr):
            '''Read in the properties for a component. This
            contains information on the type of the component,
            a description, a unit_value relative to the
            standard, a unit label, whether the data is
            only relevant per-thread, the number of MPI and/or
            UPC++ ranks (some results can theoretically use
            both UPC++ and MPI), the number of threads in
            the application, and the total number of processes
            '''
            if not _key in _dict:
                _dict[_key] = {}
            try:
                _dict[_key]['properties'] = remove_keys(
                    itr['properties'], 'cereal_class_version')
            except:
                pass
            for k in ('type', 'description', 'unit_value',
                      'unit_repr', 'thread_scope_only',
                      'mpi_size', 'upcxx_size',
                      'thread_count', 'process_count'):
                if not k in _dict[_key] or _dict[_key][k] is None:
                    if k in itr:
                        _dict[_key][k] = itr[k]
                    else:
                        _dict[_key][k] = None

        for key, itr in graph_dict['timemory'].items():
            # strip out the namespace if provided
            key = key.replace('tim::', '').replace('component::', '').lower()
            # read in properties
            read_properties(self.properties, key, itr)
            # if no DMP supported
            if 'graph' in itr:
                print('Reading graph...')
                read_graph(key, itr['graph'], None)
            else:
                # read in MPI results
                if 'mpi' in itr:
                    print('Reading MPI...')
                    read_graph(key, itr['mpi'], 0)
                # if MPI and UPC++, report ranks
                # offset by MPI_Comm_size
                _offset = self.properties[key]['mpi_size']
                _offset = 0 if _offset is None else int(_offset)
                if 'upc' in itr:
                    print('Reading UPC...')
                    read_graph(key, itr['upc'], _offset)
                elif 'upcxx' in itr:
                    print('Reading UPC++...')
                    read_graph(key, itr['upcxx'], _offset)

        # find any columns where the entries are None or 'null'
        non_null = {}
        for itr in node_dicts:
            for key, item in itr.items():
                if key not in non_null:
                    non_null[key] = False
                if item is not None:
                    if not isinstance(item, str):
                        non_null[key] = True
                    elif isinstance(item, str) and item != 'null':
                        non_null[key] = True

        # find any columns where the entries are all 'null'
        for itr in node_dicts:
            for key, item in non_null.items():
                if not item:
                    del itr[key]

        # create the graph of the roots
        graph = Graph(list_roots)
        graph.enumerate_traverse()

        # separate out the inclusive vs. exclusive columns
        exc_metrics = []
        inc_metrics = []
        for column in self.metric_cols:
            if column.endswith('.inc'):
                inc_metrics.append(column)
            else:
                exc_metrics.append(column)

        dataframe = pd.DataFrame(data=node_dicts)
        dataframe.set_index(['node'], inplace=True)
        dataframe.sort_index(inplace=True)

        return GraphFrame(graph, dataframe, exc_metrics, inc_metrics)

    def read(self):
        '''Read timemory json.
        '''
        return self.create_graph()
