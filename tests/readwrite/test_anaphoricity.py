#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os
from tempfile import NamedTemporaryFile

import pytest

import discoursegraphs as dg
from discoursegraphs.readwrite.anaphoricity import (
    AnaphoraDocumentGraph, write_anaphoricity)

"""
Basic tests for the anaphoricity annotation format
"""


def test_read_anaphoricity():
    das_adg = dg.read_anaphoricity(
        os.path.join(dg.DATA_ROOT_DIR, 'maz-17706-das.anaphoricity'))
    assert isinstance(das_adg, AnaphoraDocumentGraph)
    assert len(das_adg) == 209
    das_annos = list(
        dg.select_nodes_by_attribute(das_adg, 'anaphoricity:annotation'))
    assert len(das_annos) == 6


@pytest.mark.xfail
def test_merge_anaphoricity_graphs():
    """merging of two graphs with the same namespace doesn't work

    I tried fixing this by making rename_tokens() work on a copy of the
    input graph, but that didn't help.
    """
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


@pytest.mark.xfail
def test_write_anaphoricity():
    """output file contains '/a?' annotations instead of '/a' annotations"""
    input_path = os.path.join(dg.DATA_ROOT_DIR, 'maz-17706-das.anaphoricity')
    das_adg = dg.read_anaphoricity(
        os.path.join(dg.DATA_ROOT_DIR, 'maz-17706-das.anaphoricity'))

    temp_file = NamedTemporaryFile()
    temp_file.close()
    write_anaphoricity(das_adg, temp_file.name, anaphora='das')

    with open(input_path) as infile:
        input_text = ' '.join(infile.read().strip().split())

    with open(temp_file.name) as outfile:
        output_text = ' '.join(outfile.read().strip().split())

    assert input_text == output_text
