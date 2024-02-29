# Copyright 2024 University of Maryland and other Hatchet Project Developers.
# See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: MIT

# The name of the Pygments (syntax highlighting) style to use.
from pygments.styles.default import DefaultStyle
from pygments.token import Generic


# modifications to the default style
class HatchetStyle(DefaultStyle):
    styles = DefaultStyle.styles.copy()
    background_color = "#f4f4f8"
    styles[Generic.Output] = "#355"
    styles[Generic.Prompt] = "bold #346ec9"
