.. Copyright 2020 University of Maryland and other Hatchet Project
   Developers. See the top-level LICENSE file for details.

   SPDX-License-Identifier: MIT

Basic Tutorial: Hatchet 101
===========================

This tutorial introduces how to use hatchet, including basics about:

* Using the pandas API
* Using the hatchet API
* Generating data for hatchet


Installing Hatchet and Tutorial Setup
-------------------------------------

You can install hatchet using pip:

.. code-block:: console

  $ pip install hatchet

After installing hatchet, you can import hatchet when running the Python
interpreter in interactive mode:

.. code-block:: console

  $ python
  Python 3.7.7 (default, Mar 14 2020, 02:39:01)
  [Clang 10.0.1 (clang-1001.0.46.4)] on darwin
  Type "help", "copyright", "credits" or "license" for more information.
  >>>

Typing ``import hatchet`` at the prompt should succeed without any error
messages:

.. code-block:: console

  >>> import hatchet
  >>>

You are good to go!

The Hatchet repository includes standalone Python-based Jupyter notebook examples based on this
tutorial.
You can find them in the hatchet `GitHub repository
<https://github.com/LLNL/hatchet/tree/develop/docs/examples>`_. You can get a local copy of the repository using ``git``:

.. code-block:: console

  $ git clone https://github.com/LLNL/hatchet.git

You will the tutorial notebooks in your local hatchet repository under
``examples/tutorial/``.

Introduction
------------

You can read in a dataset into Hatchet for analysis by using one of several
``from_`` static methods. You can read in a Caliper JSON file as follows:

.. code-block:: console

  >>> import hatchet
  >>> caliper_file = 'lulesh-annotation-profile-1core.json'
  >>> gf = ht.GraphFrame.from_caliper_json(caliper_file)
  >>>

At this point, your input file (profile) has been loaded into hatchet data
structures as a pandas data frame and a corresponding graph.

The pandas DataFrame component of Hatchet's GraphFrame contains the metrics and
other non-numeric data associated with each node in the dataset.  You can print
the dataframe by typing:

.. code-block:: console

  >>> print(gf.dataframe)

This should produce output like this:

.. figure:: images/basic-tutorial/01-dataframe.png
   :scale: 50 %
   :align: center

The Graph component of Hatchet’s GraphFrame stores the connections between
parents and children.  You can print the graph using hatchet's tree printing
functionality:
 
.. code-block:: console

  >>> print(gf.tree())

This will print a graphical version of the tree on the terminal:

.. figure:: images/basic-tutorial/02-tree.png
   :scale: 50 %
   :align: center


Analyzing the DataFrame using pandas
------------------------------------

The ``DataFrame`` is one of two components that makeup the ``GraphFrame`` in
hatchet. The pandas ``DataFrame`` stores the performance metrics and other non-numeric data for all nodes in the
graph.

You can apply any pandas operations to the dataframe in hatchet. Note that modifying the dataframe in hatchet outside of the hatchet API is not recommended because operations that modify the dataframe can make the dataframe and graph inconsistent.

sorting the rows

adding columns (load imbalance)


Analyzing the Graph via printing
--------------------------------

some common tree() arguments



Analyzing the GraphFrame
------------------------


dropping index levels

filter and squash

filtering through syntax query language

arithmetic operations on two graphframes
