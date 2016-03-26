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

import discoursegraphs as dg
from discoursegraphs import DiscourseDocumentGraph, write_dot
from discoursegraphs.util import create_dir


def merging_cli(debug=False):
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
    parser.add_argument(
        '-o', '--output-format', default='dot',
        help=('output format: brackets, brat, dot, pickle, geoff, gexf, graphml, '
              'neo4j, exmaralda, conll, paula, no-output'))
    parser.add_argument('output_file', nargs='?', default=sys.stdout)

    args = parser.parse_args(sys.argv[1:])

    for filepath in (args.tiger_file, args.rst_file, args.anaphoricity_file,
                     args.conano_file):
        if filepath:  # if it was specified on the command line
            assert os.path.isfile(filepath), \
                "File '{}' doesn't exist".format(filepath)

    # create an empty document graph. merge it with other graphs later on.
    discourse_docgraph = DiscourseDocumentGraph()

    if args.tiger_file:
        from discoursegraphs.readwrite.tiger import TigerDocumentGraph
        tiger_docgraph = TigerDocumentGraph(args.tiger_file)
        discourse_docgraph.merge_graphs(tiger_docgraph)

    if args.rst_file:
        rst_graph = dg.read_rs3(args.rst_file)
        discourse_docgraph.merge_graphs(rst_graph)

    if args.anaphoricity_file:
        from discoursegraphs.readwrite import AnaphoraDocumentGraph
        anaphora_graph = AnaphoraDocumentGraph(args.anaphoricity_file)
        discourse_docgraph.merge_graphs(anaphora_graph)
        # the anaphora doc graph only contains trivial edges from its root
        # node.
        try:
            discourse_docgraph.remove_node('anaphoricity:root_node')
        except networkx.NetworkXError as e:  # ignore if the node doesn't exist
            pass

    if args.conano_file:
        from discoursegraphs.readwrite import ConanoDocumentGraph
        conano_graph = ConanoDocumentGraph(args.conano_file)
        discourse_docgraph.merge_graphs(conano_graph)

    if args.mmax_file:
        from discoursegraphs.readwrite import MMAXDocumentGraph
        mmax_graph = MMAXDocumentGraph(args.mmax_file)
        discourse_docgraph.merge_graphs(mmax_graph)

    if isinstance(args.output_file, str):  # if we're not piping to stdout ...
        # we need abspath to handle files in the current directory
        path_to_output_file = \
            os.path.dirname(os.path.abspath(args.output_file))
        if not os.path.isdir(path_to_output_file):
            create_dir(path_to_output_file)

    if args.output_format == 'dot':
        write_dot(discourse_docgraph, args.output_file)
    elif args.output_format == 'brat':
        dg.write_brat(discourse_docgraph, args.output_file)
    elif args.output_format == 'brackets':
        dg.write_brackets(discourse_docgraph, args.output_file)
    elif args.output_format == 'pickle':
        import cPickle as pickle
        with open(args.output_file, 'wb') as pickle_file:
            pickle.dump(discourse_docgraph, pickle_file)
    elif args.output_format in ('geoff', 'neo4j'):
        from discoursegraphs.readwrite.neo4j import write_geoff
        write_geoff(discourse_docgraph, args.output_file)
        print ''  # this is just cosmetic for stdout
    elif args.output_format == 'gexf':
        dg.write_gexf(discourse_docgraph, args.output_file)
    elif args.output_format == 'graphml':
        dg.write_graphml(discourse_docgraph, args.output_file)
    elif args.output_format == 'exmaralda':
        from discoursegraphs.readwrite.exmaralda import write_exb
        write_exb(discourse_docgraph, args.output_file)
    elif args.output_format == 'conll':
        from discoursegraphs.readwrite.conll import write_conll
        write_conll(discourse_docgraph, args.output_file)
    elif args.output_format == 'paula':
        from discoursegraphs.readwrite.paulaxml.paula import write_paula
        write_paula(discourse_docgraph, args.output_file)

    elif args.output_format == 'no-output':
        pass  # just testing if the merging works
    else:
        raise ValueError(
            "Unsupported output format: {}".format(args.output_format))

    if debug:
        print "Merged successfully: ", args.tiger_file

if __name__ == '__main__':
    merging_cli(debug=True)
