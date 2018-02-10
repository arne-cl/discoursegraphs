#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""Basic tests for the ``rs3`` module"""

import logging
import os
from tempfile import NamedTemporaryFile

import pytest

import discoursegraphs as dg
from discoursegraphs.corpora import pcc
from discoursegraphs.readwrite.rst.rs3 import RS3FileWriter, RSTTree
from discoursegraphs.readwrite.tree import DGParentedTree, t


DOC_ID = 'maz-9852'
RS3TREE_DIR = os.path.join(dg.DATA_ROOT_DIR, 'rs3tree')
RS3_TEST_FILE = os.path.join(pcc.path, 'rst/{}.rs3'.format(DOC_ID))
RS3_GRAPH = dg.read_rs3(RS3_TEST_FILE)


def example2tree(rs3tree_example_filename, rs3tree_dir=RS3TREE_DIR, debug=False):
    """Given the filename of an rs3 file and its directory, return an RSTTree instance of it."""
    filepath = os.path.join(rs3tree_dir, rs3tree_example_filename)
    return RSTTree(filepath, debug=debug)


def test_create_empty_rstgraph():
    assert isinstance(dg.readwrite.rst.rs3.RSTGraph(),
                      dg.readwrite.rst.rs3.RSTGraph)


def test_default_rstgraph_construction():
    assert RS3_GRAPH.name == '{}.rs3'.format(DOC_ID)

    assert RS3_GRAPH.ns == 'rst'
    assert RS3_GRAPH.tokenized == True
    assert len(RS3_GRAPH.tokens) == 192
    assert len(RS3_GRAPH.segments) == len(RS3_GRAPH.edus) == 21


def test_rstgraph_with_custom_name():
    docname = 'rstdoc'
    rdg = dg.read_rs3(RS3_TEST_FILE, name=docname)
    assert rdg.name == docname


def test_rstgraph_without_tokenization():
    rdg_untok = dg.read_rs3(RS3_TEST_FILE, tokenize=False)
    assert rdg_untok.tokenized == False
    assert rdg_untok.tokens == []


def test_rstgraph_with_precendence_relations():
    rdg_prec = dg.read_rs3(RS3_TEST_FILE, precedence=True)
    num_of_prec_rels = len(
        list(dg.select_edges_by(rdg_prec, layer='rst:precedence')))
    assert len(rdg_prec.tokens) == num_of_prec_rels == 192

def test_rstgraph_str_representation():
    rst_str = RS3_GRAPH.__str__()[:67]
    assert rst_str == \
        ('(file) name: {0}.rs3\nnumber of segments: {1}\n'
         'is tokenized: {2}'.format(DOC_ID, len(RS3_GRAPH.segments),
                                    RS3_GRAPH.tokenized))

def test_get_edus():
    RS3_GRAPH.edus == dg.readwrite.rst.rs3.rs3graph.get_edus(RS3_GRAPH)


def test_get_rst_relation_root_nodes():
    rst_relation_root_nodes = \
        list(dg.readwrite.rst.rs3.rs3graph.get_rst_relation_root_nodes(RS3_GRAPH, data=False))
    rst_relation_root_nodes_with_data = \
        list(dg.readwrite.rst.rs3.rs3graph.get_rst_relation_root_nodes(RS3_GRAPH))

    assert all((isinstance(node, str)
                for node in rst_relation_root_nodes))
    all(((isinstance(node, tuple) and len(node) == 3)
         for node in rst_relation_root_nodes_with_data))
    assert len(rst_relation_root_nodes_with_data) == len(rst_relation_root_nodes) == 15


def test_get_rst_relations():
    from collections import defaultdict
    rst_rels = dg.readwrite.rst.rs3.rs3graph.get_rst_relations(RS3_GRAPH)

    assert isinstance(rst_rels, defaultdict)

    possible_keys = ('tokens', 'nucleus', 'satellites', 'multinuc')
    for rst_rel_node in rst_rels:
        assert set(rst_rels[rst_rel_node].keys()).intersection(possible_keys)


def test_get_rst_spans():
    rst_spans = dg.readwrite.rst.rs3.rs3graph.get_rst_spans(RS3_GRAPH)
    assert isinstance(rst_spans, list)
    all(((len(span) == 5 and isinstance(span, tuple))
         for span in rst_spans))


def test_select_nodes_by_layer():
    """Are RST nodes correctly filtered based on their layer?"""
    rst_filepath = os.path.join(pcc.path, 'rst/maz-10374.rs3')
    rdg = dg.read_rst(rst_filepath)
    rst_node_ids = list(dg.select_nodes_by_layer(rdg, 'rst'))
    rst_nodes = list(dg.select_nodes_by_layer(rdg, 'rst', data=True))
    assert len(rdg) == len(rst_node_ids) == len(rst_nodes) == 195


def test_rs3filewriter_emptytree():
    """An empty DGParentedTree is converted into an empty RS3 file and back."""
    input_tree = t("", [])
    expected_output_tree = example2tree("empty.rs3")

    tempfile = NamedTemporaryFile()
    RS3FileWriter(input_tree, output_filepath=tempfile.name)
    produced_output_tree = RSTTree(tempfile.name)

    assert produced_output_tree.edu_strings == produced_output_tree.tree.leaves() == []
    assert input_tree == expected_output_tree.tree == produced_output_tree.tree


def test_rs3filewriter_onesegmenttree():
    """A DGParentedTree with only one segment is correctly converted into an RS3 file and back."""
    input_tree = t("N", ["foo"])
    expected_output_tree = example2tree('only-one-segment.rs3')

    tempfile = NamedTemporaryFile()
    RS3FileWriter(input_tree, output_filepath=tempfile.name)
    produced_output_tree = RSTTree(tempfile.name)

    assert produced_output_tree.edu_strings == produced_output_tree.tree.leaves() == ['foo']
    assert input_tree == expected_output_tree.tree == produced_output_tree.tree


def test_rs3filewriter_onesegmenttree_umlauts():
    """A DGParentedTree with only one segment with umlauts is correctly
    converted into an RS3 file and back.
    """
    edu_string = u"Über sein östliches Äußeres"
    input_tree = t("N", [edu_string])
    expected_output_tree = example2tree('only-one-segment-with-umlauts.rs3')

    tempfile = NamedTemporaryFile()
    RS3FileWriter(input_tree, output_filepath=tempfile.name)
    produced_output_tree = RSTTree(tempfile.name)

    assert expected_output_tree.edu_strings == \
        produced_output_tree.edu_strings == \
        produced_output_tree.tree.leaves() == [edu_string]
    assert input_tree == expected_output_tree.tree == produced_output_tree.tree



def test_rs3filewriter_nucsat():
    """A DGParentedTree with one nuc-sat relation is correctly converted into an RS3 file and back."""
    input_tree = t("circumstance", [
        ("S", ["foo"]),
        ("N", ["bar"])])
    expected_output_tree = example2tree("foo-bar-circ-foo-to-bar.rs3")

    tempfile = NamedTemporaryFile()
    RS3FileWriter(input_tree, output_filepath=tempfile.name)
    produced_output_tree = RSTTree(tempfile.name)

    assert produced_output_tree.edu_strings == produced_output_tree.tree.leaves() == ['foo', 'bar']
    assert input_tree == expected_output_tree.tree == produced_output_tree.tree

    input_tree = t("circumstance", [
        ("N", ["foo"]),
        ("S", ["bar"])])
    expected_output_tree = example2tree("foo-bar-circ-bar-to-foo.rs3")

    tempfile = NamedTemporaryFile()
    RS3FileWriter(input_tree, output_filepath=tempfile.name)
    produced_output_tree = RSTTree(tempfile.name)

    assert produced_output_tree.edu_strings == produced_output_tree.tree.leaves() == ['foo', 'bar']
    assert input_tree == expected_output_tree.tree == produced_output_tree.tree


def test_rs3filewriter_nested():
    """A DGParentedTree with a multinuc relation nested in a nuc-sat relation
    is correctly converted into an RS3 file and back."""
    input_tree = t('elaboration', [
        ('N', ['eins']),
        ('S', [
            ('joint', [
                ('N', ['zwei']),
                ('N', ['drei'])])])])
    expected_output_tree = example2tree('eins-zwei-drei-(elab-eins-from-(joint-zwei-and-drei).rs3')

    tempfile = NamedTemporaryFile()
    RS3FileWriter(input_tree, output_filepath=tempfile.name)
    produced_output_tree = RSTTree(tempfile.name)

    assert produced_output_tree.edu_strings == produced_output_tree.tree.leaves() == ['eins', 'zwei', 'drei']
    assert input_tree == expected_output_tree.tree == produced_output_tree.tree


def test_rs3filewriter_pcc_10575():
    """PCC rs3 file 10575 can be converted rs3 -> dgtree -> rs3' -> dgtree',
    without information loss between dgtree and dgtree'.
    """
    input_tree = t('interpretation', [
        ('N', [
            ('circumstance', [
                ('S', ['eins']),
                ('N', [
                    ('contrast', [
                        ('N', ['zwei']),
                        ('N', [
                            ('cause', [
                                ('N', ['drei']),
                                ('S', ['vier'])])])])])])]),
        ('S', ['fuenf'])])
    expected_output_tree = example2tree('maz-10575-excerpt.rs3')

    tempfile = NamedTemporaryFile()
    RS3FileWriter(input_tree, output_filepath=tempfile.name)
    produced_output_tree = RSTTree(tempfile.name)

    assert produced_output_tree.edu_strings == produced_output_tree.tree.leaves() == ['eins', 'zwei', 'drei', 'vier', 'fuenf']
    assert input_tree == expected_output_tree.tree == produced_output_tree.tree


def test_rs3filewriter_complete_pcc_stats():
    """All *.rs3 files can be parsed into a DGParentedTree (T1), converted back
    into *.rs3 files and parsed back into a DGParentedTree (T2), with T1 == T2.
    """
    okay = 0.0
    fail = 0.0

    for i, rfile in enumerate(dg.corpora.pcc.get_files_by_layer('rst')):
        try:
            # rs3 -> dgtree
            expected_output_tree = RSTTree(rfile)

            tempfile = NamedTemporaryFile()
            # dgtree -> rs3'
            RS3FileWriter(expected_output_tree, output_filepath=tempfile.name, debug=False)
            # rs3' -> dgtree'
            produced_output_tree = RSTTree(tempfile.name)

            assert expected_output_tree.edu_strings == expected_output_tree.tree.leaves() \
                == produced_output_tree.edu_strings == produced_output_tree.tree.leaves()
            assert expected_output_tree.tree == produced_output_tree.tree
            okay += 1

        except Exception as e:
            logging.log(logging.WARN,
                    "File '{0}' can't be loop-converted: {1}".format(
                        os.path.basename(rfile), e))
            fail += 1

    success_rate = okay / (okay+fail) * 100
    assert success_rate == 100, \
        "{0}% of PCC files could be loop-converted ({1} of {2})".format(success_rate, okay, okay+fail)
