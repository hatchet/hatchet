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

import hatchet


class ConsoleRenderer:
    def __init__(self, unicode=False, color=False):
        self.unicode = unicode
        self.color = color
        self.colors = self.colors_enabled if color else self.colors_disabled

    def render(self, roots, dataframe, **kwargs):
        result = self.render_preamble()

        if roots is None:
            result += "The graph is empty.\n\n"
            return result

        self.metric = kwargs["metric_column"]
        self.precision = kwargs["precision"]
        self.name = kwargs["name_column"]
        self.expand = kwargs["expand_name"]
        self.context = kwargs["context_column"]
        self.rank = kwargs["rank"]
        self.thread = kwargs["thread"]
        self.depth = kwargs["depth"]
        self.invert_colormap = kwargs["invert_colormap"]

        if self.invert_colormap:
            self.colors.colormap.reverse()
        if "rank" in dataframe.index.names:
            self.max_metric = (dataframe.xs(self.rank, level=1))[self.metric].max()
        else:
            self.max_metric = dataframe[self.metric].max()

        for root in roots:
            result += self.render_frame(root, dataframe)

        if self.color is True:
            result += self.render_legend()

        return result

    # pylint: disable=W1401
    def render_preamble(self):
        lines = [
            r"    __          __       __         __ ",
            r"   / /_  ____ _/ /______/ /_  ___  / /_",
            r"  / __ \/ __ `/ __/ ___/ __ \/ _ \/ __/",
            r" / / / / /_/ / /_/ /__/ / / /  __/ /_  ",
            r"/_/ /_/\__,_/\__/\___/_/ /_/\___/\__/  {:>2}".format(
                "v" + hatchet.__version__
            ),
            r"",
            r"",
        ]

        return "\n".join(lines)

    def render_legend(self):
        def render_label(index, low, high):
            return (
                self.colors.colormap[index]
                + u"█ "
                + self.colors.end
                + "{:.2f}".format(low * self.max_metric)
                + " - "
                + "{:.2f}".format(high * self.max_metric)
                + "\n"
            )

        legend = "\n" + "\033[4m" + "Legend" + self.colors.end + "\n"
        legend += render_label(0, 0.9, 1.0)
        legend += render_label(1, 0.7, 0.9)
        legend += render_label(2, 0.5, 0.7)
        legend += render_label(3, 0.3, 0.5)
        legend += render_label(4, 0.1, 0.3)
        legend += render_label(5, 0.0, 0.1)

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

            node_metric = dataframe.loc[df_index, self.metric]

            metric_precision = "{:." + str(self.precision) + "f}"
            metric_str = (
                self._ansi_color_for_metric(node_metric)
                + metric_precision.format(node_metric)
                + self.colors.end
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

            result = u"{indent}{metric_str} {name_str}".format(
                indent=indent, metric_str=metric_str, name_str=name_str
            )
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

            if node.children:
                last_child = node.children[-1]

            for child in node.children:
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
        proportion_of_total = metric / self.max_metric

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
        else:
            return self.colors.colormap[5]

    def _ansi_color_for_name(self, node_name):
        if "<unknown procedure>" in node_name or "<unknown file>" in node_name:
            return ""
        else:
            return self.colors.bg_dark_blue_255 + self.colors.white_255

    class colors_enabled:
        colormap = [
            "\033[38;5;160m",
            "\033[38;5;208m",
            "\033[38;5;220m",
            "\033[38;5;193m",
            "\033[38;5;113m",
            "\033[38;5;28m",
        ]

        bg_dark_blue_255 = "\033[48;5;24m"
        white_255 = "\033[38;5;15m"

        faint = "\033[2m"
        end = "\033[0m"

    class colors_disabled:
        colormap = ["", "", "", "", "", "", ""]

        def __getattr__(self, key):
            return ""

    colors_disabled = colors_disabled()
