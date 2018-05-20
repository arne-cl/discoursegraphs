#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os
from tempfile import NamedTemporaryFile

import pytest

import discoursegraphs as dg
from discoursegraphs.readwrite.rst.hilda import HILDARSTTree
from discoursegraphs.readwrite.rst.rs3 import RS3FileWriter, RSTTree

"""
Basic tests for the *.hilda format for Rhetorical Structure Theory.
"""


def test_read_hilda1():
    input_tree = dg.read_hilda(os.path.join(dg.DATA_ROOT_DIR, 'short.hilda'))
    assert isinstance(input_tree, HILDARSTTree)

    tempfile = NamedTemporaryFile()
    RS3FileWriter(input_tree, output_filepath=tempfile.name)
    produced_output_tree = RSTTree(tempfile.name)

    assert input_tree.tree == produced_output_tree.tree


def test_read_hilda2():
    input_tree = dg.read_hilda(os.path.join(dg.DATA_ROOT_DIR, 'long.hilda'))
    assert isinstance(input_tree, HILDARSTTree)

    tempfile = NamedTemporaryFile()
    RS3FileWriter(input_tree, output_filepath=tempfile.name)
    produced_output_tree = RSTTree(tempfile.name)

    assert input_tree.tree == produced_output_tree.tree

