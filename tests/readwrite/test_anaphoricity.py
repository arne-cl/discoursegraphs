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


@pytest.mark.xfail(reason="merge_graphs deletes root_node when merging same namespace")
def test_merge_anaphoricity_graphs():
    """Merging anaphoricity graphs with the same namespace doesn't work.

    Bug: When merging two anaphoricity graphs, the 'anaphoricity:root_node'
    from the first graph gets deleted, reducing node count from 209 to 208.

    Root cause: merge_graphs() doesn't properly handle special nodes (like
    root_node) that exist in both graphs with the same node ID.

    The merge should either:
    1. Preserve both root nodes with renamed IDs, or
    2. Merge root node attributes, or
    3. Require graphs to have different namespaces

    Note: The test author tried making rename_tokens() work on a copy but
    that didn't resolve the issue. The problem is deeper in merge_graphs()."""
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


def test_write_anaphoricity():
    """output file contains '/a?' annotations instead of '/a' annotations

    Fixed: gen_anaphoricity_str now checks certainty attribute value, not name"""
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
