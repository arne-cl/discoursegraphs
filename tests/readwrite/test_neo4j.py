#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import pytest

from discoursegraphs.corpora import pcc
from discoursegraphs.readwrite.neo4j import convert_to_geoff


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
