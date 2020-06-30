import numpy as np

cdef long[:] np_nids_memview
cdef long num_nids
cdef int num_stmt_nodes = 0
cdef long[:] p_nodes
cdef long[:] c_nodes

def set_np_nids_memview(long[:] np_nids, long np_nids_size):
  global np_nids_memview
  global num_nids
  np_nids_memview = np_nids
  num_nids = np_nids_size

def subtract_exclusive_metric_vals(long nid, long parent_nid, double[:] metrics):
  global num_stmt_nodes
  global np_nids_memview
  global num_nids
  global p_nodes
  global c_nodes
  cdef int loaded_p_nodes = 0
  cdef int loaded_c_nodes = 0

  if num_stmt_nodes == 0:
    for i in range(num_nids):
      if np_nids_memview[i] == nid:
        num_stmt_nodes += 1
    p_nodes = np.zeros((num_stmt_nodes), dtype=np.int64)
    c_nodes = np.zeros((num_stmt_nodes), dtype=np.int64)

  try:
    for i in range(num_nids):
      if np_nids_memview[i] == nid:
        c_nodes[loaded_c_nodes] = i
        loaded_c_nodes += 1
      elif np_nids_memview[i] == parent_nid:
        p_nodes[loaded_p_nodes] = i
        loaded_p_nodes += 1
    for i in range(loaded_c_nodes):
      metrics[p_nodes[i]] -= metrics[c_nodes[i]]

# we ran into an out of bounds error and need to allocate
# new memory
  except:
    num_stmt_nodes = 0
    subtract_exclusive_metric_vals(nid, parent_nid, metrics)
