#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
The ``tiger`` module converts a ``TigerXML`` file into a networkx-based
document graph.
"""

import os
from lxml import etree

import discoursegraphs as dg
from discoursegraphs import DiscourseDocumentGraph, EdgeTypes
from discoursegraphs.util import natural_sort_key, ensure_unicode, add_prefix
from discoursegraphs.readwrite.generic import generic_converter_cli
from discoursegraphs.relabel import relabel_nodes


class TigerDocumentGraph(DiscourseDocumentGraph):
    """
    A directed graph with multiple edges (based on
    networkx.MultiDiGraph) that represents all the
    sentences contained in a TigerXML file. A ``TigerDocumentGraph``
    contains a document root node (whose ID is stored in ``self.root``),
    which has an outgoing edge to the sentence root nodes of each
    sentence.

    To print all tokens of a Tiger document, just do::

        tdg = TigerDocumentGraph('/path/to/tiger.file')
        for token_id in tdg.tokens:
            print tdg.node[token_id]['tiger:word']

    If you want to access the tokens of a specific sentence, use::

        tdg = TigerDocumentGraph('/path/to/tiger.file')
        # print all tokens of the second sentence
        for token_id in tdg.node[tdg.sentences[1]]['tokens']:
            print tdg.get_token(token_id)

    Attributes
    ----------
    corpus_id : str
        ID of the TigerXML document specified in the 'id' attribute
        of the <corpus> element
    ns : str
        the namespace of the graph (default: tiger)
    root : str
        the ID of the root node of the document graph
    sentences : list of str
        sorted list of all sentence root node IDs (of sentences
        contained in this document graph)
    tokens : list of str
        sorted list of all token node IDs contained in this document graph
    """
    def __init__(self, tiger_filepath=None, name=None, namespace='tiger'):
        """
        Creates a directed graph that represents all syntax annotated
        sentences in the given TigerXML file.

        Parameters
        ----------
        tiger_filepath : str or None
            absolute or relative path to the TigerXML file to be parsed.
            If no path is given, return an empty TigerDocumentGraph.
        name : str or None
            the name or ID of the graph to be generated. If no name is
            given, the basename of the input file is used.
        namespace : str
            the namespace of the graph (default: tiger)
        """
        # super calls __init__() of base class DiscourseDocumentGraph
        super(TigerDocumentGraph, self).__init__(namespace=namespace)

        self.ns = namespace
        if not tiger_filepath:
            return  # create empty document graph

        utf8_parser = etree.XMLParser(encoding="utf-8")
        tigerxml_tree = etree.parse(tiger_filepath, utf8_parser)
        tigerxml_root = tigerxml_tree.getroot()

        self.name = name if name else os.path.basename(tiger_filepath)
        self.corpus_id = tigerxml_root.attrib['id']

        self.tokens = []
        self.sentences = []
        for sentence in tigerxml_root.iterfind('./body/s'):
            self.__add_sentence_to_document(sentence)
        self.sentences = sorted(self.sentences, key=natural_sort_key)

    def __add_sentence_to_document(self, sentence):
        """
        Converts a sentence into a TigerSentenceGraph and adds all
        its nodes, edges (and their features) to this document graph.

        This also adds a ``dominance_relation`` edge from the root node of this
        document graph to the root node of the sentence and appends the
        sentence root node ID to ``self.sentences``.

        Parameters
        ----------
        sentence : lxml.etree._Element
            a sentence from a TigerXML file in etree element format
        """
        sentence_graph = TigerSentenceGraph(sentence)
        self.tokens.extend(sentence_graph.tokens)
        sentence_root_node_id = sentence_graph.root

        self.add_nodes_from(sentence_graph.nodes(data=True))
        self.add_edges_from(sentence_graph.edges(data=True))
        self.add_edge(self.root, sentence_root_node_id,
                      layers={self.ns, self.ns+':sentence'},
                      edge_type=EdgeTypes.dominance_relation)
        self.sentences.append(sentence_root_node_id)


class TigerSentenceGraph(DiscourseDocumentGraph):
    """
    A directed graph (based on a networkx.MultiDiGraph) that represents
    one syntax annotated sentence extracted from a TigerXML file.

    Attributes
    ----------
    ns : str
        the namespace of the graph (default: tiger)
    root : str
        node ID of the root node of the sentence
    tokens : list of str
        a sorted list of terminal node IDs (i.e. token nodes)
    """
    def __init__(self, sentence, namespace='tiger'):
        """
        Creates a directed graph from a syntax annotated sentence (i.e.
        a <s> element from a TigerXML file parsed into an lxml etree
        Element). For performance reasons, a sorted list of terminals
        (i.e. nodes representing tokens) is stored under
        ``self.tokens``.

        Parameters
        ----------
        sentence : lxml.etree._Element
            a sentence from a TigerXML file in etree element format
        namespace : str
            the namespace of the graph (default: tiger)
        """
        # super calls __init__() of base class DiscourseDocumentGraph
        super(TigerSentenceGraph, self).__init__(namespace=namespace)
        self.remove_node(self.root)  # delete default root node
        self.ns = namespace

        self.tokens = []

        graph_element = sentence.find('./graph')
        self.root = graph_element.attrib['root']
        self.name = sentence.attrib.get('id', '')

        # sentence.attrib is a lxml.etree._Attrib, which is 'dict-like'
        # but doesn't behave exactly like a dict (i.e. it threw an error
        # when I tried to update it)
        sentence_attributes = add_prefix(sentence.attrib, self.ns+':')

        # some sentences in the Tiger corpus are marked as discontinuous
        if 'discontinuous' in graph_element.attrib:
            sentence_attributes.update(
                {self.ns+':discontinuous':
                    graph_element.attrib['discontinuous']})

        self.__tigersentence2graph(sentence)
        self.__repair_unconnected_nodes()

    def __tigersentence2graph(self, sentence):
        """
        Reads a sentence with syntax annotation (parsed from a TigerXML
        file) into this directed graph. Adds an attribute named 'tokens'
        to the sentence root node containing a sorted list of token node
        IDs. (The same list is also stored in ``self.tokens``).

        Parameters
        ----------
        sentence : lxml.etree._Element
            a sentence from a TigerXML file in etree element format
        """
        # add sentence root to graph
        self.add_node(self.root,
                      layers={self.ns, self.ns+':sentence',
                              self.ns+':sentence:root',
                              self.ns+':syntax'})

        token_ids = []
        # add terminals to graph (tokens)
        for t in sentence.iterfind('./graph/terminals/t'):
            terminal_id = t.attrib['id']
            token_ids.append(terminal_id)
            # all token attributes shall belong to the tiger namespace
            terminal_features = add_prefix(t.attrib, self.ns+':')
            # convert tokens to unicode
            terminal_features[self.ns+':token'] = ensure_unicode(
                terminal_features[self.ns+':word'])
            self.add_node(terminal_id, layers={self.ns, self.ns+':token'},
                          attr_dict=terminal_features,
                          label=terminal_features[self.ns+':token'])

            # add secedge pointing relations from tokens to other tokens or
            # syntactic categories
            for secedge in t.iterfind('./secedge'):
                to_id = secedge.attrib['idref']
                secedge_attribs = add_prefix(secedge.attrib, self.ns+':')
                if to_id not in self:  # if graph doesn't contain to-node, yet
                    self.add_node(to_id, layers={self.ns, self.ns+':secedge'})
                self.add_edge(terminal_id, to_id,
                              layers={self.ns, self.ns+':secedge'},
                              attr_dict=secedge_attribs,
                              edge_type=EdgeTypes.pointing_relation)

        # add sorted list of all token node IDs to sentence root node
        # to make queries simpler/faster
        sorted_token_ids = sorted(token_ids, key=natural_sort_key)
        self.node[self.root].update({'tokens': sorted_token_ids})
        self.tokens = sorted_token_ids

        # add nonterminals (syntax categories) to graph
        for nt in sentence.iterfind('./graph/nonterminals/nt'):
            from_id = nt.attrib['id']
            nt_feats = add_prefix(nt.attrib, self.ns+':')
            nt_feats['label'] = nt_feats[self.ns+':cat']
            # root node already exists, but doesn't have a cat value
            if from_id in self:
                self.node[from_id].update(nt_feats)
            else:
                self.add_node(from_id, layers={self.ns, self.ns+':syntax'},
                              attr_dict=nt_feats)

            # add edges to graph (syntax cat dominances token/other cat)
            for edge in nt.iterfind('./edge'):
                to_id = edge.attrib['idref']
                if to_id not in self:  # if graph doesn't contain to-node, yet
                    self.add_node(to_id, layers={self.ns, self.ns+':secedge'})
                edge_attribs = add_prefix(edge.attrib, self.ns+':')

                # add a spanning relation from a syntax cat to a token
                if self.ns+':token' in self.node[to_id]['layers']:
                    edge_type = EdgeTypes.spanning_relation
                else:  # add a dominance relation between two syntax categories
                    edge_type = EdgeTypes.dominance_relation

                self.add_edge(from_id, to_id,
                              layers={self.ns, self.ns+':edge'},
                              attr_dict=edge_attribs,
                              label=edge_attribs[self.ns+':label'],
                              edge_type=edge_type)

            # add secondary edges to graph (cat points to other cat/token)
            for secedge in nt.iterfind('./secedge'):
                to_id = secedge.attrib['idref']
                if to_id not in self:  # if graph doesn't contain to-node, yet
                    self.add_node(to_id, layers={self.ns, self.ns+':secedge'})
                secedge_attribs = add_prefix(secedge.attrib, self.ns+':')
                self.add_edge(from_id, to_id,
                              layers={self.ns, self.ns+':secedge'},
                              attr_dict=secedge_attribs,
                              label=edge_attribs[self.ns+':label'],
                              edge_type=EdgeTypes.pointing_relation)

    def __repair_unconnected_nodes(self):
        """
        Adds a (``dominance_relation``) edge from the sentence root node to all
        previously unconnected nodes (token nodes, that either represent a
        punctuation mark or are part of a headline 'sentence' that has no
        full syntax structure annotation).
        """
        unconnected_node_ids = get_unconnected_nodes(self)
        if dg.istoken(self, self.root):
            # This sentence has no hierarchical structure, i.e. the root
            # node is also a terminal / token node.
            # We will add a virtual root node to compensate for this.
            self.root = self.ns+':VROOT'
            self.add_node(self.root,
                layers={'tiger', 'tiger:syntax', 'tiger:sentence',
                        'tiger:sentence:root'})

        for unconnected_node_id in unconnected_node_ids:
            self.add_edge(self.root, unconnected_node_id,
                          layers={self.ns, self.ns+':sentence',
                                  self.ns+':unconnected'},
                          edge_type=EdgeTypes.dominance_relation)


def _get_terminals_and_nonterminals(sentence_graph):
    """
    Given a TigerSentenceGraph, returns a sorted list of terminal node
    IDs, as well as a sorted list of nonterminal node IDs.

    Parameters
    ----------
    sentence_graph : TigerSentenceGraph
        a directed graph representing one syntax annotated sentence from
        a TigerXML file

    Returns
    -------
    terminals, nonterminals : list of str
        a sorted list of terminal node IDs and a sorted list of
        nonterminal node IDs
    """
    terminals = set()
    nonterminals = set()
    for node_id in sentence_graph.nodes_iter():
        if sentence_graph.out_degree(node_id) > 0:
            # all nonterminals (incl. root)
            nonterminals.add(node_id)
        else:  # terminals
            terminals.add(node_id)
    return sorted(list(terminals), key=natural_sort_key), \
        sorted(list(nonterminals), key=natural_sort_key)


def get_unconnected_nodes(sentence_graph):
    """
    Takes a TigerSentenceGraph and returns a list of node IDs of
    unconnected nodes.

    A node is unconnected, if it doesn't have any in- or outgoing edges.
    A node is NOT considered unconnected, if the graph only consists of
    that particular node.

    Parameters
    ----------
    sentence_graph : TigerSentenceGraph
        a directed graph representing one syntax annotated sentence from
        a TigerXML file

    Returns
    -------
    unconnected_node_ids : list of str
        a list of node IDs of unconnected nodes
    """
    return [node for node in sentence_graph.nodes_iter()
            if sentence_graph.degree(node) == 0 and
            sentence_graph.number_of_nodes() > 1]


def get_subordinate_clauses(tiger_docgraph):
    """
    given a document graph of a TIGER syntax tree, return all
    node IDs of nodes representing subordinate clause constituents.

    Parameters
    ----------
    tiger_docgraph : DiscourseDocumentGraph or TigerDocumentGraph
        document graph from which subordinate clauses will be extracted

    Returns
    -------
    subord_clause_nodes : list(str)
        list of node IDs of nodes directly dominating subordinate clauses
    """
    subord_clause_rels = \
        dg.select_edges_by_attribute(
            tiger_docgraph, attribute='tiger:label',
            value=['MO', 'RC', 'SB'])

    subord_clause_nodes = []
    for src_id, target_id in subord_clause_rels:
        src_cat = tiger_docgraph.node[src_id].get('tiger:cat')
        if src_cat == 'S' and not dg.istoken(tiger_docgraph, target_id):
            subord_clause_nodes.append(target_id)
    return subord_clause_nodes


# pseudo-function to create a document graph from a Tiger XML file
read_tiger = TigerDocumentGraph


if __name__ == '__main__':
    generic_converter_cli(TigerDocumentGraph, 'TigerXML (syntax)')
