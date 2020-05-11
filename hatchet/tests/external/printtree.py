# Copyright 2017-2020 Lawrence Livermore National Security, LLC and other
# Hatchet Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

from hatchet.external import printtree as pt


def test_ansi_color_for_time_default():
    c = pt.colors_enabled_default
    pt.ansi_color_for_time(0.95, 1, c) == c.highest + c.faint
    pt.ansi_color_for_time(0.8, 1, c) == c.high
    pt.ansi_color_for_time(0.5, 1, c) == c.med
    pt.ansi_color_for_time(0.15, 1, c) == c.low
    pt.ansi_color_for_time(0.05, 1, c) == c.lowest + c.faint


def test_ansi_color_for_time_invert():
    c = pt.colors_enabled_invert
    pt.ansi_color_for_time(0.95, 1, c) == c.highest + c.faint
    pt.ansi_color_for_time(0.8, 1, c) == c.high
    pt.ansi_color_for_time(0.5, 1, c) == c.med
    pt.ansi_color_for_time(0.15, 1, c) == c.low
    pt.ansi_color_for_time(0.05, 1, c) == c.lowest + c.faint
