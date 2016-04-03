#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

from tempfile import NamedTemporaryFile, mkdtemp

from pytest import maz_1423  # global fixture
import discoursegraphs as dg

"""
Basic tests for the gexf output format.
"""


def test_write_paula():
    """convert a PCC document into a paula file."""
    temp_dir = mkdtemp()
    dg.write_paula(maz_1423, temp_dir)

