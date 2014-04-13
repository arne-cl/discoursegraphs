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
import networkx


class RSTGraph(networkx.DiGraph):
    """
    A directed graph (networkx DiGraph) that represents the rhetorical
    structure of a document.
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
        # super calls __init__() of base class DiGraph
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
            self.add_node(segment_node_id, type='segment',
                            text=sanitize_string(segment.text))
            self.segments.append(segment_node_id)
            if 'parent' in segment.attrib:
                # node has an outgoing edge,
                # i.e. segment is in an RST relation
                parent_node_id = int(segment.attrib['parent'])
                self.add_edge(segment_node_id, parent_node_id,
                                relname=segment.attrib['relname'])

        for group in rst_xml_root.iterfind('./body/group'):
            group_node_id = int(group.attrib['id'])
            node_type = group.attrib['type']
            if group_node_id in self.nodes_iter():
                # group node already exists
                self.node[group_node_id].update({'type': node_type})
            else:
                self.add_node(parent_node_id, type=node_type)

            if 'parent' in group.attrib:
                # node has an outgoing edge, i.e. group is not the
                # topmost element in an RST tree
                parent_node_id = int(group.attrib['parent'])
                self.add_edge(group_node_id, parent_node_id,
                                relname=group.attrib['relname'])

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
