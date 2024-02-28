# Copyright 2017-2024 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from setuptools import setup, Extension
from Cython.Build import build_ext as cy_build_ext
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# Get the version in a safe way which does not refrence hatchet `__init__` file
# per python docs: https://packaging.python.org/guides/single-sourcing-package-version/
version = {}
with open("./hatchet/version.py") as fp:
    exec(fp.read(), version)


setup(
    name="hatchet",
    version=version["__version__"],
    description="A Python library for analyzing hierarchical performance data",
    url="https://github.com/hatchet/hatchet",
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
    setup_requires=["cython", "setuptools"],
    install_requires=[
        "pydot",
        "pyyaml",
        "matplotlib",
        "numpy",
        "pandas",
        "textx",
        "multiprocess",
        "caliper-reader",
        "pycubexr; python_version >= '3.6'",
    ],
    # TODO: the setup could be cleaner if we didn't dump the generated
    # .so files into _libs
    ext_modules=[
        Extension(
            "hatchet.cython_modules.libs.reader_modules",
            ["hatchet/cython_modules/reader_modules.pyx"],
        ),
        Extension(
            "hatchet.cython_modules.libs.graphframe_modules",
            ["hatchet/cython_modules/graphframe_modules.pyx"],
        ),
    ],
    cmdclass={"build_ext": cy_build_ext},
)
