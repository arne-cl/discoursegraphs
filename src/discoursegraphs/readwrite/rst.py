#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <arne-neumann@web.de>

"""
This module converts an RS3 XML file into a networkx-based directed
graph.
"""

from __future__ import print_function
import os
import sys
from lxml import etree
from networkx import write_gpickle

from discoursegraphs import DiscourseDocumentGraph


class RSTGraph(DiscourseDocumentGraph):

    """
    A directed graph with multiple edges (based on a networkx
    MultiDiGraph) that represents the rhetorical structure of a
    document.
    """

    def __init__(self, rs3_filepath):
        """
        Creates an RSTGraph from a RS3 XML file and adds metadata to it
        (filename of the RS3 file, names and types of allowed RST
        relations).

        Parameters
        ----------
        rs3_filepath : str
            absolute or relative path to the RS3 file to be parsed

        Attributes
        ----------
        filename : str
            filename of the RS3 file that was parsed
        relations : dict of (str, str)
            dictionary containing all legal RST relations of that file,
            with relation names as keys (str) and relation types
            (either 'rst' or 'multinuc') as values (str).
        segments : list of str
            list of segment node IDs (i.e. leaf nodes in a RST
            tree that represent segments of text).
        tokenized : bool
            False, if the segments represent untokenized text (default).
            True, if the segments have been tokenized (after they were
            imported from an RS3 file) and have outgoing edges to nodes
            representing tokens.
        """
        # super calls __init__() of base class DiscourseDocumentGraph
        super(RSTGraph, self).__init__()
        utf8_parser = etree.XMLParser(encoding="utf-8")
        rs3_xml_tree = etree.parse(rs3_filepath, utf8_parser)

        self.filename = os.path.basename(rs3_filepath)
        self.relations = extract_relationtypes(rs3_xml_tree)
        self.segments = []
        self.tokenized = False

        self.__rst2graph(rs3_xml_tree)

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

        for segment in rst_xml_root.iterfind('./body/segment'):
            segment_node_id = int(segment.attrib['id'])
            self.add_node(segment_node_id,
                          layers={'rst', 'rst:segment'},
                          attr_dict={'rst:text': sanitize_string(segment.text)})

            self.segments.append(segment_node_id)
            if 'parent' in segment.attrib:
                # node has an outgoing edge,
                # i.e. segment is in an RST relation
                parent_node_id = int(segment.attrib['parent'])
                if parent_node_id not in self:  # node not in graph, yet
                    self.add_node(parent_node_id,
                                  layers={'rst', 'rst:segment'})
                self.add_edge(segment_node_id, parent_node_id,
                              layers={'rst', 'rst:relation'},
                              relname=segment.attrib['relname'])

        for group in rst_xml_root.iterfind('./body/group'):
            group_node_id = int(group.attrib['id'])
            node_type = group.attrib['type']
            if group_node_id in self:  # group node already exists
                self.node[group_node_id].update({'rst:reltype': node_type})
            else:
                self.add_node(group_node_id,
                              layers={'rst', 'rst:segment'},
                              attr_dict={'rst:reltype': node_type})

            if 'parent' in group.attrib:
                # node has an outgoing edge, i.e. group is not the
                # topmost element in an RST tree
                parent_node_id = int(group.attrib['parent'])
                if parent_node_id not in self:  # node not in graph, yet
                    self.add_node(parent_node_id,
                                  layers={'rst', 'rst:segment'})
                self.add_edge(group_node_id, parent_node_id,
                              layers={'rst', 'rst:relation'},
                              attr_dict={'rst:relname': group.attrib['relname']})
            else:  # group node is the root of an RST tree
                existing_layers = self.node[group_node_id]['layers']
                all_layers = existing_layers.union({'rst:root'})
                self.node[group_node_id].update({'layers': all_layers})

    def __str__(self):
        """
        string representation of an RSTGraph (contains filename,
        allowed relations and tokenization status).
        """
        ret_str = 'filename: {}\n'.format(self.filename)
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


def sanitize_string(string_or_unicode):
    """
    remove leading/trailing whitespace and always return unicode.
    """
    if isinstance(string_or_unicode, unicode):
        return string_or_unicode.strip()
    else:
        return string_or_unicode.decode('utf-8').strip()


def rst_tokenlist(rst_graph):
    """
    extracts all tokens from an RSTGraph.

    Parameters
    ----------
    rst_graph : RSTGraph
        a directed graph representing an RST tree

    Returns
    -------
    all_rst_tokens : tuple of (unicode, str)
        a list of (str, str) tuples, where the first element is the token
        and the second one is the segment node ID it belongs to.
    """
    all_rst_tokens = []
    for segment_id in rst_graph.segments:
        segment_tokens = [(token, segment_id)
                          for token in rst_graph.node[segment_id]['rst:text'].split()]
        all_rst_tokens.extend(segment_tokens)
    return all_rst_tokens


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.stderr.write('Usage: {0} RS3_input_file '
                         'GraphML_output_file\n'.format(sys.argv[0]))
        sys.exit(1)
    else:
        INPUT_PATH = sys.argv[1]
        OUTPUT_PATH = sys.argv[2]
        assert os.path.isfile(INPUT_PATH)
        RST_GRAPH = RSTGraph(INPUT_PATH)
        write_gpickle(RST_GRAPH, OUTPUT_PATH)
