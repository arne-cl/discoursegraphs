#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
The ``anaphoricity`` module parses Christian Dittrich's anaphoricity
annotation ad-hoc format into a document graph.
"""

import os
import re
from itertools import chain
import codecs

import discoursegraphs as dg
from discoursegraphs import DiscourseDocumentGraph
from discoursegraphs.util import ensure_unicode
from discoursegraphs.readwrite.generic import generic_converter_cli

# The words 'das' and 'es were annotatated in the Potsdam Commentary
# Corpus (PCC). Annotation options: '/n' (nominal), '/a' (abstract),
# '/r' (relative pronoun) or '/p' (pleonastic). If the annotator was
# uncertain, the annotation is marked with a question mark.
#
# Examples: 'Das/a', 'es/p?'
ANNOTATED_ANAPHORA_REGEX = re.compile(
    '(?P<token>([Dd]a|[Ee])s)/(?P<annotation>[anpr])(?P<uncertain>\??)')

ANNOTATION_TYPES = {'n': 'nominal',
                    'a': 'abstract',
                    'r': 'relative',
                    'p': 'pleonastic'}

ANNOTATIONS = {val: key for key, val in ANNOTATION_TYPES.items()}

class AnaphoraDocumentGraph(DiscourseDocumentGraph):

    """
    represents a text in which abstract anaphora were annotated
    as a graph.

    Attributes
    ----------
    ns : str
        the namespace of the graph (default: anaphoricity)
    tokens : list of int
        a list of node IDs (int) which represent the tokens in the
        order they occur in the text
    root : str
        name of the document root node ID
        (default: self.ns+':root_node')
    """

    def __init__(self, anaphora_filepath=None, name=None,
                 namespace='anaphoricity', connected=False):
        """
        Reads an abstract anaphora annotation file, creates a directed
        graph and adds a node for each token, as well as an edge from
        the root node to each token.
        If a token is annotated, it will have a 'namespace:annotation'
        attribute, which maps to a dict with the keys 'anaphoricity' (str)
        and 'certainty' (float). Annotated tokens are also part of the
        'namespace:annotated' layer.

        'anaphoricity' is one of the following: 'abstract', 'nominal',
        'pleonastic' or 'relative'.

        Parameters
        ----------
        anaphora_filepath : str or None
            relative or absolute path to an anaphora annotation file.
            If not set, an empty graph will be generated.
            The format of the file was created ad-hoc by one of our
            students for his diploma thesis. It consists of tokenized
            plain text (one sentence per line with spaces between
            tokens).
            A token is annotated by appending '/' and one of the letters
            'a' (abstract), 'n' (nominal), 'p' (pleonastic),
            'r' (relative pronoun) and optionally a question mark to
            signal uncertainty.
        name : str or None
            the name or ID of the graph to be generated. If no name is
            given, the basename of the input file is used.
        namespace : str
            the namespace of the graph (default: anaphoricity)
        connected : bool
            Make the graph connected, i.e. add an edge from root to each
            token (default: False).
        """
        # super calls __init__() of base class DiscourseDocumentGraph
        super(AnaphoraDocumentGraph, self).__init__(namespace='anaphoricity')
        self.name = name if name else os.path.basename(anaphora_filepath)
        self.ns = namespace
        self.root = self.ns+':root_node'
        self.tokens = []

        if anaphora_filepath:
            self.add_node(self.root, layers={self.ns})
            with open(anaphora_filepath, 'r') as anno_file:
                annotated_lines = anno_file.readlines()
                tokens = list(chain.from_iterable(line.split()
                                                  for line in annotated_lines))
                for i, token in enumerate(tokens):
                    self.__add_token_to_document(token, i, connected)
                    self.tokens.append(i)

    def __add_token_to_document(self, token, token_id, connected):
        """
        adds a token to the document graph as a node with the given ID.

        Parameters
        ----------
        token : str
            the token to be added to the document graph
        token_id : int
            the node ID of the token to be added, which must not yet
            exist in the document graph
        connected : bool
            Make the graph connected, i.e. add an edge from root this token.
        """
        regex_match = ANNOTATED_ANAPHORA_REGEX.search(token)
        if regex_match:  # token is annotated
            unannotated_token = regex_match.group('token')
            unicode_token = ensure_unicode(unannotated_token)
            annotation = regex_match.group('annotation')
            anno_type = ANNOTATION_TYPES[annotation]
            certainty = "1.0" if not regex_match.group('uncertain') else "0.5"
            self.add_node(
                token_id,
                layers={self.ns, self.ns+':token', self.ns+':annotated'},
                attr_dict={
                    self.ns+':annotation': anno_type,
                    self.ns+':certainty': certainty,
                    self.ns+':token': unicode_token,
                    'label': u"{0}_{1}".format(unicode_token, anno_type)})
        else:  # token is not annotated
            self.add_node(
                token_id,
                layers={self.ns, self.ns+':token'},
                attr_dict={self.ns+':token': ensure_unicode(token),
                           'label': ensure_unicode(token)})

        if connected:
            self.add_edge(self.root, token_id,
                          layers={self.ns, self.ns+':token'})


def gen_anaphoricity_str(docgraph, anaphora='es'):
    assert anaphora in ('das', 'es')
    ret_str = u''
    annotated_token_ids = [tok_id for tok_id in dg.select_nodes_by_layer(docgraph, docgraph.ns+':annotated')
                           if docgraph.get_token(tok_id).lower() == anaphora]
    for token_id in docgraph.tokens:
        if token_id in annotated_token_ids:
            certainty_str = '' if docgraph.ns+':certainty' == '1.0' else '?'
            ret_str += u'{0}/{1}{2} '.format(
                docgraph.get_token(token_id),
                ANNOTATIONS[docgraph.node[token_id][docgraph.ns+':annotation']],
                certainty_str)
        else:
            ret_str += u'{} '.format(docgraph.get_token(token_id))
    return ret_str


def write_anaphoricity(docgraph, output_path, anaphora='das'):
    outpath, _fname = os.path.split(output_path)
    dg.util.create_dir(outpath)
    with codecs.open(output_path, 'w', encoding='utf-8') as outfile:
        outfile.write(gen_anaphoricity_str(docgraph, anaphora=anaphora))


# pseudo-function to create a document graph from an anaphoricity file
read_anaphoricity = AnaphoraDocumentGraph


if __name__ == '__main__':
    generic_converter_cli(AnaphoraDocumentGraph,
                          file_descriptor='anaphoricity')
