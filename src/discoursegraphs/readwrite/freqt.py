#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module contains code to convert discourse graphs into bracketed strings
for FREQT.
"""

import codecs
import os

from discoursegraphs import istoken
from discoursegraphs.readwrite.tree import sorted_bfs_successors
from discoursegraphs.util import create_dir, create_multiple_replace_func

FREQT_BRACKET_ESCAPE = {'(': r'-LRB-', ')': r'-RRB-'}
FREQT_ESCAPE_FUNC = create_multiple_replace_func(FREQT_BRACKET_ESCAPE)


def node2freqt(docgraph, node_id, child_str='', include_pos=False,
               escape_func=FREQT_ESCAPE_FUNC):
    """convert a docgraph node into a FREQT string."""
    node_attrs = docgraph.node[node_id]
    if istoken(docgraph, node_id):
        token_str = escape_func(node_attrs[docgraph.ns+':token'])
        if include_pos:
            pos_str = escape_func(node_attrs.get(docgraph.ns+':pos', ''))
            return u"({pos}({token}){child})".format(
                pos=pos_str, token=token_str, child=child_str)
        else:
            return u"({token}{child})".format(token=token_str, child=child_str)

    else:  # node is not a token
        label_str=escape_func(node_attrs.get('label', node_id))
        return u"({label}{child})".format(label=label_str, child=child_str)


def sentence2freqt(docgraph, root, successors=None, include_pos=False,
                   escape_func=FREQT_ESCAPE_FUNC):
    """convert a sentence subgraph into a FREQT string."""
    if successors is None:
        successors = sorted_bfs_successors(docgraph, root)

    if root in successors:  # root node has children / subgraphs
        embed_str = u"".join(sentence2freqt(docgraph, child, successors,
                                            include_pos=include_pos,
                                            escape_func=escape_func)
                             for child in successors[root])
        return node2freqt(
            docgraph, root, embed_str, include_pos=include_pos,
            escape_func=escape_func)
    else:  # root node has no children / subgraphs
        return node2freqt(docgraph, root, include_pos=include_pos,
                          escape_func=escape_func)


def docgraph2freqt(docgraph, root=None, include_pos=False,
                   escape_func=FREQT_ESCAPE_FUNC):
    """convert a docgraph into a FREQT string."""
    if root is None:
        return u"\n".join(
            sentence2freqt(docgraph, sentence, include_pos=include_pos,
                           escape_func=escape_func)
            for sentence in docgraph.sentences)
    else:
        return sentence2freqt(docgraph, root, include_pos=include_pos,
                              escape_func=escape_func)


def write_freqt(docgraph, output_filepath, include_pos=False):
    """convert a docgraph into a FREQT input file (one sentence per line)."""
    path_to_file = os.path.dirname(output_filepath)
    if not os.path.isdir(path_to_file):
        create_dir(path_to_file)
    with codecs.open(output_filepath, 'w', 'utf-8') as output_file:
        for sentence in docgraph.sentences:
            output_file.write(docgraph2freqt(docgraph, sentence,
                              include_pos=include_pos)+'\n')
