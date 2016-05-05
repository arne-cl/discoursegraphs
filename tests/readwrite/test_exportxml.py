#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

from cStringIO import StringIO
import os
import sys

import lxml
import pytest

import discoursegraphs as dg
from discoursegraphs.readwrite.exportxml import (
    ExportXMLCorpus, ExportXMLDocumentGraph)


class Capturing(list):
    """Context manager that captures STDOUT.

    source: http://stackoverflow.com/a/16571630
    """
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self
    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        sys.stdout = self._stdout


text_0_stats = ['Name: text_0',
 'Type: ExportXMLDocumentGraph',
 'Number of nodes: 1592',
 'Number of edges: 1685',
 'Average in degree:   1.0584',
 'Average out degree:   1.0584 ',
 '',
 'Node statistics',
 '===============',
 '',
 'number of nodes with layers',
 '\texportxml - 1592',
 '\texportxml:syntax - 837',
 '\texportxml:token - 675',
 '\texportxml:markable - 87',
 '\texportxml:coreferential - 46',
 '\texportxml:ne - 44',
 '\texportxml:anaphoric - 25',
 '\texportxml:expletive - 5',
 '\texportxml:connective - 1',
 '',
 'number of nodes with attributes',
 '\tlayers - 1592',
 '\tlabel - 1556',
 '\texportxml:func - 1512',
 '\texportxml:parent - 1365',
 '\texportxml:cat - 837',
 '\texportxml:form - 675',
 '\texportxml:lemma - 675',
 '\texportxml:pos - 675',
 '\texportxml:deprel - 675',
 '\texportxml:token - 675',
 '\texportxml:dephead - 530',
 '\texportxml:morph - 447',
 '\trelation - 76',
 '\texportxml:type - 44',
 '\ttokens - 35',
 '\texportxml:comment - 3',
 '\tconnective - 1',
 '\tmetadata - 1',
 '',
 'Edge statistics',
 '===============',
 '',
 'number of edges with layers',
 '\texportxml - 1685',
 '\texportxml:coreference - 76',
 '\texportxml:ne - 58',
 '\texportxml:coreferential - 46',
 '\texportxml:anaphoric - 30',
 '\texportxml:secedge - 4',
 '',
 'number of edges with attributes',
 '\tlayers - 1685',
 '\tedge_type - 1685',
 '\tlabel - 138',
 '',
 'most common source edges',
 '\ttext_0 - 35',
 '\ts33_541 - 7',
 '\ts6_538 - 7',
 '\ts6_536 - 7',
 '\ts7_544 - 7',
 '',
 'most common target edges',
 '\ts33_527 - 3',
 '\ts33_515 - 3',
 '\ts21_532 - 3',
 '\ts19_519 - 3',
 '\ts25_505 - 3']

text_9_stats = ['Name: text_9',
 'Type: ExportXMLDocumentGraph',
 'Number of nodes: 1369',
 'Number of edges: 2431',
 'Average in degree:   1.7757',
 'Average out degree:   1.7757 ',
 '',
 'Node statistics',
 '===============',
 '',
 'number of nodes with layers',
 '\texportxml - 1369',
 '\texportxml:syntax - 703',
 '\texportxml:token - 553',
 '\texportxml:edu - 49',
 '\texportxml:relation - 34',
 '\texportxml:discourse - 34',
 '\texportxml:markable - 30',
 '\texportxml:edu:range - 13',
 '\texportxml:anaphoric - 13',
 '\texportxml:ne - 13',
 '\texportxml:topic - 5',
 '\texportxml:coreferential - 4',
 '\texportxml:expletive - 2',
 '',
 'number of nodes with attributes',
 '\tlayers - 1369',
 '\tlabel - 1269',
 '\texportxml:func - 1256',
 '\texportxml:parent - 1128',
 '\texportxml:cat - 703',
 '\texportxml:token - 553',
 '\texportxml:pos - 553',
 '\texportxml:deprel - 553',
 '\texportxml:form - 553',
 '\texportxml:lemma - 550',
 '\texportxml:dephead - 429',
 '\texportxml:morph - 335',
 '\ttokens - 86',
 '\texportxml:relation - 34',
 '\texportxml:arg2 - 34',
 '\texportxml:marking - 34',
 '\texportxml:span - 24',
 '\trelation - 19',
 '\texportxml:type - 13',
 '\tdescription - 5',
 '\tmetadata - 1',
 '\texportxml:comment - 1',
 '',
 'Edge statistics',
 '===============',
 '',
 'number of edges with layers',
 '\texportxml - 2431',
 '\texportxml:topic - 524',
 '\texportxml:edu - 511',
 '\texportxml:relation - 36',
 '\texportxml:discourse - 36',
 '\texportxml:edu:range - 26',
 '\texportxml:ne - 23',
 '\texportxml:coreference - 22',
 '\texportxml:anaphoric - 18',
 '\texportxml:coreferential - 4',
 '\texportxml:secedge - 1',
 '',
 'number of edges with attributes',
 '\tlayers - 2431',
 '\tedge_type - 2431',
 '\tlabel - 82',
 '\trelation - 36',
 '',
 'most common source edges',
 '\ttopic_9_3 - 238',
 '\ttopic_9_2 - 131',
 '\ttopic_9_4 - 68',
 '\ttopic_9_1 - 45',
 '\ttopic_9_0 - 42',
 '',
 'most common target edges',
 '\ts133_14 - 4',
 '\ts132_4 - 4',
 '\ts132_9 - 4',
 '\ts134_9 - 4',
 '\ts154_7 - 4']

text_22_stats = ['Name: text_22',
 'Type: ExportXMLDocumentGraph',
 'Number of nodes: 1331',
 'Number of edges: 1386',
 'Average in degree:   1.0413',
 'Average out degree:   1.0413 ',
 '',
 'Node statistics',
 '===============',
 '',
 'number of nodes with layers',
 '\texportxml - 1331',
 '\texportxml:syntax - 684',
 '\texportxml:token - 552',
 '\texportxml:markable - 62',
 '\texportxml:ne - 58',
 '\texportxml:coreferential - 39',
 '\texportxml:anaphoric - 6',
 '\texportxml:inherent_reflexive - 3',
 '\texportxml:split_antecedent - 2',
 '\texportxml:relation - 1',
 '\texportxml:targetspan - 1',
 '\texportxml:expletive - 1',
 '',
 'number of nodes with attributes',
 '\tlayers - 1331',
 '\tlabel - 1294',
 '\texportxml:func - 1236',
 '\texportxml:parent - 1143',
 '\texportxml:cat - 684',
 '\texportxml:form - 552',
 '\texportxml:pos - 552',
 '\texportxml:deprel - 552',
 '\texportxml:token - 552',
 '\texportxml:lemma - 550',
 '\texportxml:dephead - 459',
 '\texportxml:morph - 381',
 '\texportxml:type - 58',
 '\trelation - 49',
 '\ttokens - 35',
 '\texportxml:span - 9',
 '\texportxml:comment - 1',
 '\tmetadata - 1',
 '',
 'Edge statistics',
 '===============',
 '',
 'number of edges with layers',
 '\texportxml - 1386',
 '\texportxml:ne - 65',
 '\texportxml:coreference - 48',
 '\texportxml:coreferential - 39',
 '\texportxml:anaphoric - 8',
 '\texportxml:split_antecedent - 3',
 '\texportxml:splitrelation - 1',
 '',
 'number of edges with attributes',
 '\tlayers - 1386',
 '\tedge_type - 1386',
 '\tlabel - 112',
 '',
 'most common source edges',
 '\ttext_22 - 35',
 '\ts387_534 - 6',
 '\ts379_533 - 6',
 '\ts385_530 - 6',
 '\ts374_525 - 5',
 '',
 'most common target edges',
 '\ts381_503 - 3',
 '\ts381_10 - 3',
 '\ts374_507 - 3',
 '\ts378_510 - 3',
 '\ts369_3 - 2']


def test_read_exportxml():
    """An ExportXML file can be parsed with the expected node/edge attributes."""
    exportxml_filepath = os.path.join(dg.DATA_ROOT_DIR, 'exportxml-example.xml')
    exportxml_corpus = dg.read_exportxml(exportxml_filepath)
    assert isinstance(exportxml_corpus, dg.readwrite.exportxml.ExportXMLCorpus)
    assert len(exportxml_corpus) == 3

    docgraph_stats = []
    for docgraph in exportxml_corpus:
        assert isinstance(docgraph, dg.readwrite.exportxml.ExportXMLDocumentGraph)

        with Capturing() as output:
            dg.info(docgraph)
        docgraph_stats.append(output)

    assert docgraph_stats == [text_0_stats, text_9_stats, text_22_stats]

    exportxml_corpus_debug = dg.read_exportxml(exportxml_filepath, debug=True)
    text_elem = next(exportxml_corpus_debug)
    assert isinstance(text_elem, lxml.etree._Element)
    assert text_elem.tag == 'text'
