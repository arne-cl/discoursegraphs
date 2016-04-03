#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import pkgutil
from tempfile import NamedTemporaryFile, mkdtemp

import networkx as nx
import pytest

import discoursegraphs as dg
from discoursegraphs.corpora import pcc


@pytest.mark.slowtest
def test_pcc():
    """
    create document graphs for all PCC documents containing all annotation
    layers.
    """
    assert len(pcc.document_ids) == 176

    for doc_id in pcc.document_ids:
        docgraph = pcc[doc_id]
        assert isinstance(docgraph, dg.DiscourseDocumentGraph)
        assert nx.is_directed_acyclic_graph(docgraph) == True
