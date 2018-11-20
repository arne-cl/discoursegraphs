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
    #~ import pudb; pudb.set_trace()
    input_file = os.path.join(dg.DATA_ROOT_DIR, 'short.dplp')
    input_tree = dg.read_dplp(input_file)

    tempfile = NamedTemporaryFile()
    dg.write_rs3(input_tree, tempfile.name)
    produced_output_tree = dg.read_rs3tree(tempfile.name)

    assert input_tree.tree == produced_output_tree.tree


def test_read_dplp2():
    input_file = os.path.join(dg.DATA_ROOT_DIR, 'long.dplp')
    input_tree = dg.read_dplp(input_file)

    tempfile = NamedTemporaryFile()
    dg.write_rs3(input_tree, tempfile.name)
    produced_output_tree = dg.read_rs3tree(tempfile.name)

    assert input_tree.tree == produced_output_tree.tree
