#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os
import pkgutil
from tempfile import NamedTemporaryFile, mkdtemp

import pytest

import discoursegraphs as dg


MAZ_DOCGRAPH = dg.corpora.pcc['maz-14813']


@pytest.mark.skipif(pkgutil.find_loader("pygraphviz") == None,
                    reason="requires pygraphviz")
# pygraphviz may be hard to install on Ubuntu
# http://stackoverflow.com/questions/32885486/pygraphviz-importerror-undefined-symbol-agundirected
def test_write_dot():
    """convert a PCC document into a dot file."""
    temp_file = NamedTemporaryFile()
    temp_file.close()
    dg.write_dot(MAZ_DOCGRAPH, temp_file.name)


def test_print_dot():
    """convert a PCC document into a dot string."""
    dg.print_dot(MAZ_DOCGRAPH)

def test_unquote_from_pydot():
    """test string (de-)escaping for/from pydot."""
    unquoted = 'We are all "special" snowflakes.'
    quoted = dg.readwrite.dot.quote_for_pydot(unquoted)
    assert quoted == u'"We are all \\"special\\" snowflakes."'
    assert unquoted == dg.readwrite.dot.unquote_from_pydot(quoted)
