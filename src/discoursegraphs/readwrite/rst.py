#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module converts an RS3 XML file (used by RSTTool to annotate
rhetorical structure) into a networkx-based directed graph
(``DiscourseDocumentGraph``).
"""

from __future__ import print_function
import os
from lxml import etree

from discoursegraphs import DiscourseDocumentGraph, EdgeTypes, get_span, istoken, select_neighbors_by_layer
from discoursegraphs.util import sanitize_string, natural_sort_key
from discoursegraphs.readwrite.generic import generic_converter_cli


class RSTGraph(DiscourseDocumentGraph):
    """
    A directed graph with multiple edges (based on a networkx
    MultiDiGraph) that represents the rhetorical structure of a
    document.

    Attributes
    ----------
    name : str
        name, ID of the document or file name of the input file
    ns : str
        the namespace of the document (default: rst)
    relations : dict of (str, str)
        dictionary containing all legal RST relations of that file,
        with relation names as keys (str) and relation types
        (either 'rst' or 'multinuc') as values (str).
    segments : list of str
        list of segment node IDs (i.e. leaf nodes in a RST
        tree that represent segments of text).
    root : str
        name of the document root node ID
    tokens : list of str
        sorted list of all token node IDs contained in this document graph
    tokenized : bool
        True (default), if the segments have been tokenized (after they were
        imported from an RS3 file) and have outgoing edges to nodes
        representing tokens.
        False, if the segments represent untokenized text.
    """
    def __init__(self, rs3_filepath, name=None, namespace='rst',
                 tokenize=True, precedence=False):
        """
        Creates an RSTGraph from a RS3 XML file and adds metadata to it
        (filename of the RS3 file, names and types of allowed RST
        relations).

        Parameters
        ----------
        rs3_filepath : str
            absolute or relative path to the RS3 file to be parsed.
        name : str or None
            the name or ID of the graph to be generated. If no name is
            given, the basename of the input file is used.
        namespace : str
            the namespace of the document (default: rst)
        tokenize : bool
            If True, the RST segments (i.e. nuclei and satellites) will
            be tokenized and added as additonal token nodes to the
            document graph (with edges from the respective RST segments).
        precedence : bool
            If True (and if tokenize == True), add precedence relation edges
            (root precedes token1, which precedes token2 etc.)
        """
        # super calls __init__() of base class DiscourseDocumentGraph
        super(RSTGraph, self).__init__()

        self.name = name if name else os.path.basename(rs3_filepath)
        self.ns = namespace
        self.root = None  # __rst2graph() will find/set the root node

        self.segments = []
        self.tokenized = False
        self.tokens = []

        utf8_parser = etree.XMLParser(encoding="utf-8")
        rs3_xml_tree = etree.parse(rs3_filepath, utf8_parser)
        self.relations = extract_relationtypes(rs3_xml_tree)
        self.__rst2graph(rs3_xml_tree, tokenize)

        if tokenize:
            self.__tokenize_segments()
            self.tokenized = True
            if precedence:
                self.add_precedence_relations()

    def __rst2graph(self, rs3_xml_tree, tokenize):
        """
        Reads an RST tree (from an ElementTree representation of an RS3
        XML file) and adds all segments (nodes representing text) and
        groups (nonterminal nodes in an RST tree) as well as the
        relationships that hold between them (typed edges) to this
        RSTGraph.

        Parameters
        ----------
        rs3_xml_tree : lxml.etree._ElementTree
            lxml ElementTree representation of an RS3 XML file
        tokenize : bool
            If True, the RST segments (i.e. nuclei and satellites) will
            be tokenized and added as additonal token nodes to the
            document graph (with edges from the respective RST segments).
            If False, each RST segment will be labeled with the text it
            represents.
        """
        rst_root = rs3_xml_tree.getroot()

        # the rs3 format is weird. in order to determine edge directionality,
        # we'll mark all nodes as being either a ``segment`` (nucleus or
        # satellite) or a ``group`` (span of segments/groups or a multinucular
        # relation between two or more groups or segments).
        for element in rst_root.iter('segment', 'group'):
            element_id = self.ns+':'+element.attrib['id']
            self.add_node(element_id, layers={self.ns, self.ns+':'+element.tag},
                          attr_dict={self.ns+':rel_name': ''})

        # add attributes to segment nodes, as well as edges to/from other
        # segments/groups
        for segment in rst_root.iter('segment'):
            segment_id = self.ns+':'+segment.attrib['id']
            self.segments.append(segment_id)
            segment_text = sanitize_string(segment.text)

            relname = segment.attrib.get('relname')
            reltype = self.relations.get(relname)
            if not relname:
                # an isolated segment, e.g. a news headline
                segment_type = 'isolated'
            else:  # determine nucleus/span by the relation type
                if reltype == 'rst':
                    segment_type = 'satellite'
                    parent_segment_type = 'nucleus'
                elif reltype == 'multinuc':
                   segment_type = 'nucleus'
                   parent_segment_type = 'nucleus'
                else:  # reltype == None
                    pass  # no meaningful segment type

            if tokenize:
                segment_label = u'[{0}]:{1}:segment:{2}'.format(
                    segment_type[0], self.ns, segment.attrib['id'])
            else:
                # if the graph is not tokenized, put (the beginning of) the
                # segment's text into its label
                segment_label = u'[{0}]:{1}: {2}...'.format(
                    segment_type[0], segment.attrib['id'], segment_text[:20])

            if reltype or segment_type == 'isolated':
                self.node[segment_id].update({self.ns+':text': segment_text,
                                              'label': segment_label,
                                              self.ns+':segment_type': segment_type})
            else:
                self.node[segment_id].update({self.ns+':text': segment_text,
                                              'label': segment_label})

            # skip to the next segment, if the node has no in/outgoing edge,
            # (this often happens when annotating news headlines)
            if 'parent' not in segment.attrib:
                continue

            parent_id = self.ns+':'+segment.attrib['parent']
            # we'll search dominating nodes for their RST relations, so we'll
            # have to add this information to the parent node
            if relname != 'span':  # if it is an RST relation
                self.node[parent_id].update({self.ns+':rel_name': relname,
                                             self.ns+':segment_type': parent_segment_type})

            edge_type = EdgeTypes.dominance_relation if relname != 'span' else EdgeTypes.spanning_relation
            self.add_edge(parent_id, segment_id, layers={self.ns},
                          attr_dict={self.ns+':rel_name': relname,
                                     'label': self.ns+':'+relname},
                          edge_type=edge_type)

        # add attributes to group nodes, as well as in-edges from other
        # groups
        for group in rst_root.iter('group'):
            group_id = self.ns+':'+group.attrib['id']
            group_type = group.attrib['type']  # 'span' or 'multinuc'

            self.node[group_id].update(
                {self.ns+':group_type': group_type,
                 'label': '{0}:group:{1}:{2}'.format(self.ns, group_type,
                                                     group.attrib['id'])})

            if 'parent' not in group.attrib:  # mark group as RST root node
                self.root = group_id
                existing_layers = self.node[group_id]['layers']
                all_layers = existing_layers.union({self.ns+':root'})
                self.node[group_id].update(
                    {'layers': all_layers,
                     'label': '{0}:root:{1}'.format(self.ns, group_id)})
            else:
                parent_id = self.ns+':'+group.attrib['parent']
                relname = group.attrib['relname']
                # type of the relation, i.e. 'span', 'multinuc' or 'rst'
                reltype = self.relations.get(relname, 'span')

                # determine nucleus/span by the relation type
                if reltype == 'rst':
                    segment_type = 'satellite'
                    parent_segment_type = 'nucleus'
                elif reltype == 'multinuc':
                   segment_type = 'nucleus'
                   parent_segment_type = 'nucleus'
                else:  # reltype == 'span'
                    pass

                # we'll search dominating nodes for their RST relations, so we'll
                # have to add this information to the parent node
                if relname != 'span':  # if it is an RST relation
                    self.node[group_id].update({self.ns+':segment_type': segment_type})
                    self.node[parent_id].update({self.ns+':rel_name': relname,
                                                 self.ns+':segment_type': parent_segment_type})

                edge_type = EdgeTypes.dominance_relation if relname != 'span' else EdgeTypes.spanning_relation
                self.add_edge(
                    parent_id, group_id, layers={self.ns, self.ns+':relation'},
                    attr_dict={self.ns+':rel_name': relname,
                               self.ns+':rel_type': reltype,
                               'label': self.ns+':'+relname},
                    edge_type=edge_type)

    def __tokenize_segments(self):
        """
        tokenizes every RS3 segment (i.e. an RST nucleus or satellite).
        for each token, a node is added to the graph, as well as an edge from
        the segment node to the token node. the token node IDs are also added
        to ``self.tokens``.
        """
        for seg_node_id in self.segments:
            segment_toks = self.node[seg_node_id][self.ns+':text'].split()
            for i, tok in enumerate(segment_toks):
                tok_node_id = '{0}:{1}_{2}'.format(self.ns, seg_node_id, i)
                self.add_node(tok_node_id, layers={self.ns, self.ns+':token'},
                              attr_dict={self.ns+':token': tok, 'label': tok})
                self.tokens.append(tok_node_id)
                self.add_edge(seg_node_id, tok_node_id,
                              layers={'rst', 'rst:token'},
                              edge_type=EdgeTypes.spanning_relation)

    def __str__(self):
        """
        string representation of an RSTGraph (contains filename,
        allowed relations and tokenization status).
        """
        ret_str = '(file) name: {}\n'.format(self.name)
        ret_str += 'number of segments: {}\n'.format(len(self.segments))
        ret_str += 'is tokenized: {}\n'.format(self.tokenized)
        ret_str += 'allowed relations: {}\n'.format(self.relations)
        return ret_str


def extract_relationtypes(rs3_xml_tree):
    """
    extracts the allowed RST relation names and relation types from
    an RS3 XML file.

    Parameters
    ----------
    rs3_xml_tree : lxml.etree._ElementTree
        lxml ElementTree representation of an RS3 XML file

    Returns
    -------
    relations : dict of (str, str)
        Returns a dictionary with RST relation names as keys (str)
        and relation types (either 'rst' or 'multinuc') as values
        (str).
    """
    return {rel.attrib['name']: rel.attrib['type']
            for rel in rs3_xml_tree.iterfind('//header/relations/rel')}


def get_rst_relations(docgraph, data=True, rst_namespace='rst'):
    """
    yield all RST relations that occur in the given document graph.

    Parameters
    ----------
    docgraph : DiscourseDocumentGraph
        a document graph which contains RST annotations
    data : bool
        If True (default), yields (node ID, relation name, list of tokens)
        tuples. If False, yields just node IDs.
    rst_namespace : str
        The namespace that the RST annotations use (default: rst)

    Yields
    ------
    relations : str or (str, str, list of str) tuples
        If data=False, this will just yield node IDs of the nodes that
        directly dominate an RST relation. If data=True, this yields
        tuples of the form: (node ID, relation name, list of tokens that this
        relation spans).
    """
    rel_attr = rst_namespace+':rel_name'
    for node_id, node_attrs in docgraph.nodes_iter(data=True):
        if node_attrs.get(rel_attr):  # if rel_attr in node_attrs and is not empty
            yield (node_id, node_attrs[rel_attr], get_span(docgraph, node_id)) if data else (node_id)


def get_segment_spans_from_rst_relation(docgraph, relation_id, rst_namespace='rst'):
    spans = {}

    if rst_namespace+':segment' in docgraph.node[relation_id]['layers']:
        nuc_tok_ids = sorted([node for node in docgraph.neighbors(relation_id)
                              if istoken(docgraph, node)], key=natural_sort_key)
        spans['N'] = nuc_tok_ids

        # a nucleus segment can only dominate one other segment/group
        satellite = list(select_neighbors_by_layer(docgraph, relation_id, {'rst:segment', 'rst:group'}))[0]
        spans['S'] = get_span(docgraph, satellite)
        return spans

    else:  # dominating node (relation ID) is a <group>
        group_type = docgraph.node[relation_id][rst_namespace+':group_type']
        nucleus_count = 1
        for neighbor in select_neighbors_by_layer(docgraph, relation_id,
                                                  {rst_namespace+':segment', rst_namespace+':group'}):
            neighbor_type = docgraph.node[neighbor][rst_namespace+':segment_type']

            if neighbor_type == 'nucleus':
                if group_type == 'multinuc':
                    spans['N{}'.format(nucleus_count)] = get_span(docgraph, neighbor)
                    nucleus_count += 1
                else:
                    spans['N'] = get_span(docgraph, neighbor)
            else:  # neighbor_type == 'span'
                spans['S'] = get_span(docgraph, neighbor)
        return spans


if __name__ == '__main__':
    generic_converter_cli(RSTGraph, 'RST (rhetorical structure)')
