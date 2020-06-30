#!/bin/sh

while inotifywait -e modify $1; do
	python3 setup.py build_ext --inplace;
	cp *.so ..;
done
