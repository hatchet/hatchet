import numpy as np
import cython

cdef long[:] np_nids_memview
cdef long num_nids
cdef int num_stmt_nodes = 0
cdef long[:] p_nodes
cdef long[:] c_nodes


def set_np_nids_memview(long[:] np_nids, long np_nids_size):
  global np_nids_memview
  global num_nids
  global p_nodes
  global c_nodes
  np_nids_memview = np_nids
  num_nids = np_nids_size

# @cython.boundscheck(False)
def subtract_exclusive_metric_vals(long nid, long parent_nid, double[:] metrics, long num_stmt_nodes, long stride):
  global num_stmt_nodes
  global np_nids_memview
  global num_nids
  global p_nodes
  global c_nodes
  cdef long ref_nid = nid
  cdef long ref_pnid = parent_nid

  # compiler directive
  with cython.boundscheck(False):
  # we are modifying metrics in place here
  # since they are passed by refrence via their
  # memory
    for i in range(num_stmt_nodes):
      metrics[ref_pnid-1] -= metrics[ref_nid-1]

      ref_nid += stride
      ref_pnid += stride
