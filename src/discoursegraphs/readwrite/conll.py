#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann

"""
The ``conll`` module converts a CoNLL 2009/2010 files into a
``DiscourseDocumentGraph`` and is also able to convert document graphs
into a CoNLL 2009 file.

Current state
=============

CoNLL import
------------

The resulting document graph will contain a node for each token (with CoNLL
columns added as features) with dominance edges (representing dependency
relations between them). The document and sentence root are also represented
and connected via edges.

CoNLL 2009 import
~~~~~~~~~~~~~~~~~

Only the first 14 columns will be parsed into token features, i.e. we're
ignoring all APREDs (columns that represent argument dependencies and labels of
PRED).

CoNLL 2009 export
-----------------

Currently, most annotation levels are ignored. Only tokens, sentences
are coreferences are exported!


TODOs
=====

- write a generic_merging_cli() and a generic write_format() function.
- coordinate this with issue #43 (add write_formatname function for each output
  format)
"""

import os
import sys
import codecs
from collections import defaultdict, namedtuple

from discoursegraphs import (DiscourseDocumentGraph, get_pointing_chains,
                             get_span, select_nodes_by_layer, EdgeTypes)
from discoursegraphs.util import ensure_utf8, create_dir


CONLL2009_COLUMNS = ('word_id', 'token', 'lemma', 'plemma', 'pos', 'ppos',
                     'feat', 'pfeat', 'head', 'phead', 'deprel', 'pdeprel',
                     'fillpred', 'pred')
CONLL2010_COLUMNS = ('word_id', 'token', 'lemma', 'plemma', 'pos', 'ppos',
                     'feat', 'pfeat', 'head', 'phead', 'deprel', 'pdeprel',
                     'ne', 'pne', 'pred', 'ppred', 'coref')

Conll2009Word = namedtuple('Conll2009Word', CONLL2009_COLUMNS)
Conll2010Word = namedtuple('Conll2010Word', CONLL2010_COLUMNS)


class ConllDocumentGraph(DiscourseDocumentGraph):
    """
    This class converts a CoNLL file (CoNLL2009 or CoNLL2010) into a
    DiscourseDocumentGraph.

    Attributes
    ----------
    ns : str
        the namespace of the graph (default: conll)
    tokens : list of int
        a list of node IDs (int) which represent the tokens in the
        order they occur in the text
    root : str
        name of the document root node ID
        (default: 'conll:root_node')
    """
    def __init__(self, conll_filepath, conll_format='2010', name=None,
                 namespace='conll', precedence=False):
        """
        initializes a multidigraph and parses a CoNLL file into it.

        Parameters
        ----------
        conll_filepath : str
            relative or absolute path to a DeCour XML file
        name : str or None
            the name or ID of the graph to be generated. If no name is
            given, the basename of the input file is used.
        namespace : str
            the namespace of the graph (default: conll)
        precedence : bool
            add precedence relation edges (root precedes token1, which precedes
            token2 etc.)
        """
        # super calls __init__() of base class DiscourseDocumentGraph
        super(ConllDocumentGraph, self).__init__()

        self.name = name if name else os.path.basename(conll_filepath)
        self.ns = namespace
        self.root = self.ns+':root_node'
        self.add_node(self.root, layers={self.ns})
        self.tokens = []
        self.sentences = []

        self._parse_conll(conll_filepath, conll_format=conll_format)
        if precedence:
            self._add_precedence_relations()

    def _parse_conll(self, conll_filepath, conll_format='2010'):
        """
        parses a CoNLL2009/2010 file into a multidigraph.
        """
        assert conll_format in ('2009', '2010'), \
            "We only support CoNLL2009 and CoNLL2010 format."
        if conll_format == '2009':
            word_class = Conll2009Word
        else:
            word_class = Conll2010Word

        with codecs.open(conll_filepath, 'r', 'utf-8') as conll_file:
            conll_str = conll_file.read()
            sentences = conll_str.strip().split("\n\n")
            for i, sentence in enumerate(sentences, 1):
                sent_id = self.__add_sentence_root_node(i)
                for word in self.__parse_conll_sentence(sentence, word_class):
                    token_id = self.__add_token(word, sent_id)
                    self.__add_dependency(word, sent_id)

    def __parse_conll_sentence(self, sentence, word_class,
                               conll_format='2010'):
        """
        """
        for line in sentence.split("\n"):
            if line.startswith('#'):
                continue  # don't yield anything for comment lines
            try:
                # create a named tuple containing all features of the word
                if conll_format == '2010':
                    yield word_class._make(line.split("\t"))
                else:  # CoNLL2009
                    # we ignore APREDs (columns that represent argument
                    # dependencies and labels of PRED)
                    yield word_class._make(line.split("\t")[:14])
            except TypeError as e:
                error_msg = ("Is input really in CoNLL{} format?\n"
                    "word features: {}\n"
                    "{}".format(conll_format, line.split('\t'),e))
                raise TypeError(error_msg.format(e))

    def __add_sentence_root_node(self, sent_number):
        """
        adds the root node of a sentence to the graph and the list of sentences
        (``self.sentences``).

        Parameters
        ----------
        sent_number : int
            the index of the sentence within the document

        Results
        -------
        sent_id : str
            the ID of the sentence
        """
        sent_id = 's{}'.format(sent_number)
        self.add_node(sent_id, layers={self.ns, self.ns+':sentence'})
        self.add_edge(self.root, sent_id,
                      layers={self.ns, self.ns+':sentence'},
                      edge_type=EdgeTypes.dominance_relation)
        self.sentences.append(sent_id)
        return sent_id

    def __add_token(self, word, sent_id):
        """
        adds a token to the document graph (with all the features given
        in the columns of the CoNLL file).

        Parameters
        ----------
        word : Conll2009Word or Conll2010Word
            a namedtuple representing all the information stored in a CoNLL
            file line (token, lemma, pos, dependencies etc.)
        sent_id : str
            the ID of the sentence this word/token belongs to

        Returns
        -------
        token_id : str
            the ID of the token just created
        """
        token_id = '{}_t{}'.format(sent_id, word.word_id)
        self.add_node(token_id,
                      layers={self.ns, self.ns+':token'},
                      attr_dict=word._asdict(),
                      label=word.token)
        self.tokens.append(token_id)
        return token_id

    def __add_dependency(self, word_instance, sent_id):
        """
        adds an ingoing dependency relation from the projected head of a token
        to the token itself.
        """
        # 'phead': projected head
        if word_instance.phead == '0':  # word represents the sentence root
            source_id = sent_id
        else:
            source_id = '{}_t{}'.format(sent_id, word_instance.phead)
            # TODO: fix issue #39, so we don't have to add nodes explicitly
            if source_id not in self.node:
                self.add_node(source_id, layers={self.ns})

        target_id = '{}_t{}'.format(sent_id, word_instance.word_id)
        # 'pdeprel': projected dependency relation
        try:
            self.add_edge(source_id, target_id,
                          layers={self.ns, self.ns+':dependency'},
                          relation_type=word_instance.pdeprel,
                          label=word_instance.pdeprel,
                          edge_type=EdgeTypes.dominance_relation)
        except AssertionError:
            print "source: {}, target: {}".format(source_id, target_id)


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
        self.tok2markables, self.markable2toks, self.markable2chains = \
            self.__build_markable_token_mapper()

    def __build_markable_token_mapper(self):
        """
        Creates mappings from tokens to the markable spans they belong to
        and the coreference chains these markables are part of.

        Returns
        -------
        tok2markables : dict (str -> set of str)
            Maps from a token (node ID) to all the markables (node IDs)
            it is part of.
        markable2toks : dict (str -> list of str)
            Maps from a markable (node ID) to all the tokens (node IDs)
            that belong to it.
        markable2chains : dict (str -> list of int)
            Maps from a markable (node ID) to all the chains (chain ID) it
            belongs to.
        """
        tok2markables = defaultdict(set)
        markable2toks = defaultdict(list)
        markable2chains = defaultdict(list)

        coreference_chains = get_pointing_chains(self.docgraph)
        for chain_id, chain in enumerate(coreference_chains):
            for markable_node_id in chain:
                markable2chains[markable_node_id].append(chain_id)

        # ID of the first singleton (if there are any)
        singleton_id = len(coreference_chains)

        # markable2toks/tok2markables shall contains all markables, not only
        # those which are part of a coreference chain
        for markable_node_id in select_nodes_by_layer(self.docgraph,
                                                      'mmax:markable'):
            span = get_span(self.docgraph, markable_node_id)
            markable2toks[markable_node_id] = span
            for token_node_id in span:
                tok2markables[token_node_id].add(markable_node_id)

            # singletons each represent their own chain (with only one element)
            if markable_node_id not in markable2chains:
                markable2chains[markable_node_id] = [singleton_id]
                singleton_id += 1

        return tok2markables, markable2toks, markable2chains

    def __str__(self):
        """
        returns a string representation of the CoNLL 2009 file.
        """
        dg = self.docgraph
        conll_str = '#begin document (__); __\n'
        for sentence_id in dg.sentences:
            # every sentence in a CoNLL file starts with index 1!
            for i, tok_id in enumerate(dg.node[sentence_id]['tokens'], 1):
                if tok_id in self.tok2markables:
                    coreferences = []
                    markable_ids = self.tok2markables[tok_id]
                    for markable_id in markable_ids:
                            # a markable can be part of multiple chains,
                            # at least it's legal in MMAX2
                            for chain_id in self.markable2chains[markable_id]:
                                coref_str = self.__gen_coref_str(tok_id,
                                                                 markable_id,
                                                                 chain_id)
                                coreferences.append(coref_str)
                    coref_column = '\t{}'.format('|'.join(coreferences))

                else:
                    coref_column = '\t_'

                word = dg.get_token(tok_id)
                conll_str += '{0}\t{1}{2}{3}\n'.format(i, ensure_utf8(word),
                                                       '\t_' * 12,
                                                       coref_column)
            conll_str += '\n'
        conll_str += '#end document'
        return conll_str

    def __gen_coref_str(self, token_id, markable_id, target_id):
        """
        generates the string that represents the markables and coreference
        chains that a token is part of.

        Parameters
        ----------
        token_id : str
            the node ID of the token
        markable_id : str
            the node ID of the markable span
        target_id : int
            the ID of the target (either a singleton markable or a coreference
            chain)

        Returns
        -------
        coref_str : str
            a string representing the token's position in a markable span
            and its membership in one (or more) coreference chains
        """
        span = self.markable2toks[markable_id]
        coref_str = str(target_id)
        if span.index(token_id) == 0:
            # token is the first element of a markable span
            coref_str = '(' + coref_str
        if span.index(token_id) == len(span)-1:
            # token is the last element of a markable span
            coref_str += ')'
        return coref_str

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
