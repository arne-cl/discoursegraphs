#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import sys
import os
import re
from itertools import chain
from networkx import MultiDiGraph, write_gpickle

# The words 'das' and 'es were annotatated in the Potsdam Commentary
# Corpus (PCC). Annotation options: '/n' (nominal), '/a' (abstract),
# '/r' (relative pronoun) or '/p' (pleonastic). If the annotator was
# uncertain, the annotation is marked with a question mark.
#
# Examples: 'Das/a', 'es/p?'
ANNOTATED_ANAPHORA_REGEX = re.compile('(?P<token>([Dd]a|[Ee])s)/(?P<annotation>[anpr])(?P<uncertain>\??)')

ANNOTATION_TYPES = {'n': 'nominal',
                    'a': 'abstract',
                    'r': 'relative',
                    'p': 'pleonastic'}

class AnaphoraDocumentGraph(MultiDiGraph):
    """
    represents a text in which abstract anaphora were annotated
    as a graph.

    Attributes
    ----------
    tokens : list of int
        a list of node IDs (int) which represent the tokens in the
        order they occur in the text
    root_node_name : str
        name of the document root node ID
        (default: 'anaphoricity:root_node')
    """
    def __init__(self, anaphora_filepath, name=None):
        """
        Reads an abstract anaphora annotation file, creates a directed
        graph and adds a node for each token, as well as an edge from
        the root node to each token.
        If a token is annotated, it will have an attribute 'annotation',
        which maps to a dict with the keys 'anaphoricity' (str) and
        'certainty' (float).
        
        'anaphoricity' is one of the following: 'abstract', 'nominal', 
        'pleonastic' or 'relative'.
        
        Parameters
        ----------
        anaphora_filepath : str
            relative or absolute path to an anaphora annotation file.
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
        """
        # super calls __init__() of base class MultiDiGraph
        super(AnaphoraDocumentGraph, self).__init__()
        self.name = os.path.basename(anaphora_filepath)
        self.root_node_name = 'anaphoricity:root_node'
        self.add_node(self.root_node_name, layers={'anaphoricity'})
        self.tokens = []

        with open(anaphora_filepath, 'r') as anno_file:
            annotated_lines = anno_file.readlines()
            tokens = list(chain.from_iterable(line.split()
                                        for line in annotated_lines))
            for i, token in enumerate(tokens):
                self.__add_token_to_document(token, i)
                self.tokens.append(i)

    def __add_token_to_document(self, token, token_id):
        """
        adds a token to the document graph as a node with the given ID.

        Parameters
        ----------
        token : str
            the token to be added to the document graph
        token_id : int
            the node ID of the token to be added, which must not yet
            exist in the document graph
        """
        regex_match = ANNOTATED_ANAPHORA_REGEX.search(token)
        if regex_match: # token is annotated
            unannotated_token = regex_match.group('token')
            annotation = regex_match.group('annotation')
            certainty = 1.0 if not regex_match.group('uncertain') else 0.5
            self.add_node(token_id, attr_dict={
                'anaphoricity:annotation': ANNOTATION_TYPES[annotation], 
                'anaphoricity:certainty': certainty}, 
                token=unannotated_token,
                layers={'anaphoricity', 'anaphoricity:token'})
        else: # token is not annotated
            self.add_node(token_id, token=token,
                layers={'anaphoricity', 'anaphoricity:token'})
        self.add_edge(self.root_node_name, token_id,
            layers={'anaphoricity', 'anaphoricity:token'})


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.stderr.write('Usage: {0} anaphoricity_input_file networkx_pickle_output_file\n'.format(sys.argv[0]))
        sys.exit(1)
    else:
        anaphora_filepath = sys.argv[1]
        pickle_filepath = sys.argv[2]
        assert os.path.isfile(anaphora_filepath)
        anaphora_docgraph = AnaphoraDocumentGraph(anaphora_filepath)
        write_gpickle(anaphora_docgraph, pickle_filepath)

