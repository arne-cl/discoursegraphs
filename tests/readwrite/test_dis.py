#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os

import pytest

import discoursegraphs as dg
from discoursegraphs.readwrite.rst.dis import RSTLispDocumentGraph

"""
Basic tests for the *.dis format for Rhetorical Structure Theory
"""


def test_read_dis1():
    disdg1 = dg.read_dis(os.path.join(dg.DATA_ROOT_DIR, 'rst-example1.dis'))
    assert isinstance(disdg1, RSTLispDocumentGraph)


@pytest.mark.xfail
def test_read_dis2():
    """NotImplementedError: I don't know how to combine two satellites"""
    disdg1 = dg.read_dis(os.path.join(dg.DATA_ROOT_DIR, 'rst-example2.dis'))
    assert isinstance(disdg1, RSTLispDocumentGraph)
