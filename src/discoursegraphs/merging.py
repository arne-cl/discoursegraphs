#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os
import sys
import re
from networkx import write_gpickle

from discoursegraphs import DiscourseDocumentGraph
from discoursegraphs.readwrite.anaphoricity import AnaphoraDocumentGraph
from discoursegraphs.readwrite.rst import RSTGraph, rst_tokenlist
from discoursegraphs.readwrite.tiger import TigerDocumentGraph, tiger_tokenlist


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.stderr.write('Usage: {0} tiger_file rst_file pickle_output_file\n'.format(sys.argv[0]))
        sys.exit(1)
    else:
        #~ pass
        tiger_filepath = sys.argv[1]
        rst_filepath = sys.argv[2]
        pickle_filepath = sys.argv[3]

        assert os.path.isfile(tiger_filepath)
        tiger_docgraph = TigerDocumentGraph(tiger_filepath)
        tiger_tokens = tiger_tokenlist(tiger_docgraph)

        assert os.path.isfile(rst_filepath)
        rst_graph = RSTGraph(rst_filepath)
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
            else: # token mismatch
                raise ValueError("Tokenization mismatch between:\n" \
                    "{0}\n{1}".format(tiger_filepath, rst_filepath))

        for i, node in tiger_docgraph.nodes(data=True):
            print i, node
        #~ write_gpickle(tiger_docgraph, pickle_filepath)
