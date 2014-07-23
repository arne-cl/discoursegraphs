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
    def __init__(self, decour_filepath, name=None, namespace='decour'):
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
        """
        # super calls __init__() of base class DiscourseDocumentGraph
        super(DecourDocumentGraph, self).__init__()

        self.name = name if name else os.path.basename(decour_filepath)
        self.ns = namespace
        self.root = self.ns+':root_node'
        self.add_node(self.root, layers={self.ns})  # TODO: add metadata to root node
        self.tokens = []

        self.turns = []
        self.utterances = []

        tree = etree.parse(decour_filepath)
        root_element = tree.getroot()
        #~ token_spans = self._parse_decour(root_element)
        #~ self._add_document_structure(token_spans)

        #~ for i, (token, spans) in enumerate(token_spans):
            #~ self._add_token_to_document(i, token, spans, connected)


if __name__ == "__main__":
    generic_converter_cli(DecourDocumentGraph, 'DeCour (court transcripts)')
