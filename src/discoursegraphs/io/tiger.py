#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <arne-neumann@web.de>

import sys
import os
import re
from lxml import etree, objectify
from networkx import MultiDiGraph, write_gpickle

INTEGER_RE = re.compile('([0-9]+)')

class TigerDocumentGraph(MultiDiGraph):
    """
    A directed graph (networkx.MultiDiGraph) that represents all the
    sentences contained in a TigerXML file. A ``TigerDocumentGraph``
    contains a document root node (whose ID is stored in ``self.root``),
    which has an outgoing edge to the sentence root nodes of each
    sentence.

    Attributes
    ----------
    filename : str
        filename of the TigerXML file that was parsed
    corpus_id : str
        ID of the TigerXML document specified in the 'id' attribute
        of the <corpus> element
    root : str
        the ID of the root node of the document graph
    sentences : list of str
        sorted list of all sentence root node IDs (of sentences
        contained in this document graph)
    """
    def __init__(self, tiger_filepath):
        """
        Creates a directed graph that represents all syntax annotated
        sentences in the given TigerXML file.

        Parameters
        ----------
        tiger_filepath : str
            absolute or relative path to the TigerXML file to be parsed
        """
        # super calls __init__() of base class MultiDiGraph
        super(TigerDocumentGraph, self).__init__()

        utf8_parser = etree.XMLParser(encoding="utf-8")
        tigerxml_tree = etree.parse(tiger_filepath, utf8_parser)
        tigerxml_root = tigerxml_tree.getroot()

        self.filename = os.path.basename(tiger_filepath)
        self.corpus_id = tigerxml_root.attrib['id']

        # add root node of TigerDocumentGraph
        self.root = 'tiger_root_node'
        self.add_node(self.root, type='tiger_root_node')

        self.sentences = []
        for sentence in tigerxml_root.iterfind('./body/s'):
            self.__add_sentence_to_document(sentence)
        self.sentences = sorted(self.sentences, key=_natural_sort_key)

    def __add_sentence_to_document(self, sentence):
        """
        Converts a sentence into a TigerSentenceGraph and adds all
        its nodes, edges (and their features) to this graph.
        This also adds an edge from the root node of this document
        graph to the root node of the sentence and appends the
        sentence root node ID to ``self.sentences``.

        Parameters
        ----------
        sentence : lxml.etree._Element
            a sentence from a TigerXML file in etree element format
        """
        sentence_graph = TigerSentenceGraph(sentence)
        sentence_root_node_id = sentence_graph.root

        self.add_nodes_from(sentence_graph.nodes(data=True))
        self.add_edges_from(sentence_graph.edges(data=True))
        self.add_edge(self.root, sentence_root_node_id)
        self.sentences.append(sentence_root_node_id)


class TigerSentenceGraph(MultiDiGraph):
    """
    A directed graph (networkx.MultiDiGraph) that represents one syntax
    annotated sentence extracted from a TigerXML file.

    Attributes
    ----------
    root : str
        node ID of the root node of the sentence
    tokens : list of str
        a sorted list of terminal node IDs (i.e. token nodes)
    """
    def __init__(self, sentence):
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
        """
        # super calls __init__() of base class MultiDiGraph
        super(TigerSentenceGraph, self).__init__()

        graph_element = sentence.find('./graph')
        sentence_root_id = graph_element.attrib['root']

        # sentence.attrib is a lxml.etree._Attrib, which is 'dict-like'
        # but doesn't behave exactly like a dict (i.e. it threw an error
        # when I tried to update it)
        sentence_attributes = dict(sentence.attrib)

        # some sentences in the Tiger corpus are marked as discontinuous
        if 'discontinuous' in graph_element.attrib:
            sentence_attributes.update({'discontinuous': graph_element.attrib['discontinuous']})

        self.__add_vroot(sentence_root_id, sentence_attributes)
        self.__tigersentence2graph(sentence)
        self.__repair_unconnected_nodes()

    def __tigersentence2graph(self, sentence):
        """
        Reads a sentence with syntax annotation (parsed from a TigerXML
        file) into this directed graph. Adds an attribute named 'tokens'
        to the sentence root node containing a sorted list of token node
        IDs.

        Parameters
        ----------
        sentence : lxml.etree._Element
            a sentence from a TigerXML file in etree element format
        """
        token_ids = []
        for t in sentence.iterfind('./graph/terminals/t'):
            terminal_id = t.attrib['id']
            token_ids.append(terminal_id)
            terminal_features = {key:t.attrib[key] for key in t.attrib
                                                    if key != 'id'}
            # convert tokens to unicode
            terminal_features['word'] = ensure_unicode(terminal_features['word'])
            self.add_node(terminal_id, terminal_features)
            for secedge in t.iterfind('./secedge'):
                to_id = secedge.attrib['idref']
                self.add_edge(terminal_id, to_id, attr_dict=secedge.attrib,
                                type='secedge')

        # add sorted list of all token node IDs to sentence root node
        # for performance reasons
        sorted_token_ids = sorted(token_ids, key=_natural_sort_key)
        self.node[self.root].update({'tokens': sorted_token_ids})

        for nt in sentence.iterfind('./graph/nonterminals/nt'):
            from_id = nt.attrib['id']
            nt_feats = {key:nt.attrib[key] for key in nt.attrib
                                            if key != 'id'}
            if self.has_node(from_id): #root node already exists,
                                       #but doesn't have a cat value
                    self.node[from_id].update(nt_feats)
            else:
                self.add_node(from_id, nt_feats)

            for edge in nt.iterfind('./edge'):
                to_id = edge.attrib['idref']
                self.add_edge(from_id, to_id, attr_dict=edge.attrib, type='edge')

            for secedge in nt.iterfind('./secedge'):
                to_id = secedge.attrib['idref']
                self.add_edge(from_id, to_id, attr_dict=secedge.attrib,
                                type='secedge')


    def __add_vroot(self, sentence_root_id, sentence_attributes):
        """
        Adds a new node with the ID 'VROOT' to this sentence graph.
        The 'VROOT' node will have an outgoing edge to the node that has
        previously been considered the root node of the sentence and
        will have the attributes extracted from the <s> element of the
        corresponding sentence in the TigerXML file.
        The ``TigerSentenceGraph.root`` attribute will be set as well.

        Why do we do this?

        'VROOT' (virtual root) nodes are commonly used in the Tiger
        corpus (version 2.1). They are useful whenever a sentence does
        not have any nonterminals (e.g. if there is no full syntax
        structure annotation in the case of a three word headline
        'sentence').

        Parameters
        ----------
        sentence_root_id : str
            the ID of the root node of the sentence, extracted from the
            ``root`` attribute of the ``<graph>`` element of the
            corresponding sentence in the TigerXML file.
        sentence_attributes : dict of (str, str)
            a dictionary of sentence attributes extracted from the <s>
            element (corresponding to this sentence) of a TigerXML file.
            contains the attributes ``id``, ``art_id`` and ``orig_id``.
        """
        old_root_node_id = sentence_root_id
        sentence_id = sentence_attributes['id']
        new_root_node_id = 'VROOT-{0}'.format(sentence_id)
        self.add_node(new_root_node_id, sentence_attributes)
        self.add_edge(new_root_node_id, old_root_node_id)
        self.root = new_root_node_id

    def __repair_unconnected_nodes(self):
        """
        Adds an edge from the 'VROOT' node to all previously unconnected
        nodes (token nodes, that either represent a punctuation mark or
        are part of a headline 'sentence' that has no full syntax
        structure annotation).
        """
        unconnected_node_ids = get_unconnected_nodes(self)
        for unconnected_node_id in unconnected_node_ids:
            self.add_edge(self.root, unconnected_node_id)


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
        else: # terminals
            terminals.add(node_id)
    return sorted(list(terminals), key=_natural_sort_key), \
            sorted(list(nonterminals), key=_natural_sort_key)


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


def _natural_sort_key(s):
    """
    returns a key that can be used in sort functions.

    Example:

    >>> items = ['A99', 'a1', 'a2', 'a10', 'a24', 'a12', 'a100']

    The normal sort function will ignore the natural order of the
    integers in the string:

    >>> print sorted(items)
    ['A99', 'a1', 'a10', 'a100', 'a12', 'a2', 'a24']

    When we use this function as a key to the sort function,
    the natural order of the integer is considered.

    >>> print sorted(items, key=natural_sort_key)
    ['A99', 'a1', 'a2', 'a10', 'a12', 'a24', 'a100']
    """
    return [int(text) if text.isdigit() else text
            for text in re.split(INTEGER_RE, s)]

def ensure_unicode(str_or_unicode):
    """
    tests, if the input is ``str`` or ``unicode``. if it is ``str``, it
    will be decoded from ``UTF-8`` to unicode.
    """
    if isinstance(str_or_unicode, str):
        return str_or_unicode.decode('utf-8')
    elif isinstance(str_or_unicode, unicode):
        return str_or_unicode
    else:
        raise ValueError("Input '{0}' should be a string or unicode, "
                        "but its of type {1}".format(str_or_unicode,
                                                type(str_or_unicode)))



#~ def graph2tigersentence(sentence_graph):
    #~ """
    #~ @param sentence_graph: a directed graph containing a Tiger format
        #~ sentence structure and annotations (syntax and morphology)
    #~ @type sentence_graph: MultiDiGraph
    #~ """
    #~ terminals, nonterminals = _get_terminals_and_nonterminals(sentence_graph)
    #~ sentence_root = objectify.Element('s', sentence_graph.metadata)
    #~ graph_root = objectify.SubElement(sentence_root, 'graph', root=sentence_graph.root)
    #~ terms_node = objectify.SubElement(graph_root, 'terminals')
    #~ for term_id in terminals:
        #~ terms_node.append(objectify.Element('t', sentence_graph.node[term_id], id=term_id))
#~
    #~ nonterms_node = objectify.SubElement(graph_root, 'nonterminals')
    #~ for nt_id in nonterminals:
        #~ nt_node = objectify.Element('nt', sentence_graph.node[nt_id], id=nt_id)
        #~ # edges are grouped by their source node in TigerXML
        #~ for out_edge in sentence_graph.out_edges(nt_id, data=True):
            #~ from_id, to_id, edge_attribs = out_edge
            #~ nt_node.append(objectify.Element('edge', edge_attribs))
        #~ nonterms_node.append(nt_node)
#~
    #~ objectify.deannotate(sentence_root, cleanup_namespaces=True)
    #~ return sentence_root


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.stderr.write('Usage: {0} TigerXML_input_file networkx_pickle_output_file\n'.format(sys.argv[0]))
        sys.exit(1)
    else:
        tiger_filepath = sys.argv[1]
        pickle_filepath = sys.argv[2]
        assert os.path.isfile(tiger_filepath)
        tiger_docgraph = TigerDocumentGraph(tiger_filepath)
        write_gpickle(tiger_docgraph, pickle_filepath)


