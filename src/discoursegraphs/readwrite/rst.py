#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <arne-neumann@web.de>

"""
This module converts an RS3 XML file (used by RSTTool to annotate
rhetorical structure) into a networkx-based directed graph
(``DiscourseDocumentGraph``).
"""

from __future__ import print_function
import os
from lxml import etree

from discoursegraphs import DiscourseDocumentGraph, EdgeTypes
from discoursegraphs.util import sanitize_string
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
            absolute or relative path to the RS3 file to be parsed
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

        utf8_parser = etree.XMLParser(encoding="utf-8")
        rs3_xml_tree = etree.parse(rs3_filepath, utf8_parser)

        self.relations = extract_relationtypes(rs3_xml_tree)
        self.segments = []
        self.tokenized = False
        self.tokens = []

        self.__rst2graph(rs3_xml_tree)

        if tokenize:
            self.__tokenize_segments()
            self.tokenized = True
            if precedence:
                self.add_precedence_relations()

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
        """
        rst_xml_root = rs3_xml_tree.getroot()

        # adds a node to the graph for each RST segment (nucleus or satellite)
        for segment in rst_xml_root.iterfind('./body/segment'):
            segment_node_id = int(segment.attrib['id'])
            self.add_node(
                segment_node_id, layers={self.ns, self.ns+':segment'},
                attr_dict={self.ns+':text': sanitize_string(segment.text)},
                label='{0}:segment:{1}'.format(self.ns, segment.attrib['id']))
            self.segments.append(segment_node_id)

            # adds an edge from the parent node of the segment to the segment
            if 'parent' in segment.attrib:
                # node has an outgoing edge,
                # i.e. segment is in an RST relation
                parent_node_id = int(segment.attrib['parent'])
                # if the parent node is not in graph yet, we'll add it first
                if parent_node_id not in self:
                    self.add_node(parent_node_id,
                                  layers={self.ns, self.ns+':segment'})

                segment_rel = self.relations.get(segment.attrib['relname'],
                                                 'span')
                if segment_rel in ('multinuc', 'span'):
                    from_node = parent_node_id
                    to_node = segment_node_id
                else:  # if segment_rel == 'rst'
                    from_node = segment_node_id
                    to_node = parent_node_id

                self.add_edge(
                    from_node, to_node,
                    layers={self.ns, self.ns+':relation'},
                    attr_dict={self.ns+':relname': segment.attrib['relname'],
                               'label': self.ns+':'+segment.attrib['relname']},
                    edge_type=EdgeTypes.dominance_relation)

        for group in rst_xml_root.iterfind('./body/group'):
            group_node_id = int(group.attrib['id'])
            node_type = group.attrib['type']
            if group_node_id in self:  # group node already exists
                self.node[group_node_id].update(
                    {self.ns+':reltype': node_type,
                     'label': '{0}:group:{1}:{2}'.format(self.ns,
                                                         node_type,
                                                         group_node_id)})
            else:
                self.add_node(
                    group_node_id, layers={self.ns, self.ns+':segment'},
                    attr_dict={self.ns+':reltype': node_type,
                               'label': '{0}:{1}:{2}'.format(self.ns,
                                                             node_type,
                                                             group_node_id)})

            if 'parent' in group.attrib:
                # node has an outgoing edge, i.e. group is not the
                # topmost element in an RST tree
                parent_node_id = int(group.attrib['parent'])
                if parent_node_id not in self:  # node not in graph, yet
                    self.add_node(
                        parent_node_id, layers={self.ns, self.ns+':segment'},
                        label='{0}:{1}'.format(self.ns, parent_node_id))

                group_rel = self.relations.get(group.attrib['relname'], 'span')
                if group_rel in ('multinuc', 'span'):
                    from_node = parent_node_id
                    to_node = group_node_id
                else:  # lif segment_rel == 'rst'
                    from_node = group_node_id
                    to_node = parent_node_id

                self.add_edge(
                    from_node, to_node,
                    layers={self.ns, self.ns+':relation'},
                    attr_dict={self.ns+':relname': group.attrib['relname'],
                               'label': self.ns+':'+group.attrib['relname']},
                    edge_type=EdgeTypes.dominance_relation)

            else:  # group node is the root of an RST tree
                self.root = group_node_id
                existing_layers = self.node[group_node_id]['layers']
                all_layers = existing_layers.union({self.ns+':root'})
                self.node[group_node_id].update(
                    {'layers': all_layers,
                     'label': '{0}:root:{1}'.format(self.ns, group_node_id)})

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
    relations = {}
    for rel in rs3_xml_tree.iterfind('//header/relations/rel'):
        relations[rel.attrib['name']] = rel.attrib['type']
    return relations


if __name__ == '__main__':
    generic_converter_cli(RSTGraph, 'RST (rhetorical structure)')
