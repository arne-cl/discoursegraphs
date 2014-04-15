#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os
import sys
import re
from networkx import write_dot

from discoursegraphs import DiscourseDocumentGraph
from discoursegraphs.relabel import relabel_nodes
from discoursegraphs.util import ensure_unicode
from discoursegraphs.readwrite.anaphoricity import AnaphoraDocumentGraph
from discoursegraphs.readwrite.rst import RSTGraph, rst_tokenlist
from discoursegraphs.readwrite.tiger import TigerDocumentGraph, tiger_tokenlist


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
                             "{0}\n{1}".format(tiger_filepath, rst_filepath))


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
            raise ValueError(u"tokens don't match: {0} (anaphoricity) vs. {1} (tiger)".format(
                anaphora_token, tiger_token))
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


if __name__ == '__main__':
    if len(sys.argv) != 5:
        sys.stderr.write(
            'Usage: {0} tiger_file rst_file anaphoricity_file dot_output_file\n'.format(sys.argv[0]))
        sys.exit(1)
    else:
        tiger_filepath = sys.argv[1]
        rst_filepath = sys.argv[2]
        anaphora_filepath = sys.argv[3]
        dot_filepath = sys.argv[4]

        for filepath in (tiger_filepath, rst_filepath, anaphora_filepath):
            assert os.path.isfile(
                filepath), "{} doesn't exist".format(filepath)
        tiger_docgraph = TigerDocumentGraph(tiger_filepath)
        rst_graph = RSTGraph(rst_filepath)
        anaphora_graph = AnaphoraDocumentGraph(anaphora_filepath)

        add_rst_to_tiger(tiger_docgraph, rst_graph)
        add_anaphoricity_to_tiger(tiger_docgraph, anaphora_graph)
        write_dot(tiger_docgraph, dot_filepath)
