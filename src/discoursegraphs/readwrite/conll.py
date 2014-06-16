#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann

"""
The ``conll`` module converts a ``DiscourseDocumentGraph`` (possibly
containing multiple annotation layers) into an CoNLL 2009 tab-separated file.

Currently, most annotation levels are ignored. Only tokens, sentences
are coreferences are exported!

TODO: write a generic_merging_cli() and a generic write_format() function.
Coordinate this with
    issue #43: add write_formatname function for each output format
"""

import os
import sys
from collections import defaultdict

from discoursegraphs import get_pointing_chains, get_span
from discoursegraphs.util import create_dir, ensure_utf8


class Conll2009File(object):
    """
    This class converts a DiscourseDocumentGraph into a CoNLL 2009 file.
    """
    def __init__(self, docgraph):
        """
        Parameters
        ----------
        docgraph : DiscourseDocumentGraph
            the document graph to be converted
        """
        self.docgraph = docgraph
        self.tok2markable, self.markable2toks = \
            self.__build_markable_token_mapper()

    def __build_markable_token_mapper(self):
        """
        Returns
        -------
        tok2markable : dict (str -> set of str)
            maps from a token (node ID) to all the markables (node IDs)
            it is part of
        markable2toks : dict (str -> list of str)
            maps from a markable (node ID) to all the tokens (node IDs)
            that belong to it
        """
        tok2markable = defaultdict(set)
        markable2toks = defaultdict(list)

        for chain in get_pointing_chains(self.docgraph):
            for markable in chain:
                span = get_span(self.docgraph, markable)
                markable2toks[markable] = span
                for token_node_id in span:
                    tok2markable[token_node_id].add(markable)
        return tok2markable, markable2toks

    def __str__(self):
        """
        returns the generated CoNLL 2009 file as a string.
        """
        docgraph = self.docgraph
        conll_str = '#begin document (__); __\n'
        for sentence_id in docgraph.sentences:
            # every sentence in a CoNLL file starts with index 1!
            for i, token_id in enumerate(docgraph.node[sentence_id]['tokens'], 1):
                if token_id in self.tok2markable:
                    coreferences = []
                    markable_ids = self.tok2markable[token_id]
                    for markable_id in markable_ids:
                        span = self.markable2toks[markable_id]
                        coref_str = markable_id
                        if span.index(token_id) == 0:
                            # token is the first element of a markable span
                            coref_str = '(' + coref_str
                        if  span.index(token_id) == len(span)-1:
                            # token is the last element of a markable span
                            coref_str += ')'
                        coreferences.append(coref_str)
                    coref_column = '\t{}'.format('|'.join(coreferences))

                else:
                    coref_column = '\t_'

                word = docgraph.get_token(token_id)
                conll_str += '{0}\t{1}{2}{3}\n'.format(i, ensure_utf8(word),
                                                       '\t_' * 12,
                                                       coref_column)
            conll_str += '\n'
        conll_str += '#end document'
        return conll_str

    def write(self, output_filepath):
        """
        Parameters
        ----------
        output_filepath : str
            relative or absolute path to the CoNLL 2009 file to be created
        """
        with open(output_filepath, 'w') as out_file:
            out_file.write(self.__str__())


def write_conll(docgraph, output_file):
    """
    converts a DiscourseDocumentGraph into a tab-separated CoNLL 2009 file and
    writes it to the given file (or file path).
    """
    conll_file = Conll2009File(docgraph)
    assert isinstance(output_file, (str, file))
    if isinstance(output_file, str):
        path_to_file = os.path.dirname(output_file)
        if not os.path.isdir(path_to_file):
            create_dir(path_to_file)
        conll_file.write(output_file)
    else:  # output_file is a file object
        output_file.write(conll_file.__str__())


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
    write_conll(docgraph, args.output_file)


