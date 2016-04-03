#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os

import discoursegraphs as dg
from discoursegraphs.corpora import pcc

"""
Basic tests for the gexf output format.
"""


def test_select_nodes_by_layer():
    """Are MMAX2 nodes correctly filtered based on their layer?"""
    coref_fpath = os.path.join(pcc.path, 'coreference/maz-10374.mmax')
    cdg = dg.read_mmax2(coref_fpath)
    coref_node_ids = list(dg.select_nodes_by_layer(cdg, 'mmax'))
    coref_nodes = list(dg.select_nodes_by_layer(cdg, 'mmax', data=True))
    assert len(coref_node_ids) == len(cdg) == 231

