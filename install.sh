#!/bin/bash
if [[ "$PYTHONPATH" != *"$PWD"* ]]; then
	export PYTHONPATH=$PWD:$PYTHONPATH
fi
python setup.py build_ext --inplace 
