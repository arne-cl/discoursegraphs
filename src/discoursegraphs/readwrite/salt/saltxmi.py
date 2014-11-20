#!/usr/bin/env python

"""
This script shall parse Salt XML files and convert them to a format more
suitable for graph visualization.

TODO: get parent element statistics!

:var XSI_TYPE_CLASSES:
    a dict that maps xsi:types (which most elements in a SaltXML file have)
    to the Classes that represent those elements
"""

import os
import networkx as nx
from lxml import etree
from collections import defaultdict

from discoursegraphs.readwrite.salt.nodes import (PrimaryTextNode,
                                                  TokenNode, SpanNode,
                                                  StructureNode,
                                                  extract_sentences)
from discoursegraphs.readwrite.salt.layers import SaltLayer
from discoursegraphs.readwrite.salt.edges import (DominanceRelation,
                                                  SpanningRelation,
                                                  TextualRelation)
from discoursegraphs.readwrite.salt.elements import get_elements
from discoursegraphs.readwrite.salt.util import get_xsi_type

TEST_DOC_ID = "maz-1423"
TEST_ROOT_DIR = os.path.expanduser('~/repos/salt-test/')

TEST_FILE1 = os.path.join(
    TEST_ROOT_DIR,
    "pcc176-syntax-rst-salt/salt:/",
    TEST_DOC_ID+".salt")

TEST_FILE2 = os.path.join(
    TEST_ROOT_DIR,
    "ritz-pcc176-syntax-coref-salt/pcc_maz176_merged_paula/",
    TEST_DOC_ID+".salt")

XSI_TYPE_CLASSES = {
    'sDocumentStructure:SStructure': StructureNode,
    'sDocumentStructure:SSpan': SpanNode,
    'sDocumentStructure:SToken': TokenNode,
    'sDocumentStructure:STextualDS': PrimaryTextNode,
    'sDocumentStructure:SSpanningRelation': SpanningRelation,
    'sDocumentStructure:STextualRelation': TextualRelation,
    'sDocumentStructure:SDominanceRelation': DominanceRelation,
    'saltCore:SLayer': SaltLayer}


class SaltXMIGraph(nx.DiGraph):
    """
    a DiGraph representation of a SaltXMI file (as truthful to the orginal
    as possible).

    Attributes
    ----------
    doc_id : str
        the document ID of the input file (e.g. salt:/maz-1423/maz-1423_graph)
    tree : etree._ElementTree
        an element tree representation of the SaltXMI input file
    """
    def __init__(self, document_path):
        """
        convert a SaltXMI file into a networkx DiGraph

        Parameters
        ----------
        document_path : str
            abosulte or relative path to a SaltXMI file
            (i.e. a SDocumentGraph)
        """
        super(SaltXMIGraph, self).__init__()
        self.tree = etree.parse(document_path)
        self.doc_id = get_doc_id(self.tree)
        for i, node_element in enumerate(get_elements(self.tree, 'nodes')):
            node = create_class_instance(node_element, i, self.doc_id)
            self.add_node(i, node.__dict__)
        for i, edge_element in enumerate(get_elements(self.tree, 'edges')):
            edge = create_class_instance(edge_element, i, self.doc_id)
            self.add_edge(edge.source, edge.target, edge.__dict__)


class SaltDocument(object):
    """
    represents the relevant parts of a SaltXML file as a class (with lists
    of ``SaltNode``\s, ``SaltEdge``\s and ``SaltLayer``\s.

    Attributes
    ----------
    doc_id : str
        the document ID of the input file (e.g. salt:/maz-1423/maz-1423_graph)
    tree : etree._ElementTree
        an element tree representation of the SaltXMI input file
    edges : list of SaltEdge
        i.e. TextualRelation, SpanningRelation or DominanceRelation
    nodes : list of SaltNode
        i.e. PrimaryTextNode, TokenNode, SpanNode, StructureNode
    layers : list of SaltLayer
    """
    def __init__(self, document_path):
        """
        creates a `SaltDocument` from a SaltXML file, by parsing it with
        `lxml.etree`.

        Parameters
        ----------
        document_path : str
            path to a SaltXML file
        """
        self.tree = etree.parse(document_path)
        self.doc_id = get_doc_id(self.tree)
        for element_type in ('nodes', 'edges', 'layers'):
            self._extract_elements(self.tree, element_type)

    def __str__(self):
        """
        returns the string representation of a `SaltDocument`, i.e
        node, edge and layer counts, as well as counts of subtypes and names
        of layers.
        """
        ret_str = ""
        for element_type in ('nodes', 'edges', 'layers'):
            elements = getattr(self, element_type)
            subtype_counts = defaultdict(int)
            ret_str += "{0} {1}:\n".format(len(elements), element_type)
            for element in elements:
                subtype_counts[type(element).__name__] += 1
            for subtype in subtype_counts:
                ret_str += "\t{0}: {1}\n".format(subtype,
                                                 subtype_counts[subtype])
                if element_type == 'layers':
                    layer_names = [layer.name for layer in self.layers]
                    ret_str += "\t\t" + ", ".join(layer_names)
            ret_str += "\n"
        return ret_str

    def _extract_elements(self, tree, element_type):
        """
        extracts all element of type `element_type from the `_ElementTree`
        representation of a SaltXML document and adds them to the corresponding
        `SaltDocument` attributes, i.e. `self.nodes`, `self.edges` and
        `self.layers`.

        Parameters
        ----------
        tree : lxml.etree._ElementTree
            an ElementTree that represents a complete SaltXML document
        element_type : str
            the tag name of a SaltXML element, e.g. `nodes` or `edges`
        """
        # creates a new attribute, e.g. 'self.nodes' and assigns it an
        # empty list
        setattr(self, element_type, [])
        etree_elements = get_elements(tree, element_type)
        for i, etree_element in enumerate(etree_elements):
            # create an instance of an element class (e.g. TokenNode)
            salt_element = create_class_instance(etree_element, i, self.doc_id)
            # and add it to the corresponding element type list,
            # e.g. 'self.nodes'
            getattr(self, element_type).append(salt_element)
            # In case of a 'nodes' element this is equivalent to:
            # self.nodes.append(TokenNode(etree_element, document_id))


class LinguisticDocument(object):
    """
    A LinguisticDocument should represent the information contained in a
    SaltDocument in a manner more suitable for linguistic processing,
    e.g. it should include a node for every sentence and store in/outgoing
    edges as features of (token) nodes.
    """
    def __init__(self, salt_document):
        """
        TODO: finish LinguisticDocument.__init__ docstring!
        additional, modified information:
          - adds string onsets/offsets to `TokenNode`s
          - adds the attribute 'self.sentences'
          - adds to each `SpanNode` the `TokenNode`s that belong to it
          - adds to each `TokenNode` the `SpanNode`s that it belongs to

        :param salt_document: SaltDocument

        Attributes
        ----------
        doc_id : str
            the document ID of the Salt document
        edges : list of SaltEdge
            i.e. SaltEdges of type ``TextualRelation``, ``SpanningRelation``
            and ``DominanceRelation``
        layers : list of SaltLayer
        nodes : list of SaltNode
            i.e. SaltEdges of type ``PrimaryTextNode``, ``TokenNode``,
            ``SpanNode`` and ``StructureNode``
        text : str
            the primary text of the Salt document
        tree : etree._ElementTree
            an ElementTree that represents a SaltXML document
        sentences : list of list of int
            a list of integers represents the ordered token node ids of
            the tokens in a sentence
        """
        self.doc_id = salt_document.doc_id
        self.edges = salt_document.edges
        self.layers = salt_document.layers
        self.nodes = salt_document.nodes
        self.text = salt_document.nodes[0].text
        self.tree = salt_document.tree

        # lists of node ids of a certain type
        self._token_node_ids = subtype_ids(self.nodes, TokenNode)
        self._span_node_ids = subtype_ids(self.nodes, SpanNode)
        self._structure_node_ids = subtype_ids(self.nodes, StructureNode)

        # lists of edge ids of a certain type
        self._textual_relation_ids = subtype_ids(self.edges, TextualRelation)
        self._spanning_relation_ids = subtype_ids(self.edges, SpanningRelation)
        self._dominance_relation_ids = subtype_ids(self.edges,
                                                   DominanceRelation)

        self._add_offsets_to_token_nodes()
        self.sentences = extract_sentences(self.nodes,
                                           self._token_node_ids)
        self._add_token_node_ids_to_span_nodes()
        self._add_span_node_ids_to_token_nodes()
        self._add_dominance_relation__to__nodes()

    def __str__(self):
        """
        returns the string representation of a `LinguisticDocument`, i.e
        node, edge and layer counts, as well as counts of subtypes and the
        primary text of the document itself.
        """
        ret_str = ""
        for element_type in ('nodes', 'edges', 'layers'):
            elements = getattr(self, element_type)
            subtype_counts = defaultdict(int)
            ret_str += "{0} {1}:\n".format(len(elements), element_type)
            for element in elements:
                subtype_counts[type(element).__name__] += 1
            for subtype in subtype_counts:
                ret_str += "\t{0}: {1}\n".format(subtype,
                                                 subtype_counts[subtype])
            ret_str += "\n"
        ret_str += "primary text:\n{0}".format(self.text.encode('utf-8'))
        return ret_str

    def print_sentence(self, sent_index):
        """
        returns the string representation of a sentence.

        :param sent_index: the index of a sentence (from ``self.sentences``)
        :type sent_index: int
        :return: the sentence string
        :rtype: str
        """
        tokens = [self.print_token(tok_idx)
                  for tok_idx in self.sentences[sent_index]]
        return ' '.join(tokens)

    def print_token(self, token_node_index):
        """returns the string representation of a token."""
        err_msg = "The given node is not a token node."
        assert isinstance(self.nodes[token_node_index], TokenNode), err_msg
        onset = self.nodes[token_node_index].onset
        offset = self.nodes[token_node_index].offset
        return self.text[onset:offset]

    def _add_offsets_to_token_nodes(self):
        """
        Adds primary text string onsets/offsets to all nodes that represent
        tokens. In SaltDocuments, this data was stored in TextualRelation
        edges only.
        """
        for edge_index in self._textual_relation_ids:
            token_node_index = self.edges[edge_index].source
            self.nodes[token_node_index].onset = self.edges[edge_index].onset
            self.nodes[token_node_index].offset = self.edges[edge_index].offset

    def _add_token_node_ids_to_span_nodes(self):
        """
        Adds to every span node the list of tokens (token node IDs) that belong
        to it.

        SpanNode.tokens - a list of `int` ids of `TokenNode`s
        """
        span_dict = defaultdict(list)
        for span_edge in self._spanning_relation_ids:
            token_node_id = self.edges[span_edge].target
            span_node_id = self.edges[span_edge].source
            span_dict[span_node_id].append(token_node_id)

        for span_node_id in span_dict:
            self.nodes[span_node_id].tokens = span_dict[span_node_id]

    def _add_span_node_ids_to_token_nodes(self):
        """
        Adds to every token node the list of spans (span node IDs) that it
        belongs to.

        TokenNode.spans - a list of `int` ids of `SpanNode`s
        """
        span_dict = defaultdict(list)
        for span_edge in self._spanning_relation_ids:
            token_node_id = self.edges[span_edge].target
            span_node_id = self.edges[span_edge].source
            span_dict[token_node_id].append(span_node_id)

        for token_node_id in span_dict:
            self.nodes[token_node_id].spans = span_dict[token_node_id]

    def _add_dominance_relation__to__nodes(self):
        """
        If a node (usually a `TokenNode` or `StructureNode`) is dominated by
        another `StructureNode`, the dominated node will receive a
        `dominated_by` attribute, while the dominating node will receive a
        `dominates` attribute.

        Node.dominated_by - if present, the `int` index of the node that
        dominates this node
        Node.dominates - if present, the `int` index of the node that is
        dominated by this node
        """
        dominating_dict = defaultdict(list)
        dominated_dict = defaultdict(list)
        for dom_rel_id in self._dominance_relation_ids:
            dominated_node_id = self.edges[dom_rel_id].target
            dominating_node_id = self.edges[dom_rel_id].source
            dominating_dict[dominating_node_id].append(dominated_node_id)
            dominated_dict[dominated_node_id].append(dominating_node_id)

        for dominating_node_id in dominating_dict:
            self.nodes[dominating_node_id].dominates = \
                dominating_dict[dominating_node_id]
        for dominated_node_id in dominated_dict:
            self.nodes[dominated_node_id].dominated_by = \
                dominated_dict[dominated_node_id]


def create_class_instance(element, element_id, doc_id):
    """
    given an Salt XML element, returns a corresponding `SaltElement` class
    instance, i.e. a SaltXML `SToken` node will be converted into a
    `TokenNode`.

    Parameters
    ----------
    element : lxml.etree._Element
        an `etree._Element` is the XML representation of a Salt element,
        e.g. a single 'nodes' or 'edges' element
    element_id : int
        the index of element (used to connect edges to nodes)
    doc_id : str
        the ID of the SaltXML document

    Returns
    -------
    salt_element : SaltElement
        an instance of a `SaltElement` subclass instance, e.g. a `TokenNode`,
        `TextualRelation` or `SaltLayer`
    """
    xsi_type = get_xsi_type(element)
    element_class = XSI_TYPE_CLASSES[xsi_type]
    return element_class.from_etree(element)


def get_doc_id(element_tree):
    """
    returns the document ID of a SaltXML document.

    :param tree: an ElementTree that represents a complete SaltXML document
    :type tree: ``lxml.etree._ElementTree``
    """
    id_element = element_tree.xpath('labels[@name="id"]')[0]
    return id_element.attrib['valueString']


def subtype_ids(elements, subtype):
    """
    returns the ids of all elements of a list that have a certain type,
    e.g. show all the nodes that are ``TokenNode``\s.
    """
    return [i for (i, element) in enumerate(elements)
            if isinstance(element, subtype)]


def tree_statistics(tree):
    """
    prints the types and counts of elements present in a SaltDocument tree,
    e.g.::

        layers: 3
        sDocument: 1
        nodes: 252
        labels: 2946
        edges: 531

    """
    all_elements = tree.findall('//')
    tag_counter = defaultdict(int)
    for element in all_elements:
        tag_counter[element.tag] += 1
    for (tag, counts) in tag_counter.items():
        print "{0}: {1}".format(tag, counts)


def abslistdir(directory):
    """
    returns a list of absolute filepaths for all files found in the given
    directory.
    """
    abs_dir = os.path.abspath(directory)
    filenames = os.listdir(abs_dir)
    return [os.path.join(abs_dir, filename) for filename in filenames]


if __name__ == "__main__":
    sd = SaltDocument(TEST_FILE2)
    ld = LinguisticDocument(sd)
    sx = SaltXMIGraph(TEST_FILE2)
