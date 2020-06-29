from setuptools import setup
from Cython.Build import cythonize

setup(ext_modules=cythonize("subtract_metrics.pyx", annotate=True))
