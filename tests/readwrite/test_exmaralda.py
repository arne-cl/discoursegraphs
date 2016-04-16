#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os
from tempfile import NamedTemporaryFile

import pytest

from pytest import maz_1423  # global fixture
import discoursegraphs as dg
from discoursegraphs.readwrite.exmaralda import ExmaraldaDocumentGraph

"""
Basic tests for the Exmaralda file format.
"""


def test_read_exb():
    edg = dg.read_exb(os.path.join(dg.DATA_ROOT_DIR, 'maz-17706.exb'))
    assert isinstance(edg, ExmaraldaDocumentGraph)


@pytest.mark.xfail
def test_get_tokens():
    """the last node in .tokens (here: T208) doesn't seem to be a token"""
    edg = dg.read_exb(os.path.join(dg.DATA_ROOT_DIR, 'maz-17706.exb'))
    assert isinstance(edg, ExmaraldaDocumentGraph)

    assert len(list(edg.get_tokens())) == 208


def test_write_exb():
    """convert a PCC document into a exb file."""
    temp_file = NamedTemporaryFile()
    temp_file.close()
    dg.write_exb(maz_1423, temp_file.name)
