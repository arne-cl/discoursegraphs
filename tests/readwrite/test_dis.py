#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os

import pytest

import discoursegraphs as dg
from discoursegraphs.readwrite.rst.dis.disgraph import RSTLispDocumentGraph
from discoursegraphs.readwrite.rst.dis.distree import DisRSTTree

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


@pytest.mark.xfail
def test_read_dis2_graph():
    """NotImplementedError: I don't know how to combine two satellites.

    Don't worry, DisRSTTree can parse this."""
    disdg1 = dg.read_dis(os.path.join(dg.DATA_ROOT_DIR, 'rst-example2.dis'))
    assert isinstance(disdg1, RSTLispDocumentGraph)


def test_read_dis1_tree():
    disdg1 = DisRSTTree(os.path.join(dg.DATA_ROOT_DIR, 'rst-example1.dis'))
    assert isinstance(disdg1, DisRSTTree)


def test_read_dis2_tree():
    disdg1 = DisRSTTree(os.path.join(dg.DATA_ROOT_DIR, 'rst-example2.dis'))
    assert isinstance(disdg1, DisRSTTree)
