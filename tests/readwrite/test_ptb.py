#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os

import pytest

import discoursegraphs as dg

def test_create_empty_ptbgraph():
    pdg = dg.read_ptb()
    assert isinstance(pdg, dg.readwrite.ptb.PTBDocumentGraph)

def test_read_ptb():
    ptb_filepath = os.path.join(dg.DATA_ROOT_DIR, 'ptb-example.mrg')
    pdg = dg.read_ptb(ptb_filepath)
    assert isinstance(pdg, dg.readwrite.ptb.PTBDocumentGraph)
    assert len(pdg.tokens) == 78
    assert pdg.sentences == [1, 62, 196]

    # only parse the first sentence of the file
    pdg_first_sentence = dg.read_ptb(ptb_filepath, limit=1)
    assert len(pdg_first_sentence.tokens) == 21
    assert len(pdg_first_sentence.sentences) == 1
