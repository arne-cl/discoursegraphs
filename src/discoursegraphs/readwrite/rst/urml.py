#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module converts an URML XML file (represents underspecified
rhetorical structure annotations) into a networkx-based directed graph
(``DiscourseDocumentGraph``).
"""

import os

from lxml import etree
import networkx as nx

from discoursegraphs import DiscourseDocumentGraph, EdgeTypes
from discoursegraphs.util import sanitize_string
from discoursegraphs.readwrite.generic import XMLElementCountTarget
from discoursegraphs.readwrite.rst.common import get_segment_label


class URMLCorpus(object):
    """
    represents an URML formatted corpus of RST annotated documents as an
    iterable over URMLDocumentGraph instances (or an iterable over
    <document> elements if ``debug`` is set to ``True``).

    This class is used to 'parse' an URML XML file iteratively, using as
    little memory as possible. To retrieve the document graphs of the
    documents contained in the corpus, simply iterate over the class
    instance (or use the ``.next()`` method).
    """
    def __init__(self, urml_file, name=None, debug=False, tokenize=True,
                 precedence=False):
        """
        Parameters
        ----------
        urml_file : str
            path to an ExportXML formatted corpus file
        name : str or None
            the name or ID of the graph to be generated. If no name is
            given, the basename of the input file is used.
        debug : bool
            If True, yield the etree element representations of the <text>
            elements found in the document.
            If False, create an iterator that parses the documents
            contained in the file into ExportXMLDocumentGraph instances.
            (default: False)
        tokenize : bool
            If True, the RST segments (i.e. nuclei and satellites) will
            be tokenized and added as additonal token nodes to the
            document graph (with edges from the respective RST segments).
        precedence : bool
            If True (and if tokenize == True), add precedence relation edges
            (root precedes token1, which precedes token2 etc.)
        """
        self.name = name if name else os.path.basename(urml_file)
        self._num_of_documents = None
        self.urml_file = urml_file
        self.path = os.path.abspath(urml_file)
        self.debug = debug
        self.tokenize = tokenize
        self.precedence = precedence

        self.__context = None
        self._reset_corpus_iterator()

    def _reset_corpus_iterator(self):
        """
        create an iterator over all documents in the file (i.e. all
        <text> elements).

        Once you have iterated over all documents, call this method again
        if you want to iterate over them again.
        """
        self.__context = etree.iterparse(self.urml_file, events=('end',),
                                         tag='document', recover=False)

    def __len__(self):
        if self._num_of_documents is not None:
            return self._num_of_documents
        return self._get_num_of_documents()

    def _get_num_of_documents(self):
        '''
        counts the number of documents in an URML file.
        adapted from Listing 2 on
        http://www.ibm.com/developerworks/library/x-hiperfparse/
        '''
        parser = etree.XMLParser(target=XMLElementCountTarget('document'))
        # When iterated over, 'results' will contain the output from
        # target parser's close() method
        num_of_documents = etree.parse(self.urml_file, parser)
        self._num_of_documents = num_of_documents
        return num_of_documents

    def __iter__(self):
        return iter(self.document_iter(self.__context))

    def next(self):
        """convenience method to get the next element of this iterable"""
        # to build an iterable, __iter__() would be sufficient,
        # but adding a next() method is quite common
        return self.__iter__().next()

    def document_iter(self, context):
        """
        Iterates over all the elements in an iterparse context
        (here: <document> elements) and yields an URMLDocumentGraph instance
        for each of them. For efficiency, the elements are removed from the
        DOM / main memory after processing them.

        If ``self.debug`` is set to ``True`` (in the ``__init__`` method),
        this method will yield <documents> elements, which can be used to
        construct ``URMLDocumentGraph``s manually.
        """
        for _event, elem in context:
            if not self.debug:
                yield URMLDocumentGraph(elem, tokenize=self.tokenize,
                                        precedence=self.precedence)
            else:
                yield elem
            # removes element (and references to it) from memory after processing it
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
        del context


class URMLDocumentGraph(DiscourseDocumentGraph):
    """A directed graph with multiple edges (based on a networkx
    MultiDiGraph) that represents the potentially underspecified
    rhetorical structure of a document. It is generated from a URML file.

    Attributes
    ----------
    name : str
        name, ID of the document or file name of the input file
    ns : str
        the namespace of the document (default: urml)
    relations : dict of (str, str)
        Returns a dictionary with RST relation names as keys (str)
        and relation types (either 'par' or 'hyp') as values
        (str).
    segments : list of str
        list of segment node IDs (i.e. leaf nodes in a RST
        tree that represent segments of text).
    segment_types : dict(str: str)
        maps from segment node ID to its type (i.e. 'nucleus' or 'satellite')
    root : str
        name of the document root node ID
    tokens : list of str
        sorted list of all token node IDs contained in this document graph
    tokenized : bool
        True (default), if the segments have been tokenized (after they were
        imported from an URML file) and have outgoing edges to nodes
        representing tokens.
        False, if the segments represent untokenized text.
    """
    def __init__(self, document_elem, name=None, namespace='urml',
                 tokenize=True, precedence=False):
        """Creates an URMLDocumentGraph from a URML XML file and adds
        metadata to it (filename of the URML file, names and types of allowed
        RST relations).

        Parameters
        ----------
        document_elem : lxml.etree._Element or None
            An etree representation of a <document> element of a URML XML file.
            If None, return an empty URMLDocumentGraph
        name : str or None
            the name or ID of the graph to be generated. If no name is
            given, TODO ...
        namespace : str
            the namespace of the document (default: urml)
        tokenize : bool
            If True, the RST segments (i.e. nuclei and satellites) will
            be tokenized and added as additonal token nodes to the
            document graph (with edges from the respective RST segments).
        precedence : bool
            If True (and if tokenize == True), add precedence relation edges
            (root precedes token1, which precedes token2 etc.)
        """
        # super calls __init__() of base class DiscourseDocumentGraph
        super(URMLDocumentGraph, self).__init__(namespace=namespace)

        self.ns = namespace
        if document_elem is None:
            return  # create empty document graph

        self.name = name if name else document_elem.attrib['id']

        # self.root will be set by __urml2graph() later on
        # __add_segment() will handle tokenization if necessary
        self.tokenized = False
        self.tokenize = tokenize
        self.tokens = []
        self.edus = []
        self.segment_types = extract_segment_types(document_elem, self.ns)

        self.__urml2graph(document_elem)

        if self.tokenize:
            if precedence:
                self.add_precedence_relations()

        # the nodes representing EDUs (elementary discourse units)
        # will be stored here (to keep them even after merging graphs)
        if self.ns+':edus' not in self.node[self.root]['metadata']:
            self.node[self.root]['metadata'][self.ns+':edus'] = self.edus

    def __urml2graph(self, document_elem):
        """
        Reads an RST tree (from an ElementTree representation of an URML
        XML file) and adds all segments (nodes representing text) and
        relations (nonterminal nodes in an RST tree as well as the
        relationships that hold between them) to this
        URMLDocumentGraph.

        Parameters
        ----------
        document_elem : lxml.etree._Element
            etree representation of a <document> element of a URML XML file
        tokenize : bool
            If True, the RST segments (i.e. nuclei and satellites) will
            be tokenized and added as additonal token nodes to the
            document graph (with edges from the respective RST segments).
            If False, each RST segment will be labeled with the text it
            represents.
        """
        for segment in document_elem.iter('segment'):
            self.__add_segment(segment)
        for relation in document_elem.iter('parRelation', 'hypRelation'):
            self.__add_relation(relation)

        # each discourse docgraphs has a default root node, but we will
        # overwrite it here
        old_root_id = self.root
        # the easiest way to find the root node of a URML graph is to find the
        # origin of the longest path
        root_id = nx.algorithms.dag_longest_path(self)[0]
        self.root = root_id
        # copy metadata from old root node
        self.node[root_id]['metadata'] = self.node[old_root_id]['metadata']
        # finally, remove the old root node
        self.remove_node(old_root_id)

    def __add_segment(self, segment):
        """
        add attributes to segment nodes, as well as edges to/from other
        segments/groups. add segment to list of EDUs.

        Parameters
        ----------
        segment : ??? etree Element
        """
        segment_id = self.ns+':'+segment.attrib['id']
        self.edus.append(segment_id)  # store RST segment in list of EDUs

        # A URML file can be tokenized, partially tokenized or not tokenized
        # at all. The "tokenized tokens" in the URML file will always be added
        # to the graph as nodes. The "untokenized tokens" will only be added,
        # if ``self.tokenize`` is ``True``.

        if is_segment_tokenized(segment):
            self.tokenized = True
            segment_text = sanitize_string(
                ' '.join(e.text for e in segment if e.text is not None))

            for i, tok_elem in enumerate(segment):
                tok = tok_elem.text
                self.__add_token(segment_id, i, tok)

        else:  # is_segment_tokenized(segment) is False
            segment_text = sanitize_string(segment.text)
            segment_toks = segment_text.split()

            if self.tokenize:
                self.tokenized = True
                for i, tok in enumerate(segment_toks):
                    self.__add_token(segment_id, i, tok)

        segment_type = self.segment_types[segment_id]
        segment_label = get_segment_label(
            segment, segment_type, segment_text, self.ns, self.tokenize)
        self.add_node(
            segment_id, layers={self.ns, self.ns+':segment'},
            attr_dict={self.ns+':text' : segment_text,
                       'label':  segment_label})

    def __add_relation(self, relation):
        """
            <parRelation id="maz3377.1000" type="sequential">
              <nucleus id="maz3377.1"/>
              <nucleus id="maz3377.2"/>
            </parRelation>
        """
        rel_id = self.ns + ':' + relation.attrib['id']
        rel_name = relation.attrib['type']
        rel_type = relation.tag
        self.add_node(rel_id, layers={self.ns, self.ns+':relation'},
                      attr_dict={self.ns+':rel_name': rel_name,
                                 self.ns+':rel_type': rel_type})

        rel_attrs = {self.ns+':rel_name': rel_name,
                     self.ns+':rel_type': rel_type,
                     'label': self.ns+':'+rel_name}

        if rel_type == 'parRelation':  # relation between two or more nucleii
            for nucleus in relation:
                nucleus_id = self.ns + ':' + nucleus.attrib['id']
                self.add_edge(rel_id, nucleus_id, layers={self.ns},
                              attr_dict=rel_attrs,
                              edge_type=EdgeTypes.spanning_relation)

        elif rel_type == 'hypRelation': # between nucleus and satellite
            hyp_error = ("<hypRelation> can only contain one nucleus and one"
                         "satellite: {}".format(etree.tostring(relation)))

            rel_elems = {elem.tag: elem.attrib['id'] for elem in relation}
            assert len(relation) == 2, hyp_error
            assert set(rel_elems.keys()) == {'nucleus', 'satellite'}, hyp_error

            # add dominance from relation root node to nucleus
            nucleus_id = self.ns + ':' + rel_elems['nucleus']
            self.add_edge(rel_id, nucleus_id, layers={self.ns},
                          attr_dict=rel_attrs,
                          edge_type=EdgeTypes.dominance_relation)

            # add dominance from nucleus to satellite
            satellite_id = self.ns + ':' + rel_elems['satellite']
            self.add_edge(nucleus_id, satellite_id,
                          layers={self.ns}, attr_dict=rel_attrs,
                          edge_type=EdgeTypes.dominance_relation)

        else:  # <relation>, <span>
            raise NotImplementedError

    def __add_token(self, segment_id, segment_token_id, token):
        tok_node_id = '{0}_{1}'.format(segment_id, segment_token_id)
        self.add_node(tok_node_id, layers={self.ns, self.ns+':token'},
                      attr_dict={self.ns+':token': token, 'label': token})
        self.tokens.append(tok_node_id)
        self.add_edge(segment_id, tok_node_id,
                      layers={self.ns, self.ns+':token'},
                      edge_type=EdgeTypes.spanning_relation)


def is_segment_tokenized(segment):
    """Return True, iff the segment is already tokenized.

    Examples
    --------
    >>> s = ('<segment id="1"><sign pos="ART">Die</sign>'
    ...      '<sign pos="NN">Antwort</sign></segment>')
    >>> is_segment_tokenized(seg)
    True

    >>> seg = etree.fromstring('<segment id="1">Die Antwort</segment>')
    >>> is_segment_tokenized(seg)
    False
    """
    return len(segment) > 0


def extract_relationtypes(urml_xml_tree):
    """
    extracts the allowed RST relation names and relation types from
    an URML XML file.

    Parameters
    ----------
    urml_xml_tree : lxml.etree._ElementTree
        lxml ElementTree representation of an URML XML file

    Returns
    -------
    relations : dict of (str, str)
        Returns a dictionary with RST relation names as keys (str)
        and relation types (either 'par' or 'hyp') as values
        (str).
    """
    return {rel.attrib['name']: rel.attrib['type']
            for rel in urml_xml_tree.iterfind('//header/reltypes/rel')
            if 'type' in rel.attrib}


def extract_segment_types(urml_document_element, namespace):
    """Return a map from segment node IDs to their segment type
    ('nucleus', 'satellite' or 'isolated').
    """
    segment_types = \
        {namespace+':'+seg.attrib['id']: seg.tag
         for seg in urml_document_element.iter('nucleus', 'satellite')}

    for seg in urml_document_element.iter('segment'):
        seg_id = namespace+':'+seg.attrib['id']
        if seg_id not in segment_types:
            segment_types[seg_id] = 'isolated'
    return segment_types


# pseudo-function(s) to create a document graph from a URML file
read_urml = URMLCorpus
