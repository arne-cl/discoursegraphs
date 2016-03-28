#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os

import pytest

import discoursegraphs as dg

"""
Basic tests for the SaltXMI format used by the SaltNPepper converter framework.
"""

SALT_FILEPATH = os.path.join(dg.DATA_ROOT_DIR, 'saltxmi-example.salt')


def test_saltxmi_graph():
    """convert a SaltXMI file into a graph"""
    sxmig = dg.readwrite.SaltXMIGraph(SALT_FILEPATH)

def test_salt_document():
    """create a SaltDocument and derive a LinguisticDocument from it"""
    sdg = dg.readwrite.SaltDocument(SALT_FILEPATH)
    lingdoc = dg.readwrite.salt.saltxmi.LinguisticDocument(sdg)
