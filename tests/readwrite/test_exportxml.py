#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os

import lxml
import pytest

import discoursegraphs as dg
from discoursegraphs.readwrite.exportxml import (
    ExportXMLCorpus, ExportXMLDocumentGraph)


def test_read_exportxml():
    exportxml_filepath = os.path.join(dg.DATA_ROOT_DIR, 'exportxml-example.xml')
    exportxml_corpus = dg.read_exportxml(exportxml_filepath)
    assert isinstance(exportxml_corpus, dg.readwrite.exportxml.ExportXMLCorpus)
    assert len(exportxml_corpus) == 3

    for docgraph in exportxml_corpus:
        assert isinstance(docgraph, dg.readwrite.exportxml.ExportXMLDocumentGraph)

    exportxml_corpus_debug = dg.read_exportxml(exportxml_filepath, debug=True)
    text_elem = next(exportxml_corpus_debug)
    assert isinstance(text_elem, lxml.etree._Element)
    assert text_elem.tag == 'text'
