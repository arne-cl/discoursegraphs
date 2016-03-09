#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import pytest

from discoursegraphs.corpora import pcc
from discoursegraphs.readwrite.neo4j import convert_to_geoff, upload_to_neo4j


@pytest.mark.slowtest
def test_convert_to_geoff():
    """
    tests, if all PCC documents can be converted to geoff without errors.
    """
    assert len(pcc.document_ids) == 176

    for doc_id in pcc.document_ids:
        docgraph = pcc[doc_id]
        geoff_str = convert_to_geoff(docgraph)
        assert isinstance(geoff_str, str)


@pytest.mark.integration
def test_upload_to_neo4j():
    """
    test, if a discoursegraph can be uploaded to a running neo4j database
    without errors.
    """
    docgraph = pcc['maz-4031']
    neonx_results = upload_to_neo4j(docgraph)
    assert isinstance(neonx_results, list)

