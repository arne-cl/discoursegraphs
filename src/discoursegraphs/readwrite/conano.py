#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann

"""
This module converts a Conano XML file (used by Conano to annotate
connectives) into a networkx-based directed graph
(``DiscourseDocumentGraph``).
"""

import sys
from collections import OrderedDict
from lxml import etree
import argparse
import re
import pudb  # TODO: rm debug

from discoursegraphs import DiscourseDocumentGraph
from discoursegraphs.readwrite.generic import generic_converter_cli
from discoursegraphs.util import ensure_unicode


REDUCE_WHITESPACE_RE = re.compile(' +')


class ConanoDocumentGraph(DiscourseDocumentGraph):
    """
    represents a Conano XML file as a multidigraph.

    Attributes
    ----------
    tokens : list of int
        a list of node IDs (int) which represent the tokens in the
        order they occur in the text
    root : str
        name of the document root node ID
        (default: 'conano:root_node')
    """
    def __init__(self, conano_filepath, name=None):
        """
        reads a Conano XML file and converts it into a multidigraph.

        Parameters
        ----------
        conano_filepath : str
            relative or absolute path to a Conano XML file
        name : str or None
            the name or ID of the graph to be generated. If no name is
            given, the basename of the input file is used.
        """
        # super calls __init__() of base class DiscourseDocumentGraph
        super(DiscourseDocumentGraph, self).__init__()

        if name is not None:
            self.name = os.path.basename(conano_filepath)
        self.ns = 'conano'
        self.root = self.ns+':root_node'
        self.add_node(self.root, layers={self.ns})

        #~ pudb.set_trace() # TODO: rm
        root_element = etree.parse(conano_filepath).getroot()
        token_spans = self._parse_conano(root_element)
        self._add_document_structure(token_spans)

        for i, (token, spans) in enumerate(token_spans):
            self._add_token_to_document(i, token, spans)


    def _add_document_structure(self, token_spans):
        """
        adds the basic structure of the annotation to the graph,
        i.e. an edge from the document root node to each unit and an
        edge from each unit to its 'int', 'ext' (sub-units) and
        'connective'.

        TODO: handle continuous vs. uncontinuous connectives!
        """
        unit_ids = set()
        for (t, tdict) in token_spans:
            for (span_type, span_id) in tdict['spans']:
                unit_ids.add(span_id)

        for unit_id in unit_ids:
            for node_id in ('unit', 'int', 'ext', 'connective'):
                self.add_node(
                    '{0}-{1}'.format(node_id, unit_id),
                    layers={self.ns, self.ns+':unit'})

            self.add_edge(self.root, 'unit-{}'.format(unit_id),
                          layers={self.ns, self.ns+':unit'})
            for to_node in ('ext', 'int', 'connective'):
                self.add_edge('unit-{}'.format(unit_id),
                              '{0}-{1}'.format(to_node, unit_id),
                              layers={self.ns, self.ns+':unit'},
                              edge_type='dominates')


    def _add_token_to_document(self, token_id, token, token_attribs):
        """
        TODO: add 'relation' attribute to connective node!
        TODO: how to handle modifiers?

        Parameters
        ----------
        token_id : int
            the ID of the token
        token : str or unicode
            the token itself
        token_attribs : dict
            a dict containing all the spans a token belongs to (and
            in case of connectives the relation it is part of)
        """
        unit_node_ids = [] # add edges from root later on
        self.add_node(
            token_id,
            layers={self.ns, self.ns+':token'},
            attr_dict={self.ns+':token': ensure_unicode(token)})

        for (span_type, span_id) in token_attribs['spans']:
            if span_type in ('int', 'ext', 'connective'):
                self.add_edge("{0}-{1}".format(span_type, span_id),
                              token_id, layers={self.ns, self.ns+':unit'},
                              edge_type='contains')
            elif span_type == 'modifier':
                raise NotImplementedError("Can't handle modifiers, yet")
            else:
                raise NotImplementedError("Can't handle span_type '{}', yet".format(span_type))


        #~ # we might still need this for alignment debugging
        #~ conano_plaintext = etree.tostring(self.tree, encoding='utf8',
                                          #~ method='text')
        #~ tokens = conano_plaintext.split()


    def _parse_conano_element(self, token_list, element, part='text'):
        """
        Parameters
        ----------
        token_list : list of str or unicode
            the list of tokens to which the tokens from this element
            are added
        element : etree._Element
            an element of the etree representation of a Conano XML file
        part : str
            the part of the etree element from which the tokens are
            extracted (i.e. 'text' or 'tail')
        """
        assert part in ('text', 'tail')
        element_str = getattr(element, part)
        if element_str:
            cleaned_str = element_str.strip()
            if cleaned_str:
                tokens = cleaned_str.split()
                dominating_spans = []
                if element.tag != 'discourse': # discourse is the root element
                    dominating_spans.append((element.attrib.get('type', element.tag),
                                             element.attrib.get('id', '')))

                dominating_spans.extend([(a.attrib.get('type', a.tag), a.attrib.get('id', ''))
                                         for a in element.iterancestors()
                                         if a.tag != 'discourse'])

                for token in tokens:
                    if element.tag == 'connective':
                        token_list.append((token, {'spans': dominating_spans,
                                                   'relation': element.attrib['relation']}))
                    else:
                        token_list.append((token, {'spans': dominating_spans}))


    def _parse_conano(self, root_element):
        """
        parses Conano and returns (token, spans) tuples describing the
        spans a token belongs to.

        Parameters
        ----------
        root_element : _Element
            root element of an etree representing a ConanoXML file

        Returns
        -------
        tokens : list of (str, dict)
            a list of (token, spans) tuples describing all the units,
            connectives and modifiers a token belongs to
        """
        tokens = []
        self._parse_conano_element(tokens, root_element, 'text')
        for child in root_element.iterchildren():
             tokens.extend(self._parse_conano(child))
        self._parse_conano_element(tokens, root_element, 'tail')
        return tokens


if __name__ == "__main__":
    generic_converter_cli(ConanoDocumentGraph, 'ConanoXML (connectives)')
