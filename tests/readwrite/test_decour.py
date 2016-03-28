#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os

import pytest

import discoursegraphs as dg

"""
Basic tests for the DeCour corpus format.
"""

def test_read_decour():
    decour_filepath = os.path.join(dg.DATA_ROOT_DIR, 'decour-example.xml')
    decour_dg = dg.read_decour(decour_filepath)


