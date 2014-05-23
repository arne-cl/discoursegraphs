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

from discoursegraphs.relabel import relabel_nodes
from discoursegraphs.readwrite.anaphoricity import AnaphoraDocumentGraph
from discoursegraphs.readwrite.rst import RSTGraph, rst_tokenlist
from discoursegraphs.readwrite.tiger import TigerDocumentGraph, tiger_tokenlist
from discoursegraphs.readwrite.conano import ConanoDocumentGraph
from discoursegraphs.readwrite.neo4j import convert_to_geoff, upload_to_neo4j


def add_rst_to_tiger(tiger_docgraph, rst_graph):
    """
    adds an RSTGraph to a TigerDocumentGraph, thereby adding edges from
    each RST segment to the (Tiger) tokens they represent.

    Parameters
    ----------
    tiger_docgraph : TigerDocumentGraph
        multidigraph representing a syntax annotated (TigerXML) document
    rst_graph : RSTGraph
        multidigraph representing a RST annotated (RS3) document
    """
    tiger_tokens = tiger_tokenlist(tiger_docgraph)
    rst_tokens = rst_tokenlist(rst_graph)

    tiger_docgraph.add_nodes_from(rst_graph.nodes(data=True))
    tiger_docgraph.add_edges_from(rst_graph.edges(data=True))

    for i, (tiger_tok, tiger_sent_id, tiger_tok_id) in enumerate(tiger_tokens):
        rst_token, rst_segment_node_id = rst_tokens[i]
        if tiger_tok == rst_token:
            tiger_docgraph.add_node(tiger_tok_id, layers={'rst', 'rst:token'},
                                    attr_dict={'rst:token': rst_token})
            tiger_docgraph.add_edge(int(rst_segment_node_id), tiger_tok_id,
                                    layers={'rst', 'rst:token'})
        else:  # token mismatch
            raise ValueError("Tokenization mismatch between:\n"
                             "{0}\n{1}".format(tiger_docgraph, rst_graph))


def add_conano_to_tiger(tiger_docgraph, conano_graph):
    """
    TODO: implement function
    TODO: simplify Tiger doc graph (i.e. add `self.tokens`)
    """
    raise NotImplementedError


def map_anaphoricity_tokens_to_tiger(tiger_docgraph, anaphora_graph):
    """
    creates a map from anaphoricity token node IDs to tiger token node
    IDs.

    Parameters
    ----------
    tiger_docgraph : TigerDocumentGraph
        multidigraph representing a syntax annotated (TigerXML) document
    anaphora_graph : AnaphoraDocumentGraph
        multidigraph representing a anaphorcity annotated document
        (ad-hoc format used in Christian Dittrich's diploma thesis)

    Returns
    -------
    anaphora2tiger : dict
        map from anaphoricity token node IDs (int) to tiger token node
        IDs (str, e.g. 's23_5')
    """
    # list of (token unicode, tiger_sent_id str, tiger_token_id str)
    tiger_tokens = tiger_tokenlist(tiger_docgraph)

    anaphora2tiger = {}
    for i, anaphora_node_id in enumerate(anaphora_graph.tokens):
        anaphora_token = anaphora_graph.node[
            anaphora_node_id]['anaphoricity:token']
        tiger_token, tiger_sent_id, tiger_token_id = tiger_tokens[i]

        if anaphora_token == tiger_token:
            anaphora2tiger[anaphora_node_id] = tiger_token_id
        else:
            raise ValueError(
                (u"tokens don't match: {0} (anaphoricity) vs. "
                 "{1} (tiger)".format(anaphora_token, tiger_token)))
    return anaphora2tiger


def add_anaphoricity_to_tiger(tiger_docgraph, anaphora_graph):
    """
    adds an AnaphoraDocumentGraph to a TigerDocumentGraph, thereby
    adding information about the anaphoricity of words
    (e.g. 'das', 'es') to the respective (Tiger) tokens.

    Parameters
    ----------
    tiger_docgraph : TigerDocumentGraph
        multidigraph representing a syntax annotated (TigerXML) document
    anaphora_graph : AnaphoraDocumentGraph
        multidigraph representing a anaphorcity annotated document
        (ad-hoc format used in Christian Dittrich's diploma thesis)
    """
    anaphora2tiger = map_anaphoricity_tokens_to_tiger(
        tiger_docgraph, anaphora_graph)
    relabel_nodes(anaphora_graph, anaphora2tiger, copy=False)
    tiger_docgraph.add_nodes_from(anaphora_graph.nodes(data=True))
    # the anaphora doc graph only contains trivial edges from its root
    # node. we won't add them and will remove the root.
    try:
        tiger_docgraph.remove_node('anaphoricity:root_node')
    except:
        pass


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
    parser.add_argument('-o', '--output-format',
                        default='dot',
                        help='output format: dot, geoff, neo4j, no-output')
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
        add_rst_to_tiger(tiger_docgraph, rst_graph)

    if args.anaphoricity_file:
        anaphora_graph = AnaphoraDocumentGraph(args.anaphoricity_file)
        add_anaphoricity_to_tiger(tiger_docgraph, anaphora_graph)

    if args.conano_file:
        conano_graph = ConanoDocumentGraph(args.conano_file)
        add_conano_to_tiger(tiger_docgraph, conano_graph)

    if args.output_format == 'dot':
        write_dot(tiger_docgraph, args.output_file)
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
