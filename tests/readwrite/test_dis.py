#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os
from tempfile import NamedTemporaryFile

import pytest

import discoursegraphs as dg
from discoursegraphs.readwrite.rst.dis.disgraph import RSTLispDocumentGraph
from discoursegraphs.readwrite.rst.dis.distree import DisRSTTree
from discoursegraphs.readwrite.rst.rs3 import RS3FileWriter, RSTTree

"""
Basic tests for the *.dis format for Rhetorical Structure Theory.

There are two different approaches for this:

RSTLispDocumentGraph parses a *.dis file into a document graph (unmaintained).
DisRSTTree parses a *.dis file into a parented tree (new, recommended, format
can be exported to *.rs3).
"""


def test_read_dis1_graph():
    disdg1 = dg.read_dis(os.path.join(dg.DATA_ROOT_DIR, 'rst-example1.dis'))
    assert isinstance(disdg1, RSTLispDocumentGraph)


@pytest.mark.xfail(reason="Graph parser doesn't support two satellites in one relation")
def test_read_dis2_graph():
    """NotImplementedError: I don't know how to combine two satellites.

    The DIS graph parser (RSTLispDocumentGraph) doesn't support RST structures
    with two satellites in a single relation. This is a known limitation.

    Note: The tree parser (DisRSTTree) CAN parse this file successfully.
    Use dg.read_distree() for files with this structure."""
    disdg1 = dg.read_dis(os.path.join(dg.DATA_ROOT_DIR, 'rst-example2.dis'))
    assert isinstance(disdg1, RSTLispDocumentGraph)


def test_read_dis1_tree():
    input_tree = dg.read_distree(os.path.join(dg.DATA_ROOT_DIR, 'rst-example1.dis'))
    assert isinstance(input_tree, DisRSTTree)

    tempfile = NamedTemporaryFile()
    RS3FileWriter(input_tree, output_filepath=tempfile.name)
    produced_output_tree = RSTTree(tempfile.name)

    assert input_tree.tree == produced_output_tree.tree


def test_read_dis2_tree():
    input_tree = dg.read_distree(os.path.join(dg.DATA_ROOT_DIR, 'rst-example2.dis'))
    assert isinstance(input_tree, DisRSTTree)

    tempfile = NamedTemporaryFile()
    RS3FileWriter(input_tree, output_filepath=tempfile.name)
    produced_output_tree = RSTTree(tempfile.name)

    assert input_tree.tree == produced_output_tree.tree
