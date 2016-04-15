#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os

import pytest

import discoursegraphs as dg
from discoursegraphs.readwrite.anaphoricity import AnaphoraDocumentGraph

"""
Basic tests for the anaphoricity annotation format
"""

@pytest.mark.xfail
def test_read_anaphoricity():
    """merging of two graphs with the same namespace doesn't work"""
    das_adg = dg.read_anaphoricity(
        os.path.join(dg.DATA_ROOT_DIR, 'maz-17706-das.anaphoricity'))
    assert isinstance(das_adg, AnaphoraDocumentGraph)
    assert len(das_adg) == 209
    das_annos = list(
        dg.select_nodes_by_attribute(das_adg, 'anaphoricity:annotation'))
    assert len(das_annos) == 6
    
    es_adg = dg.read_anaphoricity(
        os.path.join(dg.DATA_ROOT_DIR, 'maz-17706-es.anaphoricity'))
    assert isinstance(es_adg, AnaphoraDocumentGraph)
    assert len(es_adg) == 209
    es_annos = list(
        dg.select_nodes_by_attribute(es_adg, 'anaphoricity:annotation'))
    assert len(es_annos) == 4

    # merge annotations
    das_adg.merge_graphs(es_adg)
    das_annos = list(
        dg.select_nodes_by_attribute(das_adg, 'anaphoricity:annotation'))
    assert len(das_annos) == 10
    assert len(das_adg) == len(es_adg) == 209
    
