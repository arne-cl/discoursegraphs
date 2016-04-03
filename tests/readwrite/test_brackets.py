#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

from tempfile import NamedTemporaryFile

from pytest import maz_1423  # global fixture
import discoursegraphs as dg

"""
Basic tests for the bracketed output format.
"""


def test_write_brackets():
    """convert a PCC document into a brackets file."""
    temp_file = NamedTemporaryFile()
    temp_file.close()
    dg.write_brackets(maz_1423, temp_file.name)

