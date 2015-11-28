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

import os

import discoursegraphs as dg

PCC_DIRNAME = 'potsdam-commentary-corpus-2.0.0'


class PCC(object):
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
        self.connectors = self.get_layer_files('connectors', 'maz*.xml')
        self.coreference = self.get_layer_files('coreference', 'maz*.mmax')
        self.rst = self.get_layer_files('rst', 'maz*.rs3')
        self.syntax = self.get_layer_files('syntax', 'maz*.xml')
        self.tokenization = self.get_layer_files('tokenized', 'maz*.tok')

        self.layers = {
            'connectors': self.connectors,
            'coreference': self.coreference,
            'rst': self.rst,
            'syntax': self.syntax,
            'tokenization': self.tokenization,
        }

    def get_layer_files(self, layer_name, file_pattern):
        """
        returns a list of all files with the given filename pattern in the
        given PCC annotation layer
        """
        layer_path = os.path.join(self.path, layer_name)
        return list(dg.find_files(layer_path, file_pattern))


pcc = PCC()
