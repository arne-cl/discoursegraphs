#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import pkgutil
from tempfile import NamedTemporaryFile

import pytest

import discoursegraphs as dg
from discoursegraphs.corpora import pcc

maz_1423 = pcc['maz-1423']


def test_write_brackets():
    """convert a PCC document into a brackets file."""
    temp_file = NamedTemporaryFile()
    temp_file.close()
    dg.write_brackets(maz_1423, temp_file.name)


def test_write_brat():
    """convert a PCC document into a brat file."""
    temp_file = NamedTemporaryFile()
    temp_file.close()
    dg.write_brat(maz_1423, temp_file.name)


def test_write_conll():
    """convert a PCC coreference document into a conll file."""
    coref_file = dg.corpora.pcc.get_files_by_layer('coreference')[0]
    cdg = dg.read_mmax2(coref_file)

    temp_file = NamedTemporaryFile()
    temp_file.close()
    dg.write_conll(cdg, temp_file.name)


@pytest.mark.skipif(pkgutil.find_loader("pygraphviz") == None,
                    reason="requires pygraphviz")
# pygraphviz may be hard to install on Ubuntu
# http://stackoverflow.com/questions/32885486/pygraphviz-importerror-undefined-symbol-agundirected
def test_write_dot():
    """convert a PCC document into a dot file."""
    temp_file = NamedTemporaryFile()
    temp_file.close()
    dg.write_dot(maz_1423, temp_file.name)


def test_write_exb():
    """convert a PCC document into a exb file."""
    temp_file = NamedTemporaryFile()
    temp_file.close()
    dg.write_exb(maz_1423, temp_file.name)


@pytest.mark.skip(reason="node IDs must match '^[A-Za-z][0-9A-Za-z]*$'")
# cf. http://www.fim.uni-passau.de/fileadmin/files/lehrstuhl/brandenburg/projekte/gml/gml-technical-report.pdf
def test_write_gml():
    """convert a PCC document into a gml file."""
    temp_file = NamedTemporaryFile()
    temp_file.close()
    dg.write_gml(maz_1423, temp_file.name)


def test_write_graphml():
    """convert a PCC document into a graphml file."""
    temp_file = NamedTemporaryFile()
    temp_file.close()
    dg.write_graphml(maz_1423, temp_file.name)


def test_write_gexf():
    """convert a PCC document into a gexf file."""
    temp_file = NamedTemporaryFile()
    temp_file.close()
    dg.write_gexf(maz_1423, temp_file.name)


def test_write_geoff():
    """convert a PCC document into a geoff file."""
    temp_file = NamedTemporaryFile()
    temp_file.close()
    dg.write_geoff(maz_1423, temp_file.name)


def test_write_paula():
    """convert a PCC document into a paula file."""
    temp_file = NamedTemporaryFile()
    temp_file.close()
    dg.write_paula(maz_1423, temp_file.name)


@pytest.mark.slowtest
def test_pcc():
    """
    create document graphs for all PCC documents containing all annotation
    layers.
    """
    assert len(pcc.document_ids) == 176

    for doc_id in pcc.document_ids:
        docgraph = pcc[doc_id]
        assert isinstance(docgraph, dg.DiscourseDocumentGraph)
