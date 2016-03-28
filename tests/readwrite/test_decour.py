#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os

import pytest

import discoursegraphs as dg

"""
Basic tests for the DeCour corpus format.
"""

def test_read_decour():
    """convert a DeCour XML file into a document graph"""
    decour_filepath = os.path.join(dg.DATA_ROOT_DIR, 'decour-example.xml')
    decour_dg = dg.read_decour(decour_filepath)

    # add precedence relations between tokens
    decour_prec = dg.read_decour(
        decour_filepath, precedence=True)

    num_of_prec_rels = len(
        list(dg.select_edges_by(decour_prec, layer='decour:precedence')))
    assert len(decour_prec.tokens) == num_of_prec_rels == 464

