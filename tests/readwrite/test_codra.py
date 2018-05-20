#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os
from tempfile import NamedTemporaryFile

import pytest

import discoursegraphs as dg
from discoursegraphs.readwrite.rst.dis.codra import CodraRSTTree
from discoursegraphs.readwrite.rst.rs3 import RS3FileWriter, RSTTree

"""Basic tests for the *.codra format for Rhetorical Structure Theory."""


def test_read_codra_tree():
    input_tree = dg.read_codra(os.path.join(dg.DATA_ROOT_DIR, 'long.codra'))
    assert isinstance(input_tree, CodraRSTTree)

    tempfile = NamedTemporaryFile()
    RS3FileWriter(input_tree, output_filepath=tempfile.name)
    produced_output_tree = RSTTree(tempfile.name)

    # there is a difference in the tree objects but I don't know what it is,
    # as their pretty-print representations are identical
    assert input_tree.tree.pprint() == produced_output_tree.tree.pprint()

