#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os
from tempfile import NamedTemporaryFile

import pytest

import discoursegraphs as dg
from discoursegraphs.readwrite.rst.stagedp import StageDPRSTTree
from discoursegraphs.readwrite.rst.rs3 import RS3FileWriter, RSTTree

"""
Basic tests for the *.stagedp format for Rhetorical Structure Theory.
"""


def test_read_stagedp_one_edu():
    """the converter must not crash if the input only consists of one EDU."""
    # ~ import pudb; pudb.set_trace()
    input_tree = dg.read_stagedp(os.path.join(dg.DATA_ROOT_DIR, 'one-edu.stagedp'))
    assert isinstance(input_tree, StageDPRSTTree)

    tempfile = NamedTemporaryFile()
    RS3FileWriter(input_tree, output_filepath=tempfile.name)
    produced_output_tree = RSTTree(tempfile.name)

    assert input_tree.tree == produced_output_tree.tree


def test_read_stagedp_short():
    # ~ import pudb; pudb.set_trace()
    input_tree = dg.read_stagedp(os.path.join(dg.DATA_ROOT_DIR, 'short.stagedp'))
    assert isinstance(input_tree, StageDPRSTTree)

    tempfile = NamedTemporaryFile()
    RS3FileWriter(input_tree, output_filepath=tempfile.name)
    produced_output_tree = RSTTree(tempfile.name)

    assert input_tree.tree == produced_output_tree.tree



def test_read_stagedp_long():
    # ~ import pudb; pudb.set_trace()
    input_tree = dg.read_stagedp(os.path.join(dg.DATA_ROOT_DIR, 'long.stagedp'))
    assert isinstance(input_tree, StageDPRSTTree)

    tempfile = NamedTemporaryFile()
    RS3FileWriter(input_tree, output_filepath=tempfile.name)
    produced_output_tree = RSTTree(tempfile.name)

    assert input_tree.tree == produced_output_tree.tree


