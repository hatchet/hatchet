# Copyright 2017-2020 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from setuptools import setup
from setuptools import Extension
from codecs import open
from os import path
from hatchet import __version__

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="hatchet",
    version=__version__,
    description="A Python library for analyzing hierarchical performance data",
    url="https://github.com/LLNL/hatchet",
    author="Abhinav Bhatele",
    author_email="bhatele@cs.umd.edu",
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
    ],
    keywords="",
    packages=[
        "hatchet",
        "hatchet.readers",
        "hatchet.util",
        "hatchet.external",
        "hatchet.tests",
        "hatchet.cython_modules.libs",
    ],
    install_requires=["pydot", "PyYAML", "matplotlib", "numpy", "pandas", "cython"],
    ext_modules=[
        Extension(
            "hatchet.cython_modules.libs.subtract_metrics",
            ["hatchet/cython_modules/subtract_metrics.c"],
        )
    ],
)
