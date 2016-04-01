#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os
from tempfile import NamedTemporaryFile

import pytest

import discoursegraphs as dg
from discoursegraphs.readwrite.conll import traverse_dependencies_up

"""
Basic tests for the CoNLL family of corpus formats.
"""

CONLL_FILEPATH = os.path.join(dg.DATA_ROOT_DIR, 'conll2009-example.tsv')
ELEFANT_2009_FILEPATH = os.path.join(dg.DATA_ROOT_DIR, 'conll2009-elefant-mate.tsv')
ELEFANT_2010_FILEPATH = os.path.join(dg.DATA_ROOT_DIR, 'conll2010-elefant-mate.tsv')


def test_read_conll():
    """convert tab-separated CoNLL (2009/2010) files into document graphs"""
    cdg = dg.read_conll(CONLL_FILEPATH)

    # add precedence relations between tokens
    conll_prec = dg.read_conll(
        CONLL_FILEPATH, precedence=True)

    num_of_prec_rels = len(
        list(dg.select_edges_by(conll_prec, layer='conll:precedence')))
    assert len(conll_prec.tokens) == num_of_prec_rels == 78

    # read a file with key|val morphological features
    cdg_elefant = dg.read_conll(ELEFANT_2009_FILEPATH)
    # read the "CoNLL-2010" format (produced by mate tools?)
    cdg_elefant_2010 = dg.read_conll(
        ELEFANT_2010_FILEPATH, conll_format='2010')


def test_traverse_dependencies_up():
    """follow the dependency path backwards from the given node to the root"""
    cdg = dg.read_conll(CONLL_FILEPATH)
    traverse_dependencies_up(cdg, 's1_t8', node_attr=None)
    
    # example sentence: Chomsky is a major figure in analytical philosophy ...
    # ROOT: is --PRD--> figure --LOC--> in 
    assert cdg.get_token('s1_t8') == u'philosophy'
    assert list(traverse_dependencies_up(cdg, 's1_t8')) == \
        [u'in', u'figure', u'be']
    assert list(traverse_dependencies_up(
        cdg, 's1_t8', node_attr='token')) == [u'in', u'figure', u'is']
    assert list(traverse_dependencies_up(
        cdg, 's1_t8', node_attr='pos')) == [u'IN', u'NN', u'VBZ']
    assert list(traverse_dependencies_up(
        cdg, 's1_t8', node_attr='deprel')) == [u'LOC', u'PRD', u'ROOT']


def test_write_conll():
    """convert a PCC coreference document into a conll file."""
    coref_file = dg.corpora.pcc.get_files_by_layer('coreference')[0]
    cdg = dg.read_mmax2(coref_file)

    temp_file = NamedTemporaryFile()
    temp_file.close()
    dg.write_conll(cdg, temp_file.name)

