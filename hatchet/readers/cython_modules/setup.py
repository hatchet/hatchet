from setuptools import setup
from Cython.Build import cythonize
from Cython.Compiler import Options

setup(ext_modules=cythonize("subtract_metrics.pyx", annotate=True))
