#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
The ``merging`` module combines several document graphs into one.
So far, it is able to merge rhetorical structure theory (RS3), syntax
(TigerXML) and anaphora (ad-hoc format) annotations of the same document.
"""

import os
import sys
import argparse
from networkx import write_dot

from discoursegraphs.readwrite.anaphoricity import AnaphoraDocumentGraph
from discoursegraphs.readwrite.rst import RSTGraph
from discoursegraphs.readwrite.tiger import TigerDocumentGraph
from discoursegraphs.readwrite.conano import ConanoDocumentGraph
from discoursegraphs.readwrite.mmax2 import MMAXDocumentGraph
from discoursegraphs.readwrite.neo4j import convert_to_geoff, upload_to_neo4j


def merging_cli():
    """
    simple commandline interface of the merging module.

    This function is called when you use the ``discoursegraphs`` application
    directly on the command line.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('-t', '--tiger-file',
                        help='TigerXML (syntax) file to be merged')
    parser.add_argument('-r', '--rst-file',
                        help='RS3 (rhetorical structure) file to be merged')
    parser.add_argument('-a', '--anaphoricity-file',
                        help='anaphoricity file to be merged')
    parser.add_argument('-c', '--conano-file',
                        help='conano file to be merged')
    parser.add_argument('-m', '--mmax-file',
                        help='MMAX2 file to be merged')
    parser.add_argument('-o', '--output-format',
                        default='dot',
                        help='output format: dot, pickle, geoff, neo4j, no-output')
    parser.add_argument('output_file', nargs='?', default=sys.stdout)

    args = parser.parse_args(sys.argv[1:])

    assert args.tiger_file, \
        "You'll need to provide at least a TigerXML file."

    for filepath in (args.tiger_file, args.rst_file, args.anaphoricity_file,
                     args.conano_file):
        if filepath:  # if it was specified on the command line
            assert os.path.isfile(filepath), \
                "File '{}' doesn't exist".format(filepath)

    tiger_docgraph = TigerDocumentGraph(args.tiger_file)

    if args.rst_file:
        rst_graph = RSTGraph(args.rst_file)
        tiger_docgraph.merge_graphs(rst_graph)

    if args.anaphoricity_file:
        anaphora_graph = AnaphoraDocumentGraph(args.anaphoricity_file)
        tiger_docgraph.merge_graphs(anaphora_graph)
        # the anaphora doc graph only contains trivial edges from its root
        # node.
        try:
            tiger_docgraph.remove_node('anaphoricity:root_node')
        except:
            pass

    if args.conano_file:
        conano_graph = ConanoDocumentGraph(args.conano_file)
        tiger_docgraph.merge_graphs(conano_graph)

    if args.mmax_file:
        mmax_graph = MMAXDocumentGraph(args.mmax_file)
        tiger_docgraph.merge_graphs(mmax_graph)

    if args.output_format == 'dot':
        write_dot(tiger_docgraph, args.output_file)
    elif args.output_format == 'pickle':
        import cPickle as pickle
        with open(args.output_file, 'wb') as pickle_file:
            pickle.dump(tiger_docgraph, pickle_file)
    elif args.output_format == 'geoff':
        args.output_file.write(convert_to_geoff(tiger_docgraph))
        print ''
    elif args.output_format == 'neo4j':
        import requests
        try:
            upload_to_neo4j(tiger_docgraph)
        except requests.exceptions.ConnectionError as e:
            sys.stderr.write(
                ("Can't upload graph to Neo4j server. "
                 "Is it running?\n{}\n".format(e)))
    elif args.output_format == 'no-output':
        pass  # just testing if the merging works
    else:
        raise ValueError(
            "Unsupported output format: {}".format(args.output_format))


if __name__ == '__main__':
    merging_cli()
