#!/bin/bash
if grep -q "$PWD" <<< "$PTYHONPATH"; then
	export PYTHONPATH
else 
	export PYTHONPATH=$PWD:$PYTHONPATH
fi
python setup.py build_ext --inplace 
