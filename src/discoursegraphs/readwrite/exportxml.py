#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

'''
The 'exportxml' module will convert a corpus in Negra ExportXML format [1]
(e.g. Tüba-D/Z [2]) into a document graph.

[1] http://www.sfs.uni-tuebingen.de/en/ascl/resources/corpora/export-format.html
[2] http://www.sfs.uni-tuebingen.de/en/ascl/resources/corpora/tueba-dz.html
'''

import os
from lxml import etree

import discoursegraphs as dg

class ExportXMLDocumentGraph(dg.DiscourseDocumentGraph):
    def __init__(self, exportxml_filepath, name=None, namespace='exportxml'):
        # super calls __init__() of base class DiscourseDocumentGraph
        super(ExportXMLDocumentGraph, self).__init__()

        self.name = name if name else os.path.basename(exportxml_filepath)
        self.ns = namespace
        self.root = self.ns+':root_node'
        self.add_node(self.root, layers={self.ns})
        tree = etree.parse(exportxml_filepath)
        for sentence in tree.iterfind('sentence'):
            add_sentence_structure(self, sentence)


def add_sentence_structure(docgraph, sentence):
    assert sentence.tag in ('sentence', 'node')
    if sentence.tag == 'sentence':
        root_id = sentence.attrib['origin']
    else: # if it's a (nested) node
        root_id = sentence.attrib['id']
        
    for node in sentence.iterfind('node'):
        docgraph.add_node(node.attrib['id'], label=node.attrib['cat'])
        docgraph.add_edge(root_id, node.attrib['id'])
        add_sentence_structure(docgraph, node)
    for word in sentence.iterfind('word'):
        docgraph.add_node(word.attrib['id'], label=word.attrib['form'])
        docgraph.add_edge(root_id, word.attrib['id'])


read_exportxml = ExportXMLDocumentGraph
