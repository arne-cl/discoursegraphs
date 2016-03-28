#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os
from tempfile import NamedTemporaryFile

import pytest

import discoursegraphs as dg

"""
Basic tests for the CoNLL family of corpus formats.
"""

def test_read_conll():
    """convert a tab-separated CoNLL-2009 file into a document graph"""
    conll_filepath = os.path.join(dg.DATA_ROOT_DIR, 'conll2009-example.tsv')
    cdg = dg.read_conll(conll_filepath)

    # add precedence relations between tokens
    conll_prec = dg.read_conll(
        conll_filepath, precedence=True)

    num_of_prec_rels = len(
        list(dg.select_edges_by(conll_prec, layer='conll:precedence')))
    assert len(conll_prec.tokens) == num_of_prec_rels == 78


def test_write_conll():
    """convert a PCC coreference document into a conll file."""
    coref_file = dg.corpora.pcc.get_files_by_layer('coreference')[0]
    cdg = dg.read_mmax2(coref_file)

    temp_file = NamedTemporaryFile()
    temp_file.close()
    dg.write_conll(cdg, temp_file.name)

