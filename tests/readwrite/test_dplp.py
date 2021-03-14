#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os
from tempfile import NamedTemporaryFile

import pytest

import discoursegraphs as dg
from discoursegraphs.readwrite.tree import t

"""
Basic tests for parsing DPLP's output format for Rhetorical Structure Theory.
"""


def test_read_dplp_short():
    input_file = os.path.join(dg.DATA_ROOT_DIR, 'short.dplp')
    input_tree = dg.read_dplp(input_file)

    tempfile = NamedTemporaryFile()
    dg.write_rs3(input_tree, tempfile.name)
    produced_output_tree = dg.read_rs3tree(tempfile.name)

    assert input_tree.tree == produced_output_tree.tree


def test_read_dplp_one_edu():
    input_file = os.path.join(dg.DATA_ROOT_DIR, 'one-edu.dplp')
    input_tree = dg.read_dplp(input_file)

    tempfile = NamedTemporaryFile()
    dg.write_rs3(input_tree, tempfile.name)
    produced_output_tree = dg.read_rs3tree(tempfile.name)

    assert input_tree.tree == produced_output_tree.tree == t('N', ['good food .'])


def test_read_dplp_too_long():
    input_file = os.path.join(dg.DATA_ROOT_DIR, 'long.dplp')
    input_tree = dg.read_dplp(input_file)

    tempfile = NamedTemporaryFile()
    dg.write_rs3(input_tree, tempfile.name)
    produced_output_tree = dg.read_rs3tree(tempfile.name)

    assert input_tree.tree == produced_output_tree.tree
