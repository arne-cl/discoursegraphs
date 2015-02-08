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


def brat_output(docgraph, layer=None):
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
    ret_str = u''
    pointing_chains = dg.get_pointing_chains(docgraph, layer=layer)
    markables = sorted(itertools.chain(*pointing_chains),
                       key=dg.util.natural_sort_key)
    markable_strings = []

    # map from a token ID to a (markable ID, markable text, span length) tuple of its span,
    # iff it is the first token of that span. Otherwise, it just maps to the markable ID
    token2markable = {}
    markable2idx = {}
    for midx, markable in enumerate(markables, 1):
        span_tokens = spanstring2tokens(docgraph, docgraph.node[markable][docgraph.ns+':span'])
        span_text = dg.tokens2text(docgraph, span_tokens)
        markable_strings.append(span_text)
        token2markable[span_tokens[0]] = (markable, midx, span_text, len(span_text))
        markable2idx[markable] = midx

        if len(span_tokens) > 1:
            for token_id in span_tokens[1:]:
                token2markable[token_id] = markable

    onset = 0
    for token_id in docgraph.tokens:
        tok_len = len(docgraph.get_token(token_id))
        if token_id in token2markable:
            if isinstance(token2markable[token_id], tuple):
                markable, midx, mark_text, mark_len = token2markable[token_id]
                ret_str += u"T{}\tMarkable {} {}\t{}\n".format(
                    midx, onset, onset+mark_len, mark_text)
            else: # if the token is not the first token of the markable
                pass
        onset += tok_len+1

    relation = 1
    for chain in pointing_chains:
        last_to_first_mention = list(reversed(chain))
        for i in xrange(0, len(chain)-1):
            ret_str += u"R{0}\tCoreference Arg1:T{1} Arg2:T{2}\n".format(
                relation, markable2idx[last_to_first_mention[i]],
                markable2idx[last_to_first_mention[i+1]])
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
            ret_str += u'{}\tbgColor:{}\n'.format(ascii_markable,
                                                  background_color)
    ret_str += '\n[labels]'
    return ret_str


def write_brat(docgraph, output_dir, layer=None):
    dg.util.create_dir(output_dir)
    doc_name = os.path.basename(docgraph.name)
    with codecs.open(os.path.join(output_dir, doc_name+'.txt'),
                     'wb', encoding='utf-8') as txtfile:
        txtfile.write(dg.get_text(docgraph))

    anno_str = brat_output(docgraph, layer=layer)

    with codecs.open(os.path.join(output_dir, 'annotation.conf'),
                     'wb', encoding='utf-8') as annotation_conf:
        annotation_conf.write(ANNOTATION_CONF)
    #~ with codecs.open(os.path.join(output_dir, 'visual.conf'),
                     #~ 'wb', encoding='utf-8') as visual_conf:
        #~ visual_conf.write(visual_conf_str)
    with codecs.open(os.path.join(output_dir, doc_name+'.ann'),
                     'wb', encoding='utf-8') as annfile:
        annfile.write(anno_str)
