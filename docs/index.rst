.. Copyright 2017-2019 Lawrence Livermore National Security, LLC and other
   Hatchet Project Developers. See the top-level LICENSE file for details.

   SPDX-License-Identifier: MIT

.. hatchet documentation master file, created by
   sphinx-quickstart on Tue Jun 26 08:43:21 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Hatchet Documentation
=====================

Hatchet is a Python-based library to analyze performance data that has a
hierarchy (derived from calling context trees, call graphs, callpath traces,
nested regions' timers, etc.). Hatchet implements various operations to analyze
a single hierarchical data set or compare multiple data sets.


Getting Started
---------------

To get started installing and using Hatchet, see the :doc:`Install Guide
<install>` and :doc:`User Guide <userguide>`.


Hatchet Project Resources
-------------------------

**Online Documentation**

http://hatchet.readthedocs.io

**Github Source Code**

http://github.com/llnl/hatchet

**Issue Tracker**

http://github.com/llnl/hatchet/issues


Citing Hatchet
--------------

If you are referencing Hatchet in a publication, please cite the
following `paper <http://www.cs.umd.edu/~bhatele/pubs/pdf/2019/sc2019.pdf>`_:

 * Abhinav Bhatele, Stephanie Brink, and Todd Gamblin. Hatchet: Pruning
   the Overgrowth in Parallel Profiles.  In *Supercomputing 2019
   (SC'19)*, Denver, Colorado, November 17-22 2019. LLNL-CONF-772402.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   install
   userguide
   source/hatchet


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
