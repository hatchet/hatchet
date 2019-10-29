# -*- coding: utf-8 -*-

# Copyright (c) 2014, Joe Rickerby
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


def trees_as_text(
    roots,
    dataframe,
    metric,
    name,
    context,
    rank,
    thread,
    threshold,
    expand_names,
    unicode,
    color,
):
    """Calls as_text in turn for each tree in the graph/forest."""
    text = ""

    # call as_text for each root in the graph
    for root in roots:
        text += as_text(
            root,
            dataframe,
            metric,
            name,
            context,
            rank,
            thread,
            threshold,
            expand_names,
            unicode=unicode,
            color=color,
        )

    return text


def as_text(
    hnode,
    dataframe,
    metric,
    name,
    context,
    rank,
    thread,
    threshold,
    expand_names,
    indent="",
    child_indent="",
    unicode=False,
    color=False,
):
    """Code adapted from https://github.com/joerick/pyinstrument

    The function takes a node, and creates a string for the node.
    """
    # set dataframe index based on if rank is a part of the index
    if "rank" in dataframe.index.names and "thread" in dataframe.index.names:
        df_index = (hnode, rank, thread)
    elif "rank" in dataframe.index.names:
        df_index = (hnode, rank)
    elif "thread" in dataframe.index.names:
        df_index = (hnode, thread)
    else:
        df_index = hnode

    colors = colors_enabled if color else colors_disabled

    node_time = dataframe.loc[df_index, metric]
    max_time = dataframe[metric].max()

    # only display nodes whose metric is greater than some threshold
    if node_time >= threshold * max_time:
        time_str = "{:.3f}".format(node_time)
        func_name = dataframe.loc[df_index, name]

        # shorten names longer than 39 characters
        if expand_names is False:
            if len(func_name) > 39:
                func_name = func_name[:18] + "..." + func_name[len(func_name) - 18 :]

        if color:
            time_str = ansi_color_for_time(node_time, max_time) + time_str + colors.end

        # add context (filename etc.) if requested
        if context in dataframe.columns:
            result = "{indent}{time_str} {function}  {c.faint}{code_position}{c.end}\n".format(
                indent=indent,
                time_str=time_str,
                function=func_name,
                code_position=dataframe.loc[df_index, context],
                c=colors_enabled if color else colors_disabled,
            )
        else:
            result = "{indent}{time_str} {function}\n".format(
                indent=indent, time_str=time_str, function=func_name
            )

        # only display those edges where child's metric is greater than
        # threshold
        children = []
        for child in hnode.children:
            if "rank" in dataframe.index.names and "thread" in dataframe.index.names:
                df_index = (child, rank, thread)
            elif "rank" in dataframe.index.names:
                df_index = (child, rank)
            elif "thread" in dataframe.index.names:
                df_index = (child, thread)
            else:
                df_index = child
            child_time = dataframe.loc[df_index, metric]
            if child_time >= threshold * max_time:
                children.append(child)

        if children:
            last_child = children[-1]

        for child in children:
            if child is not last_child:
                c_indent = child_indent + ("├─ " if unicode else "|- ")
                cc_indent = child_indent + ("│  " if unicode else "|  ")
            else:
                c_indent = child_indent + ("└─ " if unicode else "`- ")
                cc_indent = child_indent + "   "
            result += as_text(
                child,
                dataframe,
                metric,
                name,
                context,
                rank,
                thread,
                threshold,
                expand_names,
                indent=c_indent,
                child_indent=cc_indent,
                unicode=unicode,
                color=color,
            )
    else:
        result = ""

    return result


def ansi_color_for_time(time, total):
    colors = colors_enabled
    if time > 0.9 * total:
        return colors.light_red + colors.faint
    elif time > 0.75 * total:
        return colors.red
    elif time > 0.25 * total:
        return colors.yellow
    elif time > 0.10 * total:
        return colors.green
    else:
        return colors.light_green + colors.faint


class colors_enabled:
    red = "\033[31m"
    light_red = "\033[91m"
    yellow = "\033[33m"
    light_green = "\033[92m"
    green = "\033[32m"

    bold = "\033[1m"
    faint = "\033[2m"

    end = "\033[0m"


class colors_disabled:
    def __getattr__(self, key):
        return ""


colors_disabled = colors_disabled()
