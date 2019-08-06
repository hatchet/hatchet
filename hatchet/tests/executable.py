##############################################################################
# Copyright (c) 2017-2019, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# This file is part of Hatchet.
# Created by Abhinav Bhatele <bhatele@llnl.gov>.
# LLNL-CODE-741008. All rights reserved.
#
# For details, see: https://github.com/LLNL/hatchet
# Please also read the LICENSE file for the MIT License notice.
##############################################################################

import os

import six


def which(executable):
    """Return a path to the ``Executable``."""
    path = os.environ.get("PATH", "")

    if isinstance(path, six.string_types):
        path = path.split(os.pathsep)

    for directory in path:
        if os.path.isfile(directory) and os.access(directory, os.X_OK):
            return directory
        exe = os.path.join(directory, executable)
        if os.path.isfile(exe) and os.access(exe, os.X_OK):
            return exe

    return None
