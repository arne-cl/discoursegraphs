#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

__author__ = 'Arne Neumann'
__email__ = 'discoursegraphs.programming@arne.cl'
__version__ = '0.3.0'

# flake8: noqa

import os
from networkx import write_gpickle

from discoursegraphs.discoursegraph import (
    DiscourseDocumentGraph, EdgeTypes, create_token_mapping,
    get_annotation_layers, get_span, get_span_offsets,
    get_text, is_continuous, istoken, layer2namespace,
    select_neighbors_by_layer, select_nodes_by_attribute,
    select_nodes_by_layer, select_edges_by_attribute,
    select_edges_by, tokens2text,
    get_pointing_chains, get_top_level_layers)
from discoursegraphs.readwrite import (
    read_anaphoricity, write_brackets, write_brat, read_conano, read_conll, write_conll,
    read_decour, write_dot, read_exb, read_exmaralda, write_exmaralda, write_exb,
    read_exportxml, write_graphml, write_gexf, read_mmax2,
    write_neo4j, write_geoff, write_paula,
    read_ptb, read_mrg,
    read_rst, read_rs3, read_dis, read_tiger)
from discoursegraphs.readwrite.dot import print_dot
from discoursegraphs.statistics import info
from discoursegraphs.util import xmlprint, make_labels_explicit, find_files


SRC_ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

def get_package_root_dir(src_root_dir=SRC_ROOT_DIR):
    """return the path to the root directory of this package.

    This clumsy function allows me to distribute a data directory with my
    package (specified via the ``data_files`` parameter of
    ``setuptools.setup``), no matter if it is installed via setup.py or
    a ``requirements.txt`` file.
    """
    parentdir_path = os.path.abspath(os.path.join(SRC_ROOT_DIR, os.pardir))
    dirname = os.path.basename(parentdir_path)
    if dirname.startswith('discoursegraphs') and dirname.endswith('.egg'):
        # package was installed via setup.py
        return parentdir_path
    else:  # software was installed via requirements.txt
        grandparentdir_path = os.path.abspath(
            os.path.join(SRC_ROOT_DIR, os.pardir, os.pardir))
        return grandparentdir_path


PACKAGE_ROOT_DIR = get_package_root_dir(SRC_ROOT_DIR)
DATA_ROOT_DIR = os.path.join(PACKAGE_ROOT_DIR, 'data')

# corpora can't be imported before root dirs and ``find_files`` are known
from discoursegraphs import corpora
