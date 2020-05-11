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
    precision,
    depth,
    expand_names,
    invert_colors,
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
            precision,
            depth,
            expand_names,
            invert_colors,
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
    precision,
    depth,
    expand_names,
    invert_colors,
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

    if color and not invert_colors:
        colors = colors_enabled_default
    elif color and invert_colors:
        colors = colors_enabled_invert
    else:
        colors = colors_disabled

    node_time = dataframe.loc[df_index, metric]
    max_time = dataframe[metric].max()
    node_depth = hnode._depth

    # only display nodes whose metric is greater than some threshold
    # if abs(node_time) >= threshold * max_time and (node_depth < depth or not depth):
    if abs(node_time) >= threshold * max_time and node_depth < depth:
        time_str_precision = "{:." + str(precision) + "f}"
        time_str = time_str_precision.format(node_time)
        func_name = dataframe.loc[df_index, name]

        # shorten names longer than 39 characters
        if expand_names is False:
            if len(func_name) > 39:
                func_name = func_name[:18] + "..." + func_name[len(func_name) - 18 :]

        if color:
            time_str = (
                ansi_color_for_time(node_time, max_time, colors) + time_str + colors.end
            )

        # add context (filename etc.) if requested
        if context in dataframe.columns:
            if color and not invert_colors:
                colors = colors_enabled_default
            elif color and invert_colors:
                colors = colors_enabled_invert
            else:
                colors = colors_disabled
            result = "{indent}{time_str} {function}  {c.faint}{code_position}{c.end}\n".format(
                indent=indent,
                time_str=time_str,
                function=func_name,
                code_position=dataframe.loc[df_index, context],
                c=colors,
            )
        else:
            if "_missing_node" in dataframe.columns:
                # if value of _missing_node column is not nan, then this is a missing
                # node, so add decorators to differentiate it
                is_missing_node = dataframe.loc[df_index, "_missing_node"]
                if is_missing_node == "R":
                    result = "{indent}{time_str} \033[1m[[{function}]] (R)\033[0m\n".format(
                        indent=indent, time_str=time_str, function=func_name
                    )
                elif is_missing_node == "L":
                    result = "{indent}{time_str} \033[1m[[{function}]] (L)\033[0m\n".format(
                        indent=indent, time_str=time_str, function=func_name
                    )
                elif is_missing_node == "":
                    result = "{indent}{time_str} {function}\n".format(
                        indent=indent, time_str=time_str, function=func_name
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
            if abs(child_time) >= threshold * max_time:
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
                precision,
                depth,
                expand_names,
                invert_colors,
                indent=c_indent,
                child_indent=cc_indent,
                unicode=unicode,
                color=color,
            )
    else:
        result = ""

    return result


def ansi_color_for_time(time, total, c):
    colors = c
    if time > 0.9 * total:
        return colors.highest + colors.faint
    elif time > 0.75 * total:
        return colors.high
    elif time > 0.25 * total:
        return colors.med
    elif time > 0.10 * total:
        return colors.low
    else:
        return colors.lowest + colors.faint


# \033[91m red high contrast
# \033[31m red
# \033[32m yellow
# \033[32m green
# \033[92m green high contrast


class colors_enabled_default:
    highest = "\033[91m"
    high = "\033[31m"
    med = "\033[33m"
    low = "\033[32m"
    lowest = "\033[92m"

    bold = "\033[1m"
    faint = "\033[2m"

    end = "\033[0m"


class colors_enabled_invert:
    lowest = "\033[91m"
    low = "\033[31m"
    med = "\033[33m"
    high = "\033[32m"
    highest = "\033[92m"

    bold = "\033[1m"
    faint = "\033[2m"

    end = "\033[0m"


class colors_disabled:
    def __getattr__(self, key):
        return ""


colors_disabled = colors_disabled()
