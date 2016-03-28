#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann

"""
This module converts a DeCour XML file (used for the DeCour 'DEception in
COURts corpus') into a networkx-based directed graph
(``DiscourseDocumentGraph``).
"""

import os
from lxml import etree

from discoursegraphs import DiscourseDocumentGraph, EdgeTypes
from discoursegraphs.readwrite.generic import generic_converter_cli
#~ from discoursegraphs.util import ensure_unicode


class DecourDocumentGraph(DiscourseDocumentGraph):
    """
    represents a DeCour XML file as a multidigraph.

    Attributes
    ----------
    ns : str
        the namespace of the graph (default: decour)
    tokens : list of int
        a list of node IDs (int) which represent the tokens in the
        order they occur in the text
    root : str
        name of the document root node ID
        (default: 'decour:root_node')
    """
    def __init__(self, decour_filepath, name=None, namespace='decour',
                 precedence=False):
        """
        reads a DeCour XML file and converts it into a multidigraph.

        Parameters
        ----------
        decour_filepath : str
            relative or absolute path to a DeCour XML file
        name : str or None
            the name or ID of the graph to be generated. If no name is
            given, the basename of the input file is used.
        namespace : str
            the namespace of the graph (default: decour)
        precedence : bool
            add precedence relation edges (root precedes token1, which precedes
            token2 etc.)
        """
        # super calls __init__() of base class DiscourseDocumentGraph
        super(DecourDocumentGraph, self).__init__()

        self.name = name if name else os.path.basename(decour_filepath)
        self.ns = namespace
        self.root = self.ns+':root_node'
        # TODO: add metadata to root node
        self.add_node(self.root, layers={self.ns})
        self.tokens = []

        self.token_count = 1
        self.act_count = 1

        self.turns = []
        self.utterances = []

        tree = etree.parse(decour_filepath)
        self._parse_decour(tree)
        if precedence:
            self.add_precedence_relations()

    def _parse_decour(self, tree):
        """
        <!ELEMENT hearing (header, intro, turn+, conclu?)>
        # <!ELEMENT turn (act?|utterance+)*>
        # <!ELEMENT utterance (#PCDATA|token|lemma|pos)*>
        """
        self._add_dominance_relation(self.root, 'intro')
        self._add_token_span_to_document(tree.find('/intro'))

        for turn in tree.iterfind('/turn'):
            turn_id = 'turn_{}'.format(turn.attrib['nrgen'])
            self._add_dominance_relation(self.root, turn_id)
            self.turns.append(turn_id)
            act = turn.find('./act')
            if act is not None:
                self._add_dominance_relation(turn_id,
                                             'act_{}'.format(self.act_count))
                self._add_token_span_to_document(act)

            for utter in turn.iterfind('./utterance'):
                    utter_id = 'utterance_{}'.format(utter.attrib['nrgen'])
                    self._add_dominance_relation(turn_id, utter_id)
                    self._add_utterance_to_document(utter)

        conclu = tree.find('/conclu')
        if conclu is not None:
            self._add_dominance_relation(self.root, 'conclu')
            self._add_token_span_to_document(conclu)

    def _add_token_to_document(self, token_string, token_attrs=None):
        """add a token node to this document graph"""
        token_feat = {self.ns+':token': token_string}
        if token_attrs:
            token_attrs.update(token_feat)
        else:
            token_attrs = token_feat
        token_id = 'token_{}'.format(self.token_count)
        self.add_node(token_id, layers={self.ns, self.ns+':token'},
                      attr_dict=token_attrs)
        self.token_count += 1
        self.tokens.append(token_id)
        return token_id

    def _add_utterance_to_document(self, utterance):
        """add an utterance to this docgraph (as a spanning relation)"""
        utter_id = 'utterance_{}'.format(utterance.attrib['nrgen'])
        norm, lemma, pos = [elem.text.split()
                            for elem in utterance.iterchildren()]
        for i, word in enumerate(utterance.text.split()):
            token_id = self._add_token_to_document(
                word, token_attrs={self.ns+':norm': norm[i],
                                   self.ns+':lemma': lemma[i],
                                   self.ns+':pos': pos[i]})
            self._add_spanning_relation(utter_id, token_id)
        self.utterances.append(utter_id)

    def _add_token_span_to_document(self, span_element):
        """
        adds an <intro>, <act> or <conclu> token span to the document.
        """
        for token in span_element.text.split():
            token_id = self._add_token_to_document(token)
            if span_element.tag == 'act':  # doc can have 0+ acts
                self._add_spanning_relation('act_{}'.format(self.act_count),
                                            token_id)
            else:  # <intro> or <conclu>
                self._add_spanning_relation(span_element.tag, token_id)
        if span_element.tag == 'act':
            self.act_count += 1

    def _add_dominance_relation(self, source, target):
        """add a dominance relation to this docgraph"""
        # TODO: fix #39, so we don't need to add nodes by hand
        self.add_node(target, layers={self.ns, self.ns+':unit'})
        self.add_edge(source, target,
                      layers={self.ns, self.ns+':discourse'},
                      edge_type=EdgeTypes.dominance_relation)

    def _add_spanning_relation(self, source, target):
        """add a spanning relation to this docgraph"""
        self.add_edge(source, target, layers={self.ns, self.ns+':unit'},
                      edge_type=EdgeTypes.spanning_relation)


# pseudo-function to create a document graph from a DeCour XML file
read_decour = DecourDocumentGraph


if __name__ == "__main__":
    generic_converter_cli(DecourDocumentGraph, 'DeCour (court transcripts)')
