#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

__author__ = 'Arne Neumann'
__email__ = 'discoursegraphs.programming@arne.cl'
__version__ = '0.4.4'

# flake8: noqa

import os
from networkx import write_gpickle

from discoursegraphs.discoursegraph import (
    DiscourseDocumentGraph, EdgeTypes, create_token_mapping,
    get_annotation_layers, get_span, get_span_offsets,
    get_text, is_continuous, istoken, layer2namespace,
    select_neighbors_by_edge_attribute,
    select_neighbors_by_layer, select_nodes_by_attribute,
    select_nodes_by_layer, select_edges_by_attribute,
    select_edges_by, tokens2text,
    get_pointing_chains, get_top_level_layers)
from discoursegraphs.readwrite import (
    read_anaphoricity, write_brackets, write_brat, read_codra, read_conano, read_conll, write_conll,
    read_decour, read_dplp, write_dot, read_exb, read_exmaralda, write_exmaralda, write_exb,
    read_exportxml, write_freqt, write_graphml, write_gexf, read_hilda, read_hs2015tree, read_mmax2,
    write_neo4j, write_geoff, write_paula,
    read_ptb, read_mrg,
    read_rst, read_rs3, read_rs3tree, write_rs3, write_rstlatex,
    read_dis, read_distree, write_dis, read_tiger, read_urml)
from discoursegraphs.readwrite.dot import print_dot
from discoursegraphs.statistics import info
from discoursegraphs.util import xmlprint, make_labels_explicit, find_files


PACKAGE_ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_ROOT_DIR = os.path.join(PACKAGE_ROOT_DIR, 'data')

# corpora can't be imported before root dirs and ``find_files`` are known
from discoursegraphs import corpora
