#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os
import sys
import argparse
from networkx import write_dot

from discoursegraphs.util import ensure_ascii


def generic_converter_cli(docgraph_class, file_descriptor=''):
    """
    generic command line interface for importers. Will convert the file
    specified on the command line into a dot representation of the
    corresponding DiscourseDocumentGraph and write the output to stdout
    or a file specified on the command line.

    Parameters
    ----------
    docgraph_class : class
        a DiscourseDocumentGraph (or a class derived from it), not an
        instance of it!
    file_descriptor : str
        string descring the input format, e.g. 'TigerXML (syntax)'
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file',
                        help='{} file to be converted'.format(file_descriptor))
    parser.add_argument('output_file', nargs='?', default=sys.stdout)
    args = parser.parse_args(sys.argv[1:])

    assert os.path.isfile(args.input_file), \
        "'{}' isn't a file".format(args.input_file)
    docgraph = docgraph_class(args.input_file)
    write_dot(docgraph, args.output_file)


def layerset2list(discoursegraph):
    """
    typecasts all `layers` sets to lists to make the graph
    exportable (e.g. into the `geoff` format or to upload the graph to neo4j).

    Parameters
    ----------
    discoursegraph : DiscourseDocumentGraph
    """
    for node_id in discoursegraph:
        discoursegraph.node[node_id]['layers'] = \
            list(discoursegraph.node[node_id]['layers'])
    for (from_id, to_id) in discoursegraph.edges_iter():
        # there might be multiple edges between 2 nodes
        edge_dict = discoursegraph.edge[from_id][to_id]
        for edge_id in edge_dict:
            edge_dict[edge_id]['layers'] = \
                list(edge_dict[edge_id]['layers'])


def layerset2str(discoursegraph):
    """
    typecasts all `layers` from sets of strings into a single string to make
    the graph exportable (e.g. into the `gexf`, `gml` and `graphml` formats).

    Parameters
    ----------
    discoursegraph : DiscourseDocumentGraph
    """
    for node_id in discoursegraph:
        discoursegraph.node[node_id]['layers'] = \
            str(discoursegraph.node[node_id]['layers'])
    for (from_id, to_id) in discoursegraph.edges_iter():
        # there might be multiple edges between 2 nodes
        edge_dict = discoursegraph.edge[from_id][to_id]
        for edge_id in edge_dict:
            edge_dict[edge_id]['layers'] = \
                str(edge_dict[edge_id]['layers'])


def attriblist2str(discoursegraph):
    """
    converts all node/edge attributes whose values are lists into string
    values (e.g. to export them into the `gexf`, `gml` and `graphml` formats).

    WARNING: This function iterates over all nodes and edges! You can speed up
    conversion by writing a custom function that only fixes those attributes
    that have lists (of strings) as values.

    Parameters
    ----------
    discoursegraph : DiscourseDocumentGraph
    """
    for node_id in discoursegraph:
        node_dict = discoursegraph.node[node_id]
        for attrib in node_dict:
            if isinstance(node_dict[attrib], list):
                node_dict[attrib] = str(node_dict[attrib])
    for (from_id, to_id) in discoursegraph.edges_iter():
        # there might be multiple edges between 2 nodes
        edge_dict = discoursegraph.edge[from_id][to_id]
        for edge_id in edge_dict:
            for attrib in edge_dict[edge_id]:
                if isinstance(edge_dict[edge_id][attrib], list):
                    edge_dict[edge_id][attrib] \
                        = str(edge_dict[edge_id][attrib])


def ensure_ascii_labels(discoursegraph):
    """
    ensure that all node/edge labels are 7-bit latin-1 strings
    (e.g. ``ä`` becomes ``&auml;``). This is necessary for ``gml`` export.

    Parameters
    ----------
    discoursegraph : DiscourseDocumentGraph
    """
    for node_id in discoursegraph:
        label = discoursegraph.node[node_id].get('label')
        if label:
            discoursegraph.node[node_id]['label'] = ensure_ascii(label)
    for (from_id, to_id) in discoursegraph.edges_iter():
        # there might be multiple edges between 2 nodes
        edge_dict = discoursegraph.edge[from_id][to_id]
        for edge_id in edge_dict:
            label = edge_dict[edge_id].get('label')
            if label:
                edge_dict[edge_id]['label'] = ensure_ascii(label)


def ensure_utf8_graph(discoursegraph):
    """
    ensure that all node/edge labels are UTF8 encoded (e.g. to export them
    in `gml` format).

    Parameters
    ----------
    discoursegraph : DiscourseDocumentGraph
    """
    for node_id in discoursegraph:
        node_dict = discoursegraph.node[node_id]
        for attrib in node_dict:
            if isinstance(node_dict[attrib], (str, unicode)):
                node_dict[attrib] = ensure_utf8(node_dict[attrib])
    for (from_id, to_id) in discoursegraph.edges_iter():
        # there might be multiple edges between 2 nodes
        edge_dict = discoursegraph.edge[from_id][to_id]
        for edge_id in edge_dict:
            for attrib in edge_dict[edge_id]:
                if isinstance(edge_dict[edge_id][attrib], (str, unicode)):
                    edge_dict[edge_id][attrib] = ensure_utf8(attrib)
