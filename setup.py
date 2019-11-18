# Copyright 2017-2019 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="hatchet",
    version="1.0.0",
    description="A Python library for analyzing hierarchical performance data",
    url="https://github.com/LLNL/hatchet",
    author="Abhinav Bhatele",
    author_email="bhatele@cs.umd.edu",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
    ],
    keywords="",
    packages=[
        "hatchet",
        "hatchet.readers",
        "hatchet.util",
        "hatchet.external",
        "hatchet.tests",
    ],
    install_requires=["pydot"],
)
