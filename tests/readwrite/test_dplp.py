#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os
from tempfile import NamedTemporaryFile

import pytest

import discoursegraphs as dg


"""
Basic tests for parsing DPLP's output format for Rhetorical Structure Theory.
"""


def test_read_dplp1():
    parsetree_file = os.path.join(dg.DATA_ROOT_DIR, 'dplp-short.parsetree')
    merge_file = os.path.join(dg.DATA_ROOT_DIR, 'dplp-short.merge')
    input_tree = dg.read_dplp(parsetree_file, merge_file)

    tempfile = NamedTemporaryFile()
    dg.write_rs3(input_tree, tempfile.name)
    produced_output_tree = dg.read_rs3tree(tempfile.name)

    assert input_tree.tree == produced_output_tree.tree


def test_read_dplp2():
    parsetree_file = os.path.join(dg.DATA_ROOT_DIR, 'dplp-long.parsetree')
    merge_file = os.path.join(dg.DATA_ROOT_DIR, 'dplp-long.merge')
    input_tree = dg.read_dplp(parsetree_file, merge_file)

    tempfile = NamedTemporaryFile()
    dg.write_rs3(input_tree, tempfile.name)
    produced_output_tree = dg.read_rs3tree(tempfile.name)

    assert input_tree.tree == produced_output_tree.tree
