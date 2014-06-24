#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann

"""
This module converts a Conano XML file (used by Conano to annotate
connectives) into a networkx-based directed graph
(``DiscourseDocumentGraph``).
"""

import os
import sys
import re
from lxml import etree

from discoursegraphs import DiscourseDocumentGraph, EdgeTypes
from discoursegraphs.readwrite.generic import generic_converter_cli
from discoursegraphs.util import ensure_unicode


REDUCE_WHITESPACE_RE = re.compile(' +')


class ConanoDocumentGraph(DiscourseDocumentGraph):
    """
    represents a Conano XML file as a multidigraph.

    Attributes
    ----------
    ns : str
        the namespace of the graph (default: conano)
    tokens : list of int
        a list of node IDs (int) which represent the tokens in the
        order they occur in the text
    root : str
        name of the document root node ID
        (default: 'conano:root_node')
    """
    def __init__(self, conano_filepath, name=None, namespace='conano',
                 check_validity=True, precedence=False, connected=False):
        """
        reads a Conano XML file and converts it into a multidigraph.

        Parameters
        ----------
        conano_filepath : str
            relative or absolute path to a Conano XML file
        name : str or None
            the name or ID of the graph to be generated. If no name is
            given, the basename of the input file is used.
        namespace : str
            the namespace of the graph (default: conano)
        check_validity : bool
            checks, if the tokenization in the graph matches the one in
            the Conano file (converted to plain text)
        precedence : bool
            add precedence relation edges (root precedes token1, which precedes
            token2 etc.)
        connected : bool
            Make the graph connected, i.e. add an edge from root to each
            token that isn't part of any span. This doesn't do anything, if
            precendence=True.
        """
        # super calls __init__() of base class DiscourseDocumentGraph
        super(DiscourseDocumentGraph, self).__init__()

        self.name = name if name else os.path.basename(conano_filepath)
        self.ns = namespace
        self.root = self.ns+':root_node'
        self.add_node(self.root, layers={self.ns})
        self.tokens = []

        tree = etree.parse(conano_filepath)
        root_element = tree.getroot()
        token_spans = self._parse_conano(root_element)
        self._add_document_structure(token_spans)

        if precedence:
            connected = False
        for i, (token, spans) in enumerate(token_spans):
            self._add_token_to_document(i, token, spans, connected)

        if precedence:
            self.add_precedence_relations()

        if check_validity:
            assert self.is_valid(tree)

    def is_valid(self, tree):
        """
        returns true, iff the order of the tokens in the graph are the
        same as in the Conano file (converted to plain text).
        """
        conano_plaintext = etree.tostring(tree, encoding='utf8', method='text')
        token_str_list = conano_plaintext.split()
        for i, plain_token in enumerate(token_str_list):
            graph_token = self.node[self.tokens[i]][self.ns+':token']
            if ensure_unicode(plain_token) != graph_token:
                sys.stderr.write(
                    "Conano tokenizations don't match: {0} vs. {1} "
                    "({2})".format(plain_token, graph_token))
                return False
        return True

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

        # add a unit, int/ext sub-unit and connective node for each unit found
        for unit_id in unit_ids:
            for node_type in ('unit', 'int', 'ext', 'connective'):
                node_id = '{0}-{1}'.format(node_type, unit_id)
                self.add_node(node_id, layers={self.ns, self.ns+':unit'})

            # edge from root to unit
            # TODO: do we need these edges? do we need those units?
            # having just int-units and ext-units could be enough!
            self.add_edge(self.root, 'unit-{}'.format(unit_id),
                          layers={self.ns, self.ns+':unit'},
                          edge_type=EdgeTypes.spanning_relation)
            # edge from unit to int/ext sub-unit and connective
            for to_node in ('ext', 'int', 'connective'):
                self.add_edge('unit-{}'.format(unit_id),
                              '{0}-{1}'.format(to_node, unit_id),
                              layers={self.ns, self.ns+':unit'},
                              edge_type=EdgeTypes.dominance_relation)

    def _add_token_to_document(self, token_id, token, token_attribs,
                               connected=False):
        """
        TODO: add 'relation' attribute to connective node!
        TODO: how to handle modifiers?

        Parameters
        ----------
        token_id : int
            the index of the token
        token : str or unicode
            the token itself
        token_attribs : dict
            a dict containing all the spans a token belongs to (and
            in case of connectives the relation it is part of)
        connected : bool
            make the graph connected, i.e. add an edge from root to each
            token that isn't part of any span. This doesn't do anything, if
            precendence=True.
        """
        assert isinstance(token_id, int) and token_id >= 0
        token_node_id = 'token-{}'.format(token_id)
        token_str = ensure_unicode(token)
        self.add_node(
            token_node_id,
            layers={self.ns, self.ns+':token'},
            attr_dict={self.ns+':token': token_str, 'label': token_str})

        self.tokens.append(token_node_id)

        if connected:
            if not token_attribs['spans']:  # token isn't part of any span
                self.add_edge(self.root, token_node_id, layers={self.ns},
                              edge_type=EdgeTypes.spanning_relation)

        # add edges from all the spans a token is part of to the token node
        for (span_type, span_id) in token_attribs['spans']:
            if span_type in ('int', 'ext', 'connective', 'modifier'):
                span_node_id = "{0}-{1}".format(span_type, span_id)
                self.add_node(span_node_id, layers={self.ns, self.ns+':unit'})
                self.add_edge(span_node_id,
                              token_node_id, layers={self.ns, self.ns+':unit'},
                              edge_type=EdgeTypes.spanning_relation)
            else:
                raise NotImplementedError(
                    "Can't handle span_type '{}'".format(span_type))

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
                if element.tag != 'discourse':  # discourse is the root element
                    dominating_spans.append(
                        (element.attrib.get('type', element.tag),
                         element.attrib.get('id', '')))

                dominating_spans.extend(
                    [(a.attrib.get('type', a.tag), a.attrib.get('id', ''))
                     for a in element.iterancestors()
                     if a.tag != 'discourse'])

                for token in tokens:
                    if element.tag == 'connective':
                        token_list.append(
                            (token, {'spans': dominating_spans,
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
