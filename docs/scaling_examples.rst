.. Copyright 2020 University of Maryland and other Hatchet Project
   Developers. See the top-level LICENSE file for details.

   SPDX-License-Identifier: MIT

Scaling Performance Examples
============================

Strong Scaling
--------------

.. literalinclude:: examples/hpctoolkit.py
    :language: python

Weak Scaling
------------

Hatchet can be used for comparing parallel scaling performance of applications.
In this example, we compare the performance of LULESH running on 1 and 27 cores.
By executing a simple ``divide`` of the two datasets in Hatchet, we can quickly
identify which function calls did or did not scale well. In the resulting
graph, we invert the color scheme, so that functions that did not scale well
(i.e., have a low speedup) are colored in red.

.. code-block:: python

  gf_1core = ht.GraphFrame.from_caliper('lulesh*-1core.json')
  gf_27cores = ht.GraphFrame.from_caliper('lulesh*-27cores.json')

  speedup = gf_1core / gf_27cores

|pic1| / |pic2|

= |pic3|

.. |pic1| image:: images/speedup-graph1.png
   :scale: 30 %

.. |pic2| image:: images/speedup-graph2.png
   :scale: 30 %

.. |pic3| image:: images/speedup-graph3.png
   :scale: 30 %
