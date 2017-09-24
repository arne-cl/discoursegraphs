#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module contains code that is used by multiple importers and/or exporters.
"""

import os
import sys
import argparse

from discoursegraphs.readwrite.dot import write_dot
from discoursegraphs.util import ensure_utf8, ensure_ascii


class XMLElementCountTarget(object):
    '''
    counts all <``self.element_name``> elements in the XML document to be
    parsed. Adapted from Listing 2 on
    http://www.ibm.com/developerworks/library/x-hiperfparse/

    NOTE: The unused arguments `attrib` and `data` are required by
    `etree.XMLParser`.
    '''
    def __init__(self, element_name):
        self.count = 0
        self.element_name = element_name
    def start(self, tag, attrib):
        """handle the start of a <``self.element_name``> element"""
        if tag == self.element_name:
            self.count +=1
    def end(self, tag):
        pass
    def data(self, data):
        pass
    def close(self):
        """return the number of <``self.element_name``> elements"""
        return self.count


def generic_converter_cli(docgraph_class, file_descriptor=''):
    """
    generic command line interface for importers. Will convert the file
    specified on the command line into a dot representation of the
    corresponding DiscourseDocumentGraph and write the output to stdout
    or a file specified on the command line.

    Parameters
    ----------
    docgraph_class : class
        a DiscourseDocumentGraph (or a class derived from it), not an
        instance of it!
    file_descriptor : str
        string descring the input format, e.g. 'TigerXML (syntax)'
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file',
                        help='{} file to be converted'.format(file_descriptor))
    parser.add_argument('output_file', nargs='?', default=sys.stdout)
    args = parser.parse_args(sys.argv[1:])

    assert os.path.isfile(args.input_file), \
        "'{}' isn't a file".format(args.input_file)
    docgraph = docgraph_class(args.input_file)
    write_dot(docgraph, args.output_file)


def layerset2list(discoursegraph):
    """
    typecasts all `layers` sets to lists to make the graph
    exportable (e.g. into the `geoff` format).

    Parameters
    ----------
    discoursegraph : DiscourseDocumentGraph
    """
    for node_id in discoursegraph:
        discoursegraph.node[node_id]['layers'] = \
            list(discoursegraph.node[node_id]['layers'])
    for (from_id, to_id) in discoursegraph.edges_iter():
        # there might be multiple edges between 2 nodes
        edge_dict = discoursegraph.edge[from_id][to_id]
        for edge_id in edge_dict:
            edge_dict[edge_id]['layers'] = \
                list(edge_dict[edge_id]['layers'])


def layerset2str(discoursegraph):
    """
    typecasts all `layers` from sets of strings into a single string to make
    the graph exportable (e.g. into the `gexf` and `graphml` formats).

    Parameters
    ----------
    discoursegraph : DiscourseDocumentGraph
    """
    for node_id in discoursegraph:
        discoursegraph.node[node_id]['layers'] = \
            str(discoursegraph.node[node_id]['layers'])
    for (from_id, to_id) in discoursegraph.edges_iter():
        # there might be multiple edges between 2 nodes
        edge_dict = discoursegraph.edge[from_id][to_id]
        for edge_id in edge_dict:
            edge_dict[edge_id]['layers'] = \
                str(edge_dict[edge_id]['layers'])


def attriblist2str(discoursegraph):
    """
    converts all node/edge attributes whose values are lists into string
    values (e.g. to export them into the `gexf` and `graphml` formats).

    WARNING: This function iterates over all nodes and edges! You can speed up
    conversion by writing a custom function that only fixes those attributes
    that have lists (of strings) as values.

    Parameters
    ----------
    discoursegraph : DiscourseDocumentGraph
    """
    for node_id in discoursegraph:
        node_dict = discoursegraph.node[node_id]
        for attrib in node_dict:
            if isinstance(node_dict[attrib], list):
                node_dict[attrib] = str(node_dict[attrib])
    for (from_id, to_id) in discoursegraph.edges_iter():
        # there might be multiple edges between 2 nodes
        edge_dict = discoursegraph.edge[from_id][to_id]
        for edge_id in edge_dict:
            for attrib in edge_dict[edge_id]:
                if isinstance(edge_dict[edge_id][attrib], list):
                    edge_dict[edge_id][attrib] \
                        = str(edge_dict[edge_id][attrib])


def remove_root_metadata(docgraph):
    """
    removes the ``metadata`` attribute of the root node of a document graph.
    this is necessary for some exporters, as the attribute may contain
    (nested) dictionaries.
    """
    docgraph.node[docgraph.root].pop('metadata', None)
    # delete metadata from the generic root node (which probably only exists
    # when we merge graphs on the command line, cf. issue #89
    if 'discoursegraph:root_node' in docgraph.node:
        docgraph.node['discoursegraph:root_node'].pop('metadata', None)
    # delete the metadata from all former root nodes which have been merged
    # into this graph
    if hasattr(docgraph, 'merged_rootnodes'):
        for merged_rootnode in docgraph.merged_rootnodes:
            try:  # some of these nodes may not exist any longer
                docgraph.node[merged_rootnode].pop('metadata', None)
            except KeyError as e:
                pass


def convert_spanstring(span_string):
    """
    converts a span of tokens (str, e.g. 'word_88..word_91')
    into a list of token IDs (e.g. ['word_88', 'word_89', 'word_90', 'word_91']

    Note: Please don't use this function directly, use spanstring2tokens()
    instead, which checks for non-existing tokens!

    Examples
    --------
    >>> convert_spanstring('word_1')
    ['word_1']
    >>> convert_spanstring('word_2,word_3')
    ['word_2', 'word_3']
    >>> convert_spanstring('word_7..word_11')
    ['word_7', 'word_8', 'word_9', 'word_10', 'word_11']
    >>> convert_spanstring('word_2,word_3,word_7..word_9')
    ['word_2', 'word_3', 'word_7', 'word_8', 'word_9']
    >>> convert_spanstring('word_7..word_9,word_15,word_17..word_19')
    ['word_7', 'word_8', 'word_9', 'word_15', 'word_17', 'word_18', 'word_19']
    """
    prefix_err = "All tokens must share the same prefix: {0} vs. {1}"

    tokens = []
    if not span_string:
        return tokens

    spans = span_string.split(',')
    for span in spans:
        span_elements = span.split('..')
        if len(span_elements) == 1:
            tokens.append(span_elements[0])
        elif len(span_elements) == 2:
            start, end = span_elements
            start_prefix, start_id_str = start.split('_')
            end_prefix, end_id_str = end.split('_')
            assert start_prefix == end_prefix, prefix_err.format(
                start_prefix, end_prefix)
            tokens.extend("{0}_{1}".format(start_prefix, token_id)
                          for token_id in range(int(start_id_str),
                                                int(end_id_str)+1))

        else:
            raise ValueError("Can't parse span '{}'".format(span_string))

    first_prefix = tokens[0].split('_')[0]
    for token in tokens:
        token_parts = token.split('_')
        assert len(token_parts) == 2, \
            "All token IDs must use the format prefix + '_' + number"
        assert token_parts[0] == first_prefix, prefix_err.format(
            token_parts[0], first_prefix)
    return tokens
