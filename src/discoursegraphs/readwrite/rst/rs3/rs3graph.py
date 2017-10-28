#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module converts an RS3 XML file (used by RSTTool to annotate
rhetorical structure) into a networkx-based directed graph
(``DiscourseDocumentGraph``).

Warning: RS3 files considered harmful. Segment IDs appear ordered, but they
aren't. For example, after segment 1, there could be segment 19, followed by
segment 2, 3 and 4 etc.

TODO: merge self.segments into self.edus
"""
from __future__ import print_function
from collections import defaultdict
import os
import sys

from lxml import etree

from discoursegraphs.util import (get_segment_token_offsets, natural_sort_key,
                                  sanitize_string, TokenMapper)
from discoursegraphs import (DiscourseDocumentGraph, EdgeTypes, get_span,
                             istoken, select_neighbors_by_layer)
from discoursegraphs.readwrite.generic import generic_converter_cli
from discoursegraphs.readwrite.rst.common import get_segment_label
from discoursegraphs.readwrite.rst.rs3 import extract_relationtypes


class RSTGraph(DiscourseDocumentGraph):
    """
    A directed graph with multiple edges (based on a networkx
    MultiDiGraph) that represents the rhetorical structure of a
    document. It is generated from a *.rs3 file.

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
    def __init__(self, rs3_filepath=None, name=None, namespace='rst',
                 tokenize=True, precedence=False):
        """
        Creates an RSTGraph from a RS3 XML file and adds metadata to it
        (filename of the RS3 file, names and types of allowed RST
        relations).

        Parameters
        ----------
        rs3_filepath : str or None
            Absolute or relative path to the RS3 file to be parsed.
            If no path is given, return an empty RSTGraph.
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
        super(RSTGraph, self).__init__(namespace=namespace)

        self.ns = namespace
        if not rs3_filepath:
            return  # create empty document graph

        self.name = name if name else os.path.basename(rs3_filepath)

        # __rst2graph() will find/set the root node later on

        self.segments = []
        self.tokenized = False
        self.tokens = []
        self.edus = []

        utf8_parser = etree.XMLParser(encoding="utf-8")
        rs3_xml_tree = etree.parse(rs3_filepath, utf8_parser)
        self.relations = extract_relationtypes(rs3_xml_tree)
        self.__rst2graph(rs3_xml_tree)

        if tokenize:
            self.__tokenize_segments()
            self.tokenized = True
            if precedence:
                self.add_precedence_relations()

        # the nodes representing EDUs (elementary discourse units)
        # will be stored here (to keep them even after merging graphs)
        if self.ns+':edus' not in self.node[self.root]['metadata']:
            self.node[self.root]['metadata'][self.ns+':edus'] = self.edus

    def __rst2graph(self, rs3_xml_tree):
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
        doc_root = rs3_xml_tree.getroot()

        for segment in doc_root.iter('segment'):
            self.__add_segment(segment)
        for group in doc_root.iter('group'):
            self.__add_group(group)

    def __add_segment(self, segment):
        """
        add attributes to segment nodes, as well as edges to/from other
        segments/groups. add segment to list of EDUs.

        Parameters
        ----------
        segment : ??? etree Element
        """
        segment_id = self.ns+':'+segment.attrib['id']
        self.segments.append(segment_id)
        segment_type, parent_segment_type = self.__get_segment_types(segment)
        segment_text = sanitize_string(segment.text)
        segment_label = get_segment_label(
            segment, segment_type, segment_text, self.ns, self.tokenized)

        self.add_node(
            segment_id, layers={self.ns, self.ns+':segment'},
            attr_dict={'label': segment_label,
                       self.ns+':text' : segment_text,
                       self.ns+':segment_type': segment_type})

        # store RST segment in list of EDUs
        self.edus.append(segment_id)

        if 'parent' in segment.attrib:
            self.__add_parent_relation(segment, segment_id, segment_type,
                                       parent_segment_type)

    def __add_group(self, group):
        """
        add attributes to group nodes, as well as in-edges from other
        groups. a group's ``type`` attribute tells us whether the group
        node represents a span (of RST segments or other groups) OR
        a multinuc(ular) relation (i.e. it dominates several RST nucleii).

        a group's ``relname`` gives us the name of the relation between
        the group node and the group's parent node.

        Parameters
        ----------
        group : ??? etree Element
        """
        group_id = self.ns+':'+group.attrib['id']
        group_type = group.attrib['type']  # 'span' or 'multinuc'
        group_layers = {self.ns, self.ns+':group'}
        segment_type, parent_segment_type = self.__get_segment_types(group)

        group_attrs = \
            {self.ns+':group_type': group_type,
             'label': '{0}:group:{1}:{2}'.format(self.ns, group_type,
                                                 group.attrib['id'])}

        if group_id not in self:  # group node doesn't exist, yet
            group_attrs[self.ns+':segment_type'] = segment_type
            self.add_node(group_id, layers=group_layers,
                          attr_dict=group_attrs)
        else: # group node does already exist
            if segment_type != 'span':  # if it is an RST relation
                group_attrs[self.ns+':segment_type'] = segment_type
            else: # segment_type == 'span'
                # if the group already has a segment type, we won't overwrite
                # it, since 'span' is not very informative
                if not self.ns+':segment_type' in self.node[group_id]:
                    group_attrs[self.ns+':segment_type'] = segment_type
            self.node[group_id].update(group_attrs,
                                       layers={self.ns, self.ns+':group'})

        if 'parent' not in group.attrib:  # mark group as RST root node
            # each discourse docgraphs has a default root node, but we will
            # overwrite it here
            old_root_id = self.root
            self.root = group_id
            # workaround for #141: the layers attribute is append-only,
            # but here we're updating it as a part of the attribute dict
            #
            # root segment type: always span
            root_attrs = {'layers': {self.ns, self.ns+':root'},
                          self.ns+':segment_type': 'span'}
            self.node[group_id].update(root_attrs)
            # copy metadata from old root node
            self.node[group_id]['metadata'] = self.node[old_root_id]['metadata']
            # finally, remove the old root node
            self.remove_node(old_root_id)
        else:  # the group node is dominated by another group or segment
            self.__add_parent_relation(group, group_id, segment_type,
                                       parent_segment_type)

    def __add_parent_relation(self, element, element_id, segment_type, parent_segment_type):
        """
        - add parent node (if not there, yet) w/ segment type
        - add edge from parent node to current element
        """
        relname = element.attrib['relname'] # name of RST relation or 'span'
        reltype = self.relations.get(relname, '') # 'span', 'multinuc' or ''

        parent_id = self.ns+':'+element.attrib['parent']

        if parent_segment_type:
            parent_attrs = {self.ns+':rel_name': relname,
                            self.ns+':segment_type': parent_segment_type}
        else: # e.g. if the parent is a root node of a multinuc, we don't
              # know what its segment type is
            parent_attrs = {self.ns+':rel_name': relname}

        if parent_id not in self:
            self.add_node(parent_id, layers={self.ns}, attr_dict=parent_attrs)
        else:
            if segment_type != 'span':
                self.node[parent_id].update(parent_attrs)

        if segment_type == 'span':
            edge_type = EdgeTypes.spanning_relation
        else:
            edge_type = EdgeTypes.dominance_relation

        rel_attrs = {self.ns+':rel_name': relname, self.ns+':rel_type': reltype,
                     'label': self.ns+':'+relname}
        self.add_edge(parent_id, element_id, layers={self.ns},
                      attr_dict=rel_attrs, edge_type=edge_type)


    def __get_segment_types(self, element):
        """
        given a <segment> or <group> element, returns its segment type and the
        segment type of its parent (i.e. its dominating node)

        Parameters
        ----------
        element : ??? etree Element

        Returns
        -------
        segment_type : str
            'nucleus', 'satellite' or 'isolated' (unconnected segment, e.g. a
            news headline) or 'span' (iff the segment type is currently
            unknown -- i.e. ``relname`` is ``span``)
        parent_segment_type : str or None
            'nucleus', 'satellite' or None (e.g. for the root group node)
        """
        if not 'parent' in element.attrib:
            if element.tag == 'segment':
                segment_type = 'isolated'
                parent_segment_type = None
            else:  # element.tag == 'group'
                segment_type = 'span'
                parent_segment_type = None
            return segment_type, parent_segment_type

        # ``relname`` either contains the name of an RST relation or
        # the string ``span`` (iff the segment is dominated by a span
        # node -- a horizontal line spanning one or more segments/groups
        # in an RST diagram). ``relname`` is '', if the segment is
        # unconnected.
        relname = element.attrib.get('relname', '')
        # we look up, if ``relname`` represents a regular, binary RST
        # relation or a multinucular relation. ``reltype`` is '',
        # if ``relname`` is ``span`` (i.e. a span isn't an RST relation).
        reltype = self.relations.get(relname, '')

        if reltype == 'rst':
            segment_type = 'satellite'
            parent_segment_type = 'nucleus'
        elif reltype == 'multinuc':
            segment_type = 'nucleus'
            parent_segment_type = None # we don't know it's type, yet
        else:  # reltype == ''
            # the segment is of unknown type, it is dominated by
            # a span group node
            segment_type = 'span'
            parent_segment_type = 'span'
        return segment_type, parent_segment_type


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


def get_edus(rst_graph, namespace='rst'):
    """
    returns the elementary discourse units (EDUs) in the order they occur
    in the document.

    Parameters
    ----------
    rst_graph : RSTGraph
        a document graph representing an RS3 file
    namespace : str
        the namespace that contains the EDUs (default: 'rst')

    Returns
    -------
    edus : list of str
        a list of node IDs of RST segments (EDUs) in the order they occur
        in the RS3 file
    """
    return rst_graph.node[rst_graph.root]['metadata'][namespace+':edus']


def get_rst_relation_root_nodes(docgraph, data=True, rst_namespace='rst'):
    """
    yield all nodes that dominate one or more RST relations in the given
    document graph (in no particular order).

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
        if rel_attr in node_attrs and node_attrs[rel_attr] != 'span':
            yield (node_id, node_attrs[rel_attr], get_span(docgraph, node_id)) \
                if data else (node_id)


def get_rst_relations(docgraph):
    """
    returns a dictionary with RST relation root node IDs (str, e.g. 'rst:23')
    as keys and dictionaries describing these RST relations as values.

    Parameters
    ----------
    docgraph : DiscourseDocumentGraph
        a document graph which contains RST annotations

    Returns
    -------
    rst_relations : defaultdict(str)
        possible keys: 'tokens', 'nucleus', 'satellites', 'multinuc'
        maps from an RST relation root node ID (str, e.g. 'rst:23') to a
        dictionary describing this RST relation.
        The key 'tokens' maps to a list of token (node IDs) which the relation
        spans.
        If the dictionary contains the key 'multinuc', the relation is
        multinuclear and the keys 'nucleus' and 'satellites' contain nothing.
        The key 'multinuc' maps to a list of
        (node ID (str), RST reltype (str), list of token node IDs) triples;
        each one describes a nucleus.
        The key 'nucleus' maps to a list of token (node IDs) which the relation
        spans.
        The key 'satellites' maps to a list of
        (node ID (str), RST reltype (str), list of token node IDs) triples;
        each one describes a satellite.
    """
    rst_relations = defaultdict(lambda: defaultdict(str))

    for dom_node, _, _ in get_rst_relation_root_nodes(docgraph):
        neighbors = \
            list(select_neighbors_by_layer(docgraph, dom_node,
                                           layer={'rst:segment', 'rst:group'}))
        multinuc_nuc_count = 1
        directly_dominated_tokens = sorted([node for node in docgraph.neighbors(dom_node)
                                            if istoken(docgraph, node)], key=natural_sort_key)
        if directly_dominated_tokens:
            rst_relations[dom_node]['tokens'] = directly_dominated_tokens

        for neighbor in neighbors:
            for edge in docgraph[dom_node][neighbor]:  # multidigraph
                edge_attrs = docgraph[dom_node][neighbor][edge]

                if edge_attrs['edge_type'] == EdgeTypes.spanning_relation:
                    # a span always signifies the nucleus of a relation
                    # there can be only one
                    rst_relations[dom_node]['nucleus'] = (neighbor, get_span(docgraph, neighbor))
                elif edge_attrs['rst:rel_type'] == 'rst':
                    # a segment/group nucleus can dominate multiple satellites
                    # (in different RST relations)
                    satellite = (neighbor, edge_attrs['rst:rel_name'], get_span(docgraph, neighbor))
                    if 'satellites' in rst_relations[dom_node]:
                        rst_relations[dom_node]['satellites'].append(satellite)
                    else:
                        rst_relations[dom_node]['satellites'] = [satellite]
                elif edge_attrs['rst:rel_type'] == 'multinuc':
                    nucleus = (neighbor, edge_attrs['rst:rel_name'], get_span(docgraph, neighbor))
                    if 'multinuc' in rst_relations[dom_node]:
                        rst_relations[dom_node]['multinuc'].append(nucleus)
                    else:
                        rst_relations[dom_node]['multinuc'] = [nucleus]
                    multinuc_nuc_count += 1
                else:
                    raise NotImplementedError("unknown type of RST segment domination")
    return rst_relations


def get_rst_spans(rst_graph):
    """
    Returns a list of 5-tuples describing each RST span (i.e. the nucleus
    or satellite of a relation) in the document. (This function is meant for
    people who prefer to work with R / DataFrames / CSV files instead of
    graphs.)

    Parameters
    ----------
    docgraph : DiscourseDocumentGraph
        a document graph which contains RST annotations

    Returns
    -------
    all_spans : list of (str, str, str, int, int)
        each list element represents an RST span (i.e. the nucleus or satellite)
        as a 5-tuple
        (relation string, span type, relation type, token onset, token offset).
        In the example ('rst:16-rst:2', 'N', 'evaluation-s', 9, 24), the
        relation string 'rst:16-rst:2' consists of two parts, the relation root
        node ID and the node ID of its nucleus (span type 'N').
        In the example ('rst:16-rst:4-rst:3', 'N1', 'list', 20, 24), the
        relation string consists of 3 parts, the relation root
        node ID and the node IDs of its nucleii (span type 'N1', 'N2').

    Examples
    --------
        [('rst:16-rst:4-rst:3', 'N1', 'list', 20, 24),
        ('rst:16-rst:4-rst:3', 'N2', 'list', 9, 19),
        ('rst:16-rst:2', 'N', 'evaluation-s', 9, 24),
        ('rst:16-rst:2', 'S', 'evaluation-s', 4, 8)]
    """
    token_map = TokenMapper(rst_graph).id2index
    rst_relations = get_rst_relations(rst_graph)
    all_spans = []
    for dom_node in rst_relations:
        if 'multinuc' in rst_relations[dom_node]:
            nuc_count = 1
            multinuc_start, multinuc_end = sys.maxint, 0
            multinuc_spans = rst_relations[dom_node]['multinuc']
            multinuc_rel_id = "{0}-{1}".format(
                dom_node, '-'.join(target for target, _rel, _toks in multinuc_spans))

            for _, relname, toks in multinuc_spans:
                nuc_start, nuc_end = get_segment_token_offsets(toks, token_map)
                multinuc_span = (multinuc_rel_id, "N{}".format(nuc_count),
                                 relname, nuc_start, nuc_end)
                all_spans.append(multinuc_span)
                nuc_count += 1
                # determine the token offsets of the whole multinuc relation iteratively
                if nuc_start < multinuc_start:
                    multinuc_start = nuc_start
                if nuc_end > multinuc_end:
                    multinuc_end = nuc_end

        if 'satellites' in rst_relations[dom_node]:
            # find the nucleus
            if 'nucleus' in rst_relations[dom_node]:
                nuc_id, nuc_toks = rst_relations[dom_node]['nucleus']
                nuc_start, nuc_end = get_segment_token_offsets(nuc_toks, token_map)
            elif 'multinuc' in rst_relations[dom_node]:
                nuc_id = dom_node # multinuc as a whole is the nucleus
                nuc_start, nuc_end = multinuc_start, multinuc_end
            elif 'tokens' in rst_relations[dom_node]:
                nuc_id = dom_node # dominating segment node directly dominates these tokens
                nuc_start, nuc_end = get_segment_token_offsets(
                    rst_relations[dom_node]['tokens'], token_map)
            else:
                raise ValueError(
                    "Can't find a nucleus for these satellites: {}".format(
                        rst_relations[dom_node]['satellites']))

            sat_spans = rst_relations[dom_node]['satellites']
            for satellite, relname, sat_toks in sat_spans:
                sat_start, sat_end = get_segment_token_offsets(sat_toks, token_map)
                nucleus_span = ("{0}-{1}".format(nuc_id, satellite), 'N',
                                relname, nuc_start, nuc_end)
                all_spans.append(nucleus_span)
                satellite_span = ("{0}-{1}".format(nuc_id, satellite), 'S',
                                  relname, sat_start, sat_end)
                all_spans.append(satellite_span)
    return all_spans


# pseudo-function(s) to create a document graph from a RST (.rs3) file
read_rst = read_rs3 = RSTGraph


if __name__ == '__main__':
    generic_converter_cli(RSTGraph, 'RST (rhetorical structure)')
