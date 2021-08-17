.. Copyright 2021 University of Maryland and other Hatchet Project Developers.
   See the top-level LICENSE file for details.

   SPDX-License-Identifier: MIT

***************
Developer Guide
***************

Contributing to hatchet
=======================

If you want to contribute a new data reader, feature, or bugfix to hatchet,
please read below. This guide discusses the contributing workflow used in the
hatchet project, and the granularity of pull requests (PRs).

Branches
--------
The main branch in hatchet that has the latest contributions is named
``develop``. All pull requests should start from ``develop`` and target
``develop``.

There is a branch for each minor release series. Release branches originate
from ``develop`` and have tags for each revision release in the series.

Continuous Integration
----------------------

Hatchet uses `Travis CI <https://travis-ci.com>`_ for Continuous Integration
testing. This means that every time you submit a pull request, a series of
tests are run to make sure you didn’t accidentally introduce any bugs into
hatchet. Your PR will not be accepted until it passes all of these tests.

Unit tests
^^^^^^^^^^

Unit tests ensure that Hatchet's core API is working as expected. If you add a new data reader or new functionality to the hatchet API, you should add unit tests that provide adequate coverage for your code. You should also check that your changes pass all unit tests. You can do this by typing:

.. code-block:: console

  $ pytest

Style tests
^^^^^^^^^^^

Hatchet uses `Flake8 <https://flake8.pycqa.org/en/latest>`_ to test for `PEP 8 <https://www.python.org/dev/peps/pep-0008>` compliance. You can check for compliance using:

.. code-block:: console

  $ flake8

Contributing Workflow
---------------------

Hatchet is being actively developed, so the ``develop`` branch in hatchet has
new pull requests being merged often. The recommended way to contribute a pull
request is to fork the hatchet repo in your own space (if you already have a
fork, make sure is it up-to-date), and then create a new branch off of
``develop``.

We prefer that commits pertaining to different components of hatchet (specific
readers, the core graphframe API, query language, vis tools etc.) prefix the
component name in the commit message (for example ``<component>: descriptive
message``.

GitHub provides a detailed `tutorial
<https://docs.github.com/en/github/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests>`_
on creating pull requests.
