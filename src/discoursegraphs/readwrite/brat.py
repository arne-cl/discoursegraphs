#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
The ``brat`` module converts discourse graphs into brat annotation
files.
"""

import os
import codecs
import math
import itertools
from collections import defaultdict

import brewer2mpl
from unidecode import unidecode
import discoursegraphs as dg
from discoursegraphs.readwrite.mmax2 import spanstring2text, spanstring2tokens


ANNOTATION_CONF = u"""
[entities]

Markable

[relations]

Coreference\tArg1:Markable, Arg2:Markable, <REL-TYPE>:symmetric-transitive

# "Markable" annotations can nest arbitrarily

ENTITY-NESTING\tArg1:Markable, Arg2:Markable

[events]

[attributes]
"""


def brat_output(docgraph, layer=None, show_relations=True):
    """
    converts a document graph with pointing chains into a string representation
    of a brat *.ann file.

    Parameters
    ----------
    docgraph : DiscourseDocumentGraph
        a document graph which might contain pointing chains (e.g. coreference links)
    layer : str or None
        the name of the layer that contains the pointing chains (e.g. 'mmax' or 'pocores').
        If unspecified, all pointing chains in the document will be considered

    Returns
    -------
    ret_str : unicode
        the content of a brat *.ann file
    """
    # we can't rely on the .ns attribute of a merged graph
    if layer:
        namespace = dg.layer2namespace(layer)
    else:
        namespace = docgraph.ns

    ret_str = u''
    pointing_chains = dg.get_pointing_chains(docgraph, layer=layer)

    # a token can be part of 1+ markable(s)
    first_token2markables = defaultdict(list)
    markable_dict = {}
    markable_index = 1

    for pointing_chain in pointing_chains:
        for markable in sorted(pointing_chain, key=dg.util.natural_sort_key):
            span_tokens = spanstring2tokens(docgraph, docgraph.node[markable][namespace+':span'])
            span_text = dg.tokens2text(docgraph, span_tokens)
            first_token2markables[span_tokens[0]].append(markable)
            markable_dict[markable] = (markable_index, span_text, len(span_text))
            markable_index += 1

    onset = 0
    for token_id in docgraph.tokens:
        tok_len = len(docgraph.get_token(token_id))
        if token_id in first_token2markables:
            for markable in first_token2markables[token_id]:
                mark_index, mark_text, mark_len = markable_dict[markable]
                ret_str += u"T{0}\tMarkable {1} {2}\t{3}\n".format(
                    mark_index, onset, onset+mark_len, mark_text)
        onset += tok_len+1

    if show_relations:
        relation = 1
        for pointing_chain in pointing_chains:
            last_to_first_mention = sorted(pointing_chain, key=dg.util.natural_sort_key, reverse=True)
            for i in xrange(0, len(pointing_chain)-1):
                chain_element = markable_dict[last_to_first_mention[i]][0]
                prev_chain_element = markable_dict[last_to_first_mention[i+1]][0]
                ret_str += u"R{0}\tCoreference Arg1:T{1} Arg2:T{2}\n".format(
                    relation, chain_element, prev_chain_element)
                relation += 1
    return ret_str


def create_visual_conf(docgraph, pointing_chains):
    """
    creates a visual.conf file (as a string)
    for the given document graph.
    """
    num_of_entities = len(pointing_chains)
    mapsize = max(3, min(12, num_of_entities)) # 3 <= mapsize <= 12
    colormap = brewer2mpl.get_map(name='Paired', map_type='Qualitative', number=mapsize)
    colors = range(mapsize) * int(math.ceil(num_of_entities / float(mapsize)))
    # recycle colors if we need more than 12
    endless_color_cycle = itertools.cycle(colors)

    ret_str = u'[drawing]\n\n'
    for chain in pointing_chains:
        background_color = colormap.hex_colors[endless_color_cycle.next()]
        for markable in chain:
            span_tokens = spanstring2tokens(docgraph, docgraph.node[markable][docgraph.ns+':span'])
            span_text = dg.tokens2text(docgraph, span_tokens)
            ascii_markable = unidecode(span_text)
            ret_str += u'{0}\tbgColor:{1}\n'.format(ascii_markable,
                                                  background_color)
    ret_str += '\n[labels]'
    return ret_str


def write_brat(docgraph, output_dir, layer='mmax', show_relations=True):
    dg.util.create_dir(output_dir)
    doc_name = os.path.basename(docgraph.name)
    with codecs.open(os.path.join(output_dir, doc_name+'.txt'),
                     'wb', encoding='utf-8') as txtfile:
        txtfile.write(dg.get_text(docgraph))

    anno_str = brat_output(docgraph, layer=layer,
                           show_relations=show_relations)

    with codecs.open(os.path.join(output_dir, 'annotation.conf'),
                     'wb', encoding='utf-8') as annotation_conf:
        annotation_conf.write(ANNOTATION_CONF)
    #~ with codecs.open(os.path.join(output_dir, 'visual.conf'),
                     #~ 'wb', encoding='utf-8') as visual_conf:
        #~ visual_conf.write(visual_conf_str)
    with codecs.open(os.path.join(output_dir, doc_name+'.ann'),
                     'wb', encoding='utf-8') as annfile:
        annfile.write(anno_str)
