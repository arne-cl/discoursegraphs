#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module provides convenient access to the Potsdam Commentary Corpus [1][2],
a German newspaper commentary corpus containing syntax, part-of-speech,
coreference, connectors and rhetorical structure annotation.

The corpus is released under a Creative Commons
Attribution-NonCommercial-ShareAlike license.

[1] http://angcl.ling.uni-potsdam.de/resources/pcc.html
[2] Stede, Manfred and A. Neumann (2014). Potsdam Commentary Corpus 2.0:
    Annotation for Discourse Research. Proc. of the Language Resources and
    Evaluation Conference (LREC), Reykjavik.
"""

from collections import Sequence

import fnmatch
from itertools import chain
import os
import random
import re

import discoursegraphs as dg

PCC_DIRNAME = 'potsdam-commentary-corpus-2.0.0'
PCC_DOCID_RE = re.compile('^.*(maz-\d+)\..*')

TUEBADZ_PATH = os.path.expanduser(
    '~/corpora/tuebadz-8.0/tuebadz-8.0-mit-NE+Anaphern+Diskurs.exml.xml')


class PCC(Sequence):
    """
    class representation of the Potsdam Commentary Corpus

    Attributes
    ----------
    connectors : list(str)
        list of all Conano annotation files
    coreference : list(str)
        list of all MMAX2 coreference annotation files
    layers : dict(str: list(str))
        maps from an annotation layer name to it files
    path : str
        root directory of the PCC corpus
    rst : list(str)
        list of all RSTTool annotation files
    syntax : list(str)
        list of all Tiger annotation files
    tokenization : list(str)
        list of all tokenized plain text files

    """
    def __init__(self):
        self.path = os.path.join(dg.DATA_ROOT_DIR, PCC_DIRNAME)
        self.connectors = self.get_files_by_layer('connectors', 'maz*.xml')
        self.coreference = self.get_files_by_layer('coreference', 'maz*.mmax')
        self.rst = self.get_files_by_layer('rst', 'maz*.rs3')
        self.syntax = self.get_files_by_layer('syntax', 'maz*.xml')
        self.tokenization = self.get_files_by_layer('tokenized', 'maz*.tok')

        self.layers = {
            'connectors': (self.connectors, dg.read_conano),
            'coreference': (self.coreference, dg.read_mmax2),
            'rst': (self.rst, dg.read_rs3),
            'syntax': (self.syntax, dg.read_tiger),
            # TODO: implement TokenDocumentGraph before adding this
            # 'tokenization': (self.tokenization, dg.read_tokenized),
        }

        list_of_dir_contents = (files for (files, _) in self.layers.values())
        self._all_files = list(chain.from_iterable(list_of_dir_contents))

    @property
    def document_ids(self):
        """returns a list of document IDs used in the PCC"""
        matches = [PCC_DOCID_RE.match(os.path.basename(fname))
                   for fname in pcc.tokenization]
        return sorted(match.groups()[0] for match in matches)

    def __len__(self):
        """return the number of documents in the corpus"""
        return len(self.document_ids)

    def get_document(self, doc_id):
        """
        given a document ID, returns a merged document graph containng all
        available annotation layers.
        """
        layer_graphs = []
        for layer_name in self.layers:
            layer_files, read_function = self.layers[layer_name]
            for layer_file in layer_files:
                if fnmatch.fnmatch(layer_file, '*{}.*'.format(doc_id)):
                    layer_graphs.append(read_function(layer_file))

        if not layer_graphs:
            raise TypeError("There are no files with that document ID.")
        else:
            doc_graph = layer_graphs[0]
            for layer_graph in layer_graphs[1:]:
                doc_graph.merge_graphs(layer_graph)
        return doc_graph

    def __getitem__(self, sliced):
        """access documents by their index or by their document ID"""
        if isinstance(sliced, str):  # get document by its document ID
            return self.get_document(sliced)
        elif isinstance(sliced, int):  # get document by its index
            return self.get_document(self.document_ids[sliced])
        else:  # get a slice/range of documents
            doc_ids = self.document_ids[sliced]
            return [self.get_document(doc_id) for doc_id in doc_ids]

    def get_random_document(self):
        """return the document graph of a random PCC document"""
        random_docid = random.choice(self.document_ids)
        return self[random_docid]

    def get_files_by_layer(self, layer_name, file_pattern='*'):
        """
        returns a list of all files with the given filename pattern in the
        given PCC annotation layer
        """
        layer_path = os.path.join(self.path, layer_name)
        return list(dg.find_files(layer_path, file_pattern))

    def get_files_by_document_id(self, document_id):
        """
        returns a list of all files (from all available annotation layers)
        with the given document ID.
        """
        assert isinstance(document_id, basestring), \
            "The document ID must be given as a string, e.g. 'maz-1423'"
        return list(dg.find_files(self._all_files, '*{}.*'.format(document_id)))


pcc = PCC()
