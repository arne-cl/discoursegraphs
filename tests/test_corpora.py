#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

from copy import deepcopy
from multiprocessing import Process
import pkgutil
from tempfile import NamedTemporaryFile, mkdtemp

import networkx as nx
import pytest

import discoursegraphs as dg
from discoursegraphs.corpora import pcc


def test_pcc():
    """
    create document graphs for all PCC documents containing all annotation
    layers and test them for cyclicity.
    """
    def convert_pcc_doc(doc_id):
        docgraph = pcc[doc_id]
        assert isinstance(docgraph, dg.DiscourseDocumentGraph)

        # We can't guarantee that all graphs are acyclic, because of secedges
        # in TigerSentenceGraphs, but there must be no self loops.
        if nx.is_directed_acyclic_graph(docgraph):
            for src, target in docgraph.edges_iter():
                assert src != target

            # cyclic graphs must become acyclic once we remove the secedges
            bad_graph = deepcopy(docgraph)
            secedges = dg.select_edges_by(bad_graph, 'tiger:secedge')
            bad_graph.remove_edges_from(secedges)
            assert nx.is_directed_acyclic_graph(docgraph)


    assert len(pcc.document_ids) == 176

    p = Process(target=convert_pcc_doc, args=pcc.document_ids)
    p.start()
    p.join()
