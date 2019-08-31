# Copyright 2017-2019 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from hatchet.external import printtree as pt


def test_ansi_color_for_time():
    c = pt.colors_enabled
    pt.ansi_color_for_time(0.95, 1) == c.light_red + c.faint
    pt.ansi_color_for_time(0.8, 1) == c.red
    pt.ansi_color_for_time(0.5, 1) == c.yellow
    pt.ansi_color_for_time(0.15, 1) == c.green
    pt.ansi_color_for_time(0.05, 1) == c.green + c.faint
