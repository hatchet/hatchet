from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='hatchet',
    version='0.0.2',
    description='A Python library for analyzing hierarchical performance data',
    url = 'https://github.com/LLNL/hatchet',
    author = 'Abhinav Bhatele',
    author_email = 'bhatele@llnl.gov',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
    ],
    keywords='',
    packages = ['hatchet', 'hatchet.external'],
)

