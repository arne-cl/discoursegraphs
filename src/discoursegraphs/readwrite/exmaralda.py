#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann

"""
The ``exmaralda`` module converts a ``DiscourseDocumentGraph`` (possibly
containing multiple annotation layers) into an Exmaralda ``*.exb`` file.

WARNING: This module contains lots of bad, academic code (i.e. I needed to get
stuff done quickly for a presentation and didn't take the time to add
parameters and refactor large methods).
"""

import os
import sys
from collections import defaultdict
from lxml import etree
from lxml.builder import ElementMaker

from discoursegraphs import (get_annotation_layers, get_pointing_chains,
                             get_span, select_nodes_by_layer)
from discoursegraphs.util import create_dir


class ExmaraldaFile(object):
    """
    This class converts a DiscourseDocumentGraph into an Exmaralda file.

    Attributes
    ----------
    toknode2id : dict
        maps from a token node ID to its Exmaralda ID (ID in the common
        timeline)
    """
    def __init__(self, docgraph, remove_redundant_layers=True):
        """
        Parameters
        ----------
        docgraph : DiscourseDocumentGraph
            the document graph to be converted
        """
        self.toknode2id = {node_id: i
                           for i, node_id in enumerate(docgraph.tokens)}
        self.E = ElementMaker()
        self.tier_count = 0
        self.tree = self.__add_document_structure(docgraph,
                                                  remove_redundant_layers)

    def __str__(self):
        """
        returns the generated Exmaralda ``*.exb`` file as a string.
        """
        return etree.tostring(self.tree, pretty_print=True,
                              xml_declaration=True, encoding='UTF-8')

    def write(self, output_filepath):
        """
        Parameters
        ----------
        output_filepath : str
            relative or absolute path to the Exmaralda file to be created
        """
        with open(output_filepath, 'w') as out_file:
            out_file.write(self.__str__())

    def __create_document_header(self):
        """
        Look, mum! XML generation without string concatenation!1!!

        This creates an empty, but functional header for an Exmaralda *.exb
        file.
        """
        E = self.E
        root = E('basic-transcription')
        head = E('head')

        meta = E('meta-information')
        project = E('project-name')
        tname = E('transcription-name')
        ref_file = E('referenced-file', url="")
        ud = E('ud-meta-information')
        comment = E('comment')
        tconvention = E('transcription-convention')
        meta.append(project)
        meta.append(tname)
        meta.append(ref_file)
        meta.append(ud)
        meta.append(comment)
        meta.append(tconvention)

        speakers = E('speakertable')
        head.append(meta)
        head.append(speakers)
        root.append(head)
        return root

    def __add_document_structure(self, docgraph,
                                 remove_redundant_layers=True):
        E = self.E
        root = self.__create_document_header()

        body = E('basic-body')
        timeline = E('common-timeline')

        # for n tokens we need to create n+1 timeline indices
        for i in xrange(len(docgraph.tokens)+1):
            idx = str(i)
            # example: <tli id="T0" time="0"/>
            timeline.append(E('tli', {'id': 'T'+idx, 'time': idx}))

        body.append(timeline)
        body = self.__add_token_tiers(docgraph, body)

        annotation_layers = get_annotation_layers(docgraph)
        for layer in annotation_layers:
            if remove_redundant_layers:
                if is_informative(layer):
                    self.__add_annotation_tier(docgraph, body, layer)
            else:  # always add all layers
                self.__add_annotation_tier(docgraph, body, layer)

        self.__add_coreference_chain_tiers(docgraph, body)
        root.append(body)
        return root

    def __add_annotation_tier(self, docgraph, body, annotation_layer):
        """
        adds a span-based annotation layer as a <tier> to the Exmaralda <body>.

        Parameter
        ---------
        docgraph : DiscourseDocumentGraph
            the document graph from which the chains will be extracted
        body : etree._Element
            an etree representation of the <basic_body> element (and all its
            descendants) of the Exmaralda file
        annotation_layer : str
            the name of a layer, e.g. 'tiger', 'tiger:token' or 'mmax:sentence'
        """
        layer_cat = annotation_layer.split(':')[-1]
        temp_tier = self.E('tier',
                           {'id': "TIE{}".format(self.tier_count),
                            'category': layer_cat, 'type': "t",
                            'display-name': "[{}]".format(annotation_layer)})
        self.tier_count += 1

        for node_id in select_nodes_by_layer(docgraph, annotation_layer):
            span_node_ids = get_span(docgraph, node_id)
            if span_node_ids:
                start_id, end_id = self.__span2event(span_node_ids)
                event_label = docgraph.node[node_id].get('label', '')
                # TODO: dirty hack to remove 'markable_n:sentence'
                # annotations
                if not event_label.endswith(':sentence'):
                    event = self.E('event',
                                   {'start': "T{}".format(start_id),
                                    'end': "T{}".format(end_id)},
                                   event_label)
                    temp_tier.append(event)
        body.append(temp_tier)

    def __add_coreference_chain_tiers(self, docgraph, body,
                                      min_chain_length=3):
        """
        Parameters
        ----------
        docgraph : DiscourseDocumentGraph
            the document graph from which the chains will be extracted
        body : etree._Element
            an etree representation of the <basic_body> element (and all its
            descendants) of the Exmaralda file
        min_chain_length : int
            don't add tiers for chains with less than N elements (default: 3)

        TODO: this method assumes that each pointing relation chains signifies
        a coreference chain.
        """
        E = self.E

        for i, chain in enumerate(get_pointing_chains(docgraph)):
            chain_tier = E('tier',
                           {'id': "TIE{}".format(self.tier_count),
                            'category': "chain", 'type': "t",
                            'display-name': "[coref-chain-{}]".format(i)})
            self.tier_count += 1

            chain_length = len(chain)
            if chain_length < min_chain_length:
                continue  # ignore short chains

            for j, node_id in enumerate(chain):
                span_node_ids = get_span(docgraph, node_id)
                if span_node_ids:
                    start_id, end_id = self.__span2event(span_node_ids)
                    element_str = "chain_{0}: {1}/{2}".format(
                        i, chain_length-j, chain_length)
                    chain_tier.append(
                        E('event', {'start': "T{}".format(start_id),
                                    'end': "T{}".format(end_id)}, element_str))
            body.append(chain_tier)

    def __add_token_tiers(self, docgraph, body, default_ns='tiger'):
        """
        adds all tiers that annotate single tokens (e.g. token string, lemma,
        POS tag) to the etree representation of the Exmaralda XML file.

        Parameters
        ----------
        docgraph : DiscourseDocumentGraph
            the document graph to be converted
        body : etree._Element
            an etree representation of the <basic_body> element (and all its
            descendants) of the Exmaralda file
        default_ns : str
            the default namespace (i.a. used to extract the token strings
            only once)
        """
        E = self.E
        token_tier = E('tier',
                       {'id': "TIE{}".format(self.tier_count),
                        'category': "tok", 'type': "t",
                        'display-name': "[tok]"})
        self.tier_count += 1

        token_attribs = defaultdict(lambda: defaultdict(str))
        for token_node_id in docgraph.tokens:
            for attrib in docgraph.node[token_node_id]:
                is_boring_attrib = attrib in ('layers', 'label')
                is_boring_cat = attrib.split(':')[-1] in ('token',
                                                          'id', 'word',
                                                          'morph', 'lemma')
                if not is_boring_attrib and not is_boring_cat:
                    token_attribs[attrib][token_node_id] = \
                        docgraph.node[token_node_id][attrib]

        for i, (_tok_id, token_str) in enumerate(docgraph.get_tokens()):
            # example: <event start="T0" end="T1">Zum</event>
            token_tier.append(
                E('event', {'start': "T{}".format(i),
                            'end': "T{}".format(i+1)}, token_str))
        body.append(token_tier)

        for anno_tier in token_attribs:
            category = anno_tier.split(':')[-1]
            temp_tier = E(
                'tier', {'id': "TIE{}".format(self.tier_count),
                         'category': category, 'type': "t",
                         'display-name': "[{}]".format(anno_tier)})
            self.tier_count += 1
            for token_node_id in token_attribs[anno_tier]:
                token_tier_id = self.toknode2id[token_node_id]
                token_attrib = token_attribs[anno_tier][token_node_id]
                temp_tier.append(
                    E('event', {'start': "T{}".format(token_tier_id),
                                'end': "T{}".format(token_tier_id+1)},
                      token_attrib))
            body.append(temp_tier)
        return body

    def __span2event(self, span_node_ids):
        """
        converts a span of tokens (list of token node IDs) into an Exmaralda
        event (start and end ID).

        Parameters
        ----------
        span_node_ids : list of str
            sorted list of node IDs representing a span of tokens

        Returns
        -------
        event : tuple of (str, str)
            event start ID and event end ID
        """
        return (self.toknode2id[span_node_ids[0]],
                self.toknode2id[span_node_ids[-1]]+1)


def is_informative(layer):
    """
    returns true, iff the annotation layer contains information that 'makes
    sense' in Exmaralda (i.e. there are annotations we don't need and which
    would clutter the Exmaralda Partitur editor).

    Parameters
    ----------
    layer : str
        the name of a layer, e.g. 'tiger', 'tiger:token' or 'mmax:sentence'

    Returns
    -------
    is_informative : bool
        Returns True, iff the layer is likely to contain information that
        should be exported to Exmaralda. Usually, we don't want to include
        information about sentence or token boundaries, since they are already
        obvious from the token layer.
    """
    # very dirty hack
    # TODO: fix Issue #36 (efficient self.layers / get_hierarchical_layers()
    return layer not in ('tiger', 'tiger:token', 'tiger:sentence:root',
                         'tiger:sentence:vroot', 'tiger:edge', 'tiger:secedge',
                         'exmaralda', 'exmaralda:tier',
                         'discoursegraph')


def write_exb(docgraph, output_file):
    """
    converts a DiscourseDocumentGraph into an Exmaralda ``*.exb`` file and
    writes it to the given file (or file path).
    """
    exmaralda_file = ExmaraldaFile(docgraph)
    assert isinstance(output_file, (str, file))
    if isinstance(output_file, str):
        path_to_file = os.path.dirname(output_file)
        if not os.path.isdir(path_to_file):
            create_dir(path_to_file)
        exmaralda_file.write(output_file)
    else:  # output_file is a file object
        output_file.write(exmaralda_file.__str__())


if __name__ == "__main__":
    import argparse
    import cPickle as pickle

    parser = argparse.ArgumentParser()
    parser.add_argument('input_file',
                        help='pickle file of a document graph to be converted')
    parser.add_argument('output_file', nargs='?', default=sys.stdout)
    args = parser.parse_args(sys.argv[1:])

    assert os.path.isfile(args.input_file), \
        "'{}' isn't a file".format(args.input_file)

    with open(args.input_file, 'rb') as docgraph_file:
        docgraph = pickle.load(docgraph_file)
    write_exb(docgraph, args.output_file)
