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

def as_text(ccnode, root, src_files, metric, threshold,
            indent=u'', child_indent=u'', unicode=False, color=False):
    """ Code adapted from https://github.com/joerick/pyinstrument
    """
    colors = colors_enabled if color else colors_disabled
    if metric is 'exclusive':
        node_time = ccnode.metrics[1][1] # exc, avg
        root_time = root.metrics[1][1]   # exc, avg
    else:
        node_time = ccnode.metrics[0][1] # inc, avg
        root_time = root.metrics[0][1]   # inc, avg

    time_str = '{:.3f}'.format(node_time)

    if color:
        time_str = ansi_color_for_time(node_time, root_time) + time_str + colors.end

    result = u'{indent}{time_str} {function}  {c.faint}{code_position}{c.end}\n'.format(indent=indent, time_str=time_str, function=ccnode.name,
         code_position=src_files[ccnode.src_file],
         c=colors_enabled if color else colors_disabled)

    children = [child for child in ccnode.children if node_time >= threshold * root_time]

    if children:
        last_child = children[-1]

    for child in children:
        if child is not last_child:
            c_indent = child_indent + (u'├─ ' if unicode else '|- ')
            cc_indent = child_indent + (u'│  ' if unicode else '|  ')
        else:
            c_indent = child_indent + (u'└─ ' if unicode else '`- ')
            cc_indent = child_indent + u'   '
        result += as_text(child, root, src_files, metric, threshold,
                          indent=c_indent, child_indent=cc_indent,
                          unicode=unicode, color=color)

    return result


def ansi_color_for_time(time, total):
    colors = colors_enabled
    if time > 0.6 * total:
        return colors.red
    elif time > 0.2 * total:
        return colors.yellow
    elif time > 0.05 * total:
        return colors.green
    else:
        return colors.bright_green + colors.faint


class colors_enabled:
    red = '\033[31m'
    green = '\033[32m'
    yellow = '\033[33m'
    blue = '\033[34m'
    cyan = '\033[36m'
    bright_green = '\033[92m'

    bold = '\033[1m'
    faint = '\033[2m'

    end = '\033[0m'


class colors_disabled:
    def __getattr__(self, key):
        return ''

colors_disabled = colors_disabled()
