# -*- coding: utf-8 -*-

# Copyright (c) 2014-2018, Joe Rickerby and contributors
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from ..version import __version__

import pandas as pd
import numpy as np
import warnings


class ConsoleRenderer:
    def __init__(self, unicode=False, color=False):
        self.unicode = unicode
        self.color = color
        self.colors = self.colors_enabled if color else self.colors_disabled
        self.visited = []

    def render(self, roots, dataframe, **kwargs):
        result = self.render_preamble()

        if roots is None:
            result += "The graph is empty.\n\n"
            return result

        self.metric_columns = kwargs["metric_column"]
        self.precision = kwargs["precision"]
        self.name = kwargs["name_column"]
        self.expand = kwargs["expand_name"]
        self.context = kwargs["context_column"]
        self.rank = kwargs["rank"]
        self.thread = kwargs["thread"]
        self.depth = kwargs["depth"]
        self.highlight = kwargs["highlight_name"]
        self.invert_colormap = kwargs["invert_colormap"]
        # know what the user input for the colormap
        self.color_map = kwargs["color_map"]

        if self.color:
            # assigning the colormap based on user input
            self.assign_mapcolor()

        if isinstance(self.metric_columns, str):
            self.primary_metric = self.metric_columns
            self.second_metric = None
        elif isinstance(self.metric_columns, list):
            if len(self.metric_columns) > 2:
                warnings.warn(
                    "More than 2 metrics specified in metric_column=. Tree() will only show 2 metrics at a time. The remaining metrics will not be shown.",
                    SyntaxWarning,
                )
                self.primary_metric = self.metric_columns[0]
                self.second_metric = self.metric_columns[1]
            elif len(self.metric_columns) == 2:
                self.primary_metric = self.metric_columns[0]
                self.second_metric = self.metric_columns[1]
            elif len(self.metric_columns) == 1:
                self.primary_metric = self.metric_columns[0]
                self.second_metric = None

        if self.primary_metric not in dataframe.columns:
            raise KeyError(
                "metric_column={} does not exist in the dataframe, please select a valid column. See a list of the available metrics with GraphFrame.show_metric_columns().".format(
                    self.primary_metric
                )
            )
        if (
            self.second_metric is not None
            and self.second_metric not in dataframe.columns
        ):
            raise KeyError(
                "metric_column={} does not exist in the dataframe, please select a valid column. See a list of the available metrics with GraphFrame.show_metric_columns().".format(
                    self.second_metric
                )
            )

        if self.invert_colormap:
            self.colors.colormap.reverse()

        # grab the min and max value for the primary metric, ignoring inf and
        # nan values
        if "rank" in dataframe.index.names:
            metric_series = (dataframe.xs(self.rank, level=1))[self.primary_metric]
        else:
            metric_series = dataframe[self.primary_metric]
        isfinite_mask = np.isfinite(metric_series.values)
        filtered_series = pd.Series(
            metric_series.values[isfinite_mask], metric_series.index[isfinite_mask]
        )

        self.max_metric = filtered_series.max()
        self.min_metric = filtered_series.min()

        if self.unicode:
            self.lr_arrows = {"◀": u"◀ ", "▶": u"▶ "}
        else:
            self.lr_arrows = {"◀": u"< ", "▶": u"> "}

        for root in sorted(roots, key=lambda n: n.frame):
            result += self.render_frame(root, dataframe)

        if self.color is True:
            result += self.render_legend()

        if self.invert_colormap:
            self.colors.colormap.reverse()

        if self.unicode:
            return result
        else:
            return result.encode("utf-8")

    # pylint: disable=W1401
    def render_preamble(self):
        lines = [
            r"    __          __       __         __ ",
            r"   / /_  ____ _/ /______/ /_  ___  / /_",
            r"  / __ \/ __ `/ __/ ___/ __ \/ _ \/ __/",
            r" / / / / /_/ / /_/ /__/ / / /  __/ /_  ",
            r"/_/ /_/\__,_/\__/\___/_/ /_/\___/\__/  {:>2}".format("v" + __version__),
            r"",
            r"",
        ]

        return "\n".join(lines)

    # This function is used for assigning different color schemes for colormaps if
    # the user decided to choose a color scheme other than the default colormap.
    def assign_mapcolor(self):
        # Here we are changing the color schemes of the
        # the map based on the user input

        # This is the default colormap (RdYlGn)
        # if the user doesn't enter any specific colormap option
        # then the color is by default RdYlGn
        if self.color_map == ("RdYlGn"):
            self.colors.colormap = self.colors.colormap_RdYlGn
        elif self.color_map == ("BrBG"):
            self.colors.colormap = self.colors.colormap_BrBG
        elif self.color_map == ("PiYG"):
            self.colors.colormap = self.colors.colormap_PiYG
        elif self.color_map == ("PRGn"):
            self.colors.colormap = self.colors.colormap_PRGn
        elif self.color_map == ("PiYG"):
            self.colors.colormap = self.colors.colormap_PiYG
        elif self.color_map == ("PuOr"):
            self.colors.colormap = self.colors.colormap_PuOr
        elif self.color_map == ("RdBu"):
            self.colors.colormap = self.colors.colormap_RdBu
        elif self.color_map == ("RdGy"):
            self.colors.colormap = self.colors.colormap_RdGy
        elif self.color_map == ("RdYlBu"):
            self.colors.colormap = self.colors.colormap_RdYlBu
        elif self.color_map == ("Spectral"):
            self.colors.colormap = self.colors.colormap_Spectral
        else:
            raise ValueError(
                "Incorrect Colormap. Select any one out of BrBG, PiYg, PRGn,"
                + " PuOr, RdBu, RdGy, RdYlBu, RdYlGn and Spectral."
            )

    def render_legend(self):
        def render_label(index, low, high):
            metric_range = self.max_metric - self.min_metric

            return (
                self.colors.colormap[index]
                + u"█ "
                + self.colors.end
                + "{:.2f}".format(low * metric_range + self.min_metric)
                + " - "
                + "{:.2f}".format(high * metric_range + self.min_metric)
                + "\n"
            )

        legend = (
            "\n"
            + "\033[4m"
            + "Legend"
            + self.colors.end
            + " (Metric: "
            + self.primary_metric
            + " Min: {:.2f}".format(self.min_metric)
            + " Max: {:.2f}".format(self.max_metric)
            + ")\n"
        )

        legend += render_label(0, 0.9, 1.0)
        legend += render_label(1, 0.7, 0.9)
        legend += render_label(2, 0.5, 0.7)
        legend += render_label(3, 0.3, 0.5)
        legend += render_label(4, 0.1, 0.3)
        legend += render_label(5, 0.0, 0.1)

        legend += "\n" + self._ansi_color_for_name("name") + "name" + self.colors.end
        legend += " User code    "

        legend += self.colors.left + self.lr_arrows["◀"] + self.colors.end
        legend += " Only in left graph    "
        legend += self.colors.right + self.lr_arrows["▶"] + self.colors.end
        legend += " Only in right graph\n"

        return legend

    def render_frame(self, node, dataframe, indent=u"", child_indent=u""):
        node_depth = node._depth
        if node_depth < self.depth:
            # set dataframe index based on whether rank and thread are part of
            # the MultiIndex
            if "rank" in dataframe.index.names and "thread" in dataframe.index.names:
                df_index = (node, self.rank, self.thread)
            elif "rank" in dataframe.index.names:
                df_index = (node, self.rank)
            elif "thread" in dataframe.index.names:
                df_index = (node, self.thread)
            else:
                df_index = node

            node_metric = dataframe.loc[df_index, self.primary_metric]

            metric_precision = "{:." + str(self.precision) + "f}"
            metric_str = (
                self._ansi_color_for_metric(node_metric)
                + metric_precision.format(node_metric)
                + self.colors.end
            )

            if self.second_metric is not None:
                metric_str += u" {c.faint}{second_metric:.{precision}f}{c.end}".format(
                    second_metric=dataframe.loc[df_index, self.second_metric],
                    precision=self.precision,
                    c=self.colors,
                )

            node_name = dataframe.loc[df_index, self.name]
            if self.expand is False:
                if len(node_name) > 39:
                    node_name = (
                        node_name[:18] + "..." + node_name[(len(node_name) - 18) :]
                    )
            name_str = (
                self._ansi_color_for_name(node_name) + node_name + self.colors.end
            )

            # 0 is "", 1 is "L", and 2 is "R"
            if "_missing_node" in dataframe.columns:
                left_or_right = dataframe.loc[df_index, "_missing_node"]
                if left_or_right == 0:
                    lr_decorator = u""
                elif left_or_right == 1:
                    lr_decorator = u" {c.left}{decorator}{c.end}".format(
                        decorator=self.lr_arrows["◀"], c=self.colors
                    )
                elif left_or_right == 2:
                    lr_decorator = u" {c.right}{decorator}{c.end}".format(
                        decorator=self.lr_arrows["▶"], c=self.colors
                    )

            result = u"{indent}{metric_str} {name_str}".format(
                indent=indent, metric_str=metric_str, name_str=name_str
            )
            if "_missing_node" in dataframe.columns:
                result += lr_decorator
            if self.context in dataframe.columns:
                result += u" {c.faint}{context}{c.end}\n".format(
                    context=dataframe.loc[df_index, self.context], c=self.colors
                )
            else:
                result += u"\n"

            if self.unicode:
                indents = {"├": u"├─ ", "│": u"│  ", "└": u"└─ ", " ": u"   "}
            else:
                indents = {"├": u"|- ", "│": u"|  ", "└": u"`- ", " ": u"   "}

            # ensures that we never revisit nodes in the case of
            # large complex graphs
            if node not in self.visited:
                self.visited.append(node)
                sorted_children = sorted(node.children, key=lambda n: n.frame)
                if sorted_children:
                    last_child = sorted_children[-1]

                for child in sorted_children:
                    if child is not last_child:
                        c_indent = child_indent + indents["├"]
                        cc_indent = child_indent + indents["│"]
                    else:
                        c_indent = child_indent + indents["└"]
                        cc_indent = child_indent + indents[" "]
                    result += self.render_frame(
                        child, dataframe, indent=c_indent, child_indent=cc_indent
                    )
        else:
            result = ""
            indents = {"├": u"", "│": u"", "└": u"", " ": u""}

        return result

    def _ansi_color_for_metric(self, metric):
        metric_range = self.max_metric - self.min_metric

        if metric_range != 0:
            proportion_of_total = (metric - self.min_metric) / metric_range
        else:
            proportion_of_total = metric / 1

        if proportion_of_total > 0.9:
            return self.colors.colormap[0]
        elif proportion_of_total > 0.7:
            return self.colors.colormap[1]
        elif proportion_of_total > 0.5:
            return self.colors.colormap[2]
        elif proportion_of_total > 0.3:
            return self.colors.colormap[3]
        elif proportion_of_total > 0.1:
            return self.colors.colormap[4]
        elif proportion_of_total >= 0:
            return self.colors.colormap[5]
        else:
            return self.colors.blue

    def _ansi_color_for_name(self, node_name):
        if self.highlight is False:
            return ""

        if "<unknown procedure>" in node_name or "<unknown file>" in node_name:
            return ""
        else:
            return self.colors.bg_white_255 + self.colors.dark_gray_255

    class colors_enabled:
        colormap = []

        # RdYlGn (Default) color map
        colormap_RdYlGn = [
            "\033[38;5;196m",  # red
            "\033[38;5;208m",  # orange
            "\033[38;5;220m",  # yellow-ish
            "\033[38;5;46m",  # neon green
            "\033[38;5;34m",  # light green
            "\033[38;5;22m",  # dark green
        ]

        # BrBG color map
        colormap_BrBG = [
            "\033[38;5;94m",  # Brown
            "\033[38;5;179m",  # Light Brown
            "\033[38;5;222m",  # Cream
            "\033[38;5;116m",  # Light Turqouise
            "\033[38;5;37m",  # Blue-Green 73
            "\033[38;5;23m",  # Dark Blue-Green
        ]

        #  PiYG color map
        colormap_PiYG = [
            "\033[38;5;162m",  # Dark Pink
            "\033[38;5;176m",  # Light-ish Pink
            "\033[38;5;219m",  # Pale Pink
            "\033[38;5;149m",  # Pale Green
            "\033[38;5;70m",  # Light Forest Green
            "\033[38;5;22m",  # Dark Green
        ]

        # PRGn color map
        colormap_PRGn = [
            "\033[38;5;90m",  # Dark Purple
            "\033[38;5;140m",  # Purple
            "\033[38;5;183m",  # Light Purple
            "\033[38;5;151m",  # Pale Green
            "\033[38;5;70m",  # Forest Green
            "\033[38;5;22m",  # Dark Green
        ]

        # PuOr color map
        colormap_PuOr = [
            "\033[38;5;130m",  # Brown
            "\033[38;5;208m",  # Orange
            "\033[38;5;220m",  # Pale Orange
            "\033[38;5;189m",  # Pale Purple
            "\033[38;5;104m",  # Light-ish Purple
            "\033[38;5;57m",  # Dark Purple
        ]

        # RdBu color map
        colormap_RdBu = [
            "\033[38;5;124m",  # Maroon Red
            "\033[38;5;209m",  # Dark Orange
            "\033[38;5;224m",  # Pale Orange
            "\033[38;5;153m",  # Light Sky Blue
            "\033[38;5;75m",  # Light-ish Blue
            "\033[38;5;25m",  # Navy Blue
        ]

        # RdGy color map
        colormap_RdGy = [
            "\033[38;5;124m",  # Maroon Red
            "\033[38;5;209m",  # Dark Orange
            "\033[38;5;223m",  # Pale Orange
            "\033[38;5;251m",  # Pale Grey
            "\033[38;5;244m",  # Grey
            "\033[38;5;238m",  # Dark Grey
        ]

        # RdYlBu color map
        colormap_RdYlBu = [
            "\033[38;5;196m",  # Red
            "\033[38;5;208m",  # Orange
            "\033[38;5;220m",  # Yellow-ish
            "\033[38;5;153m",  # Light Cyan Blue
            "\033[38;5;68m",  # Seagull Blue
            "\033[38;5;24m",  # Dark Blue
        ]

        # Spectral color map
        colormap_Spectral = [
            "\033[38;5;196m",  # Red
            "\033[38;5;208m",  # Orange
            "\033[38;5;220m",  # Yellow-ish
            "\033[38;5;191m",  # Yellow-ish Green
            "\033[38;5;114m",  # Olive Green
            "\033[38;5;26m",  # Dark Blue
        ]

        blue = "\033[34m"
        cyan = "\033[36m"

        bg_white_255 = "\033[48;5;246m"
        dark_gray_255 = "\033[38;5;232m"

        left = "\033[38;5;160m"
        right = "\033[38;5;28m"

        faint = "\033[2m"
        end = "\033[0m"

    class colors_disabled:
        colormap = ["", "", "", "", "", "", ""]

        def __getattr__(self, key):
            return ""

    colors_disabled = colors_disabled()
