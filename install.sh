#!/bin/sh

if [ "$PYTHONPATH" != *"$PWD"* ]; then
	PYTHONPATH=$PWD:$PYTHONPATH
fi

python setup.py build_ext --inplace
