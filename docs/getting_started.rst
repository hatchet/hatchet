.. Copyright 2017-2019 Lawrence Livermore National Security, LLC and other
   Hatchet Project Developers. See the top-level LICENSE file for details.

   SPDX-License-Identifier: MIT

Getting Started
===============

Prerequisites
-------------

Hatchet has the following minimum requirements, which must be installed before Hatchet is run:

#. Python 2 (2.7) or 3 (3.5 - 3.8)
#. matplotlib
#. pydot
#. numpy, and
#. pandas

Hatchet is available on `GitHub <https://github.com/LLNL/hatchet>`_.

Installation
------------

You can get hatchet from the `github repository
<https://github.com/LLNL/hatchet>`_ using this command:

.. code-block:: console

  $ git clone https://github.com/LLNL/hatchet.git

This will create a directory called ``hatchet``.

Add Hatchet to your PYTHONPATH
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Assuming that the full path to your cloned hatchet directory is in the ``HATCHET_ROOT`` environment variable, you can add ``$HATCHET_ROOT`` to your ``PYTHONPATH`` and you are ready to start using hatchet:

.. code-block:: console

    $ export PYTHONPATH=$HATCHET_ROOT:$PYTHONPATH

Alternatively, you can install hatchet using pip:

.. code-block:: console

  $ pip install hatchet

Check Installation
^^^^^^^^^^^^^^^^^^

After installing hatchet, you should be able to import hatchet when running the Python interpreter in interactive mode:

.. code-block:: console

  Python 3.7.4 (default, Jul 11 2019, 01:08:00)
  [Clang 10.0.1 (clang-1001.0.46.4)] on darwin
  Type "help", "copyright", "credits" or "license" for more information.
  >>>

Typing ``import hatchet`` at the prompt should succeed without any error
messages:

.. code-block:: console

  >>> import hatchet
  >>>

