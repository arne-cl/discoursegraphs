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
    """Are nodes correctly filtered based on their layer?"""
    conano_fpath = os.path.join(pcc.path, 'connectors/maz-10374.xml')
    codg = dg.read_conano(conano_fpath)
    conano_node_ids = list(dg.select_nodes_by_layer(codg, 'conano'))
    conano_nodes = list(dg.select_nodes_by_layer(codg, 'conano', data=True))
    assert len(codg) == len(conano_node_ids) == len(conano_nodes) == 188

