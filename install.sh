#!/bin/sh

case "$PYTHONPATH" in
    *"$PWD"*)
        ;;

    *)
        PYTHONPATH=$PWD:$PYTHONPATH
        ;;
esac

mypy=`which python`
rc=$?
if [ ${rc} -ne 0 ] ; then
    mypy=`which python3`
    rc=$?
    if [ ${rc} -ne 0 ] ; then
        echo "Python not found. Is it in your path?"
    fi
fi

${mypy} setup.py build_ext --inplace
