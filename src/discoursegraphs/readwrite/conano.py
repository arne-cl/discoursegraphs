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

from discoursegraphs import (DiscourseDocumentGraph, EdgeTypes, get_span,
                             select_nodes_by_layer)
from discoursegraphs.readwrite.generic import generic_converter_cli
from discoursegraphs.util import (ensure_unicode, natural_sort_key,
                                  sanitize_string)


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
                 check_validity=True, precedence=False, tokenize=True):
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
        tokenize : bool
            If True, the text will be tokenized and each int(ernal) and
            ext(ernal) unit will have outgoing edges to each of the tokens it
            spans. If False, each int/ext unit node will be labeled with the
            text it spans (this is only useful for debugging).
        """
        # super calls __init__() of base class DiscourseDocumentGraph
        super(ConanoDocumentGraph, self).__init__(namespace=namespace)

        self.name = name if name else os.path.basename(conano_filepath)
        self.ns = namespace
        self.tokenize = tokenize
        if self.tokenize:
            self.tokens = []
            self.token_count = 1

        tree = etree.parse(conano_filepath)
        root_element = tree.getroot()  # <discourse>
        self._add_element(root_element, self.root)

        if precedence:
            self.add_precedence_relations()

        if check_validity and self.tokenize:
            assert self.is_valid(tree)

    def _add_element(self, element, parent_node):
        """
        add an element (i.e. a unit/connective/discourse or modifier)
        to the docgraph.
        """
        if element.tag == 'unit':
            element_node_id = element.attrib['id']+':'+element.attrib['type']
            node_layers = {self.ns, self.ns+':unit', self.ns+':'+element.attrib['type']}
        elif element.tag == 'connective':
            element_node_id = element.attrib['id']+':connective'
            node_layers = {self.ns, self.ns+':connective'}
        elif element.tag == 'discourse':
            element_node_id = 'discourse'
            node_layers = {self.ns}
        else:  # <modifier>
            element_node_id = element.getparent().attrib['id']+':'+element.tag
            node_layers = {self.ns, self.ns+':modifier'}

        self.add_node(element_node_id, layers=node_layers)
        self.add_edge(parent_node, element_node_id, layers={self.ns},
                      edge_type=EdgeTypes.dominance_relation)

        if element.text:
            if self.tokenize:
                for token in element.text.split():
                    self._add_token(token, element_node_id)
            else:
                element_text = sanitize_string(element.text)
                self.node[element_node_id].update(
                    {'label': u"{0}: {1}...".format(element_node_id,
                                                   element_text[:20])})


        for child_element in element.iterchildren():
            self._add_element(child_element, element_node_id)

        if element.tail:  # tokens _after_ the </element> closes
            if self.tokenize:
                for token in element.tail.split():
                    self._add_token(token, parent_node)
            else:
                tail_text = sanitize_string(element.tail)
                self.node[parent_node].update(
                    {'label': u"{0}: {1}...".format(parent_node,
                                                    tail_text[:20])})


    def _add_token(self, token, parent_node='root'):
        """add a token to this docgraph"""
        if parent_node == 'root':
            parent_node = self.root

        token_node_id = 'token:{}'.format(self.token_count)
        self.add_node(token_node_id, layers={self.ns, self.ns+':token'},
                      attr_dict={self.ns+':token': token})
        self.add_edge(parent_node, token_node_id,
                      layers={self.ns},
                      edge_type=EdgeTypes.spanning_relation)
        self.tokens.append(token_node_id)
        self.token_count += 1

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


def get_conano_units(docgraph, data=True, conano_namespace='conano'):
    """
    yield all Conano units that occur in the given document graph,
    sorted by their unit ID. int(ernal) and ext(ernal) count as distinct units.

    Parameters
    ----------
    docgraph : DiscourseDocumentGraph
        a document graph which contains Conano annotations
    data : bool
        If True (default), yields (node ID, list of tokens)
        tuples. If False, yields just unit IDs.
    conano_namespace : str
        The namespace that the Conano annotations use (default: conano)

    Yields
    ------
    relations : str or (str, str, list of str) tuples
        If data=False, this will just yield node IDs of the nodes that
        directly dominate an RST relation. If data=True, this yields
        tuples of the form: (node ID, relation name, list of tokens that this
        relation spans).
    """
    for unit_id in sorted(select_nodes_by_layer(docgraph, conano_namespace+':unit'),
                          key=natural_sort_key):
        yield (unit_id, get_span(docgraph, unit_id)) if data else (unit_id)


def get_connective(docgraph, unit_id):
    """
    returns the lowercased string of the connective used in the given Conano unit.
    """
    unit_index, _unit_type = unit_id.split(':')
    connective_id = unit_index+':connective'
    return ' '.join(docgraph.get_token(tok_id).lower()
                    for tok_id in get_span(docgraph, connective_id))


# pseudo-function to create a document graph from a ConanoXML file
read_conano = ConanoDocumentGraph


if __name__ == "__main__":
    generic_converter_cli(ConanoDocumentGraph, 'ConanoXML (connectives)')
