#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module converts an Penn Treebank *.mrg file into a networkx-based
directed graph (``DiscourseDocumentGraph``).
"""

import os
import tempfile

import nltk # version 3.x is needed here (.labels() vs. .node)

import discoursegraphs as dg


PTB_BRACKET_ESCAPE = {'(': r'-LRB-',
                       ')': r'-RRB-',
                       '[': r'-LSB-',
                       ']': r'-RSB-',
                       '{': r'-LCB-',
                       '}': r'-RCB-'}
PTB_BRACKET_UNESCAPE = {val:key for (key, val)
                                in PTB_BRACKET_ESCAPE.items()}

class PTBDocumentGraph(dg.DiscourseDocumentGraph):
    """
    A directed graph with multiple edges (based on a networkx
    MultiDiGraph) that represents the syntax structure of a
    document.

    Attributes
    ----------
    name : str
        name, ID of the document or file name of the input file
    ns : str
        the namespace of the document (default: ptb)
    root : str
        name of the document root node ID
    tokens : list of str
        sorted list of all token node IDs contained in this document graph
    """
    def __init__(self, ptb_filepath=None, name=None, namespace='ptb',
                 precedence=False, limit=None, ignore_traces=True):
        """
        Creates an PTBDocumentGraph from a Penn Treebank *.mrg file and adds metadata
        to it.

        Parameters
        ----------
        ptb_filepath : str or None
            absolute or relative path to the Penn Treebank *.mrg file to be
            parsed. If no path is given, return an empty PTBDocumentGraph.
        name : str or None
            the name or ID of the graph to be generated. If no name is
            given, the basename of the input file is used.
        namespace : str
            the namespace of the document (default: ptb)
        precedence : bool
            add precedence relation edges (root precedes token1, which precedes
            token2 etc.)
        limit : int or None
            only parse the first n sentences of the input file into the
            document graph
        """
        # super calls __init__() of base class DiscourseDocumentGraph
        super(PTBDocumentGraph, self).__init__()

        if 'discoursegraph:root_node' in self:
            self.remove_node('discoursegraph:root_node')

        self.ns = namespace
        if not ptb_filepath:
            return # create empty document graph

        self.name = name if name else os.path.basename(ptb_filepath)
        self.root = 0
        self.add_node(self.root, layers={self.ns}, label=self.ns+':root_node')
            
        self.sentences = []
        self.tokens = []

        self._node_id = 1

        ptb_path, ptb_filename = os.path.split(ptb_filepath)
        self._parsed_doc = nltk.corpus.BracketParseCorpusReader(ptb_path, [ptb_filename])
        parsed_sents_iter = self._parsed_doc.parsed_sents()
        
        if limit:
            for sentence in parsed_sents_iter[:limit]:
                self._add_sentence(sentence, ignore_traces=ignore_traces)
        else: # parse all sentences
            for sentence in parsed_sents_iter:
                self._add_sentence(sentence, ignore_traces=ignore_traces)

        if precedence:
            self.add_precedence_relations()

    @classmethod
    def fromstring(cls, ptb_string, namespace='ptb', precedence=False,
                  ignore_traces=True):
        """create a PTBDocumentGraph from a string containing PTB parses."""
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(ptb_string)
        temp.close()
        ptb_docgraph = cls(ptb_filepath=temp.name, namespace=namespace,
                           precedence=precedence, ignore_traces=ignore_traces)
        os.unlink(temp.name)
        return ptb_docgraph

    def _add_sentence(self, sentence, ignore_traces=True):
        """
        add a sentence from the input document to the document graph.

        Parameters
        ----------
        sentence : nltk.tree.Tree
            a sentence represented by a Tree instance
        """
        self.sentences.append(self._node_id)
        # add edge from document root to sentence root
        self.add_edge(self.root, self._node_id, edge_type=dg.EdgeTypes.dominance_relation)
        self._parse_sentencetree(sentence, ignore_traces=ignore_traces)
        self._node_id += 1 # iterate after last subtree has been processed
        
    def _parse_sentencetree(self, tree, parent_node_id=None, ignore_traces=True):
        """parse a sentence Tree into this document graph"""
        def get_nodelabel(node):
            if isinstance(node, nltk.tree.Tree):
                return node.label()
            elif isinstance(node, unicode):
                return node.encode('utf-8')
            else:
                raise ValueError("Unexpected node type: {0}, {1}".format(type(node), node))

        root_node_id = self._node_id
        self.node[root_node_id]['label'] = get_nodelabel(tree)

        for subtree in tree:
            self._node_id += 1
            node_label = get_nodelabel(subtree)
            # unescape the node label, if necessary
            node_label = PTB_BRACKET_UNESCAPE.get(node_label, node_label)
            # TODO: refactor this, so we don't need to query this all the time
            if ignore_traces and node_label == '-NONE-': # ignore tokens annotated for traces
                continue
            if isinstance(subtree, nltk.tree.Tree):
                if len(subtree) > 1: # subtree is a syntactic category
                    node_attrs = {'label': node_label,
                                  self.ns+':cat': node_label}
                    layers = {self.ns, self.ns+':syntax'}
                else:  # subtree represents a token and its POS tag
                    node_attrs = {'label': node_label}
                    layers = {self.ns}

                edge_type = dg.EdgeTypes.dominance_relation
                self.add_node(self._node_id, layers=layers,
                              attr_dict=node_attrs)
                self.add_edge(root_node_id, self._node_id, edge_type=edge_type)

            else: # isinstance(subtree, unicode); subtree is a token
                # we'll have to modify the parent node of a token, since
                # in NLTK Trees, even a leaf node (with its POS tag) is
                # represented as a Tree (an iterator over a single unicode
                # string), e.g. ``Tree('NNS', ['prices'])``
                pos_tag = self.node[parent_node_id]['label']
                token_attrs = {
                    'label': node_label, self.ns+':token': node_label,
                    self.ns+':pos': pos_tag}
                self.node[parent_node_id].update(token_attrs)
                self.tokens.append(parent_node_id)

            if isinstance(subtree, nltk.tree.Tree):
                self._parse_sentencetree(subtree, parent_node_id=self._node_id)


# pseudo-function(s) to create a document graph from a Penn Treebank *.mrg file
read_mrg = read_ptb = PTBDocumentGraph



