#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

from tempfile import NamedTemporaryFile

import pytest

import discoursegraphs as dg
from discoursegraphs.corpora import pcc
from discoursegraphs.readwrite.neo4j import convert_to_geoff


MAZ_DOCGRAPH = pcc['maz-1423']


def test_convert_to_geoff():
    """converts a PCC docgraph into a geoff string."""
    geoff_str = convert_to_geoff(MAZ_DOCGRAPH)
    assert isinstance(geoff_str, str)


def test_write_geoff():
    """convert a PCC document into a geoff file."""
    temp_file = NamedTemporaryFile()
    temp_file.close()

    # write using an output file path
    dg.write_geoff(MAZ_DOCGRAPH, temp_file.name)

    # write using an output file object
    temp_file2 = NamedTemporaryFile()
    dg.write_geoff(MAZ_DOCGRAPH, temp_file2)
