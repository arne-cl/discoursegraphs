#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""Basic tests for the ``rs3tree`` module"""

import os

import pytest

from discoursegraphs import t
from discoursegraphs.readwrite.rst.rs3 import RSTTree
import discoursegraphs as dg


def example2tree(rs3tree_example_filename):
    """Return the absolute path of an example file."""
    filepath = os.path.join(dg.DATA_ROOT_DIR, 'rs3tree',
                            rs3tree_example_filename)
    return RSTTree(filepath)


def test_segments_only_trees():
    """Files without a single root must get a virtual one."""
    # minimal case: file without any segments
    produced = example2tree("empty.rs3")
    expected = t("")

    assert expected == produced.tree

    # one segment only
    produced = example2tree('only-one-segment.rs3')
    expected = t("foo")

    assert expected == produced.tree

    # two segments w/out a root
    produced = example2tree("foo-bar-only-segments.rs3")
    expected = t("virtual-root",
                 [("N", "foo"), ("N", "bar")])

    assert expected == produced.tree

    # three segments w/out a root
    produced = example2tree('eins-zwei-drei-only-segments.rs3')
    expected = t("virtual-root",
                 [("N", "eins"), ("N", "zwei"), ("N", "drei")])

    assert expected == produced.tree


def test_single_nucsat_relation():
    produced = example2tree("foo-bar-circ-foo-to-bar.rs3")
    expected = t("circumstance", [
        ("S", "foo"),
        ("N", "bar")])

    assert expected == produced.tree

    produced = example2tree("foo-bar-elab-foo-to-bar.rs3")
    expected = t("elaboration", [
        ("S", "foo"),
        ("N", "bar")])

    assert expected == produced.tree

    produced = example2tree("foo-bar-circ-bar-to-foo.rs3")
    expected = t("circumstance", [
        ("N", "foo"),
        ("S", "bar")])

    assert expected == produced.tree

    produced = example2tree("foo-bar-elab-bar-to-foo.rs3")
    expected = t("elaboration", [
        ("N", "foo"),
        ("S", "bar")])

    assert expected == produced.tree


def test_single_nucsat_relation_topspan():
    """It doesn't matter if there is a span above a single N-S relation."""
    produced1 = example2tree("foo-bar-circ-foo-to-bar-plus-top-span.rs3")
    expected1 = t("circumstance", [
        ("S", "foo"),
        ("N", "bar")])
    assert expected1 == produced1.tree

    produced2 = example2tree("foo-bar-circ-foo-to-bar.rs3")
    expected2 = t("circumstance", [
        ("S", "foo"),
        ("N", "bar")])
    assert expected2 == produced2.tree
    assert produced1.tree == produced2.tree


def test_single_nucnuc_relation():
    produced = example2tree("foo-bar-foo-joint-bar.rs3")
    expected = t("joint", [
        ("N", "foo"),
        ("N", "bar")])

    assert expected == produced.tree

    produced = example2tree("foo-bar-foo-conj-bar.rs3")
    expected = t("conjunction", [
        ("N", "foo"),
        ("N", "bar")])

    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(joint-eins-and-zwei-and-drei).rs3')
    expected = t("joint", [
        ("N", "eins"),
        ("N", "zwei"),
        ("N", "drei")])

    assert expected == produced.tree


def test_nested_nucsat_relation():
    produced = example2tree('eins-zwei-drei-(circ-(circ-eins-to-zwei)-from-drei).rs3')
    expected = t("circumstance", [
        ("N", [
            ("circumstance", [
                ("S", "eins"),
                ("N", "zwei")])]),
        ("S", "drei")])

    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(circ-(circ-eins-from-zwei)-from-drei).rs3')
    expected = t("circumstance", [
        ("N", [
            ("circumstance", [
                ("N", "eins"),
                ("S", "zwei")])]),
        ("S", "drei")])

    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(circ-(circ-eins-from-zwei)-to-drei).rs3')
    expected = t("circumstance", [
        ("S", [
            ("circumstance", [
                ("N", "eins"),
                ("S", "zwei")])]),
        ("N", "drei")])

    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(circ-(circ-eins-to-zwei)-to-drei.rs3')
    expected = t("circumstance", [
        ("S", [
            ("circumstance", [
                ("S", "eins"),
                ("N", "zwei")])]),
        ("N", "drei")])

    assert expected == produced.tree


def test_nested_nucsat_nucnuc_relation():
    produced = example2tree('eins-zwei-drei-(circ-eins-to-(joint-zwei-and-drei).rs3')
    expected = t("circumstance", [
        ("S", "eins"),
        ("N", [
            ("joint", [
                ("N", "zwei"),
                ("N", "drei")])])])

    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(circ-(joint-eins-and-zwei)-from-drei).rs3')
    expected = t("circumstance", [
        ("N", [
            ("joint", [
                ("N", "eins"),
                ("N", "zwei")
            ])
        ]),
        ("S", "drei")])

    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(circ-eins-from-(joint-zwei-and-drei).rs3')
    expected = t("circumstance", [
        ("N", "eins"),
        ("S", [
            ("joint", [
                ("N", "zwei"),
                ("N", "drei")])])])

    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(circ-(joint-eins-and-zwei)-to-drei).rs3')
    expected = t("circumstance", [
        ("S", [
            ("joint", [
                ("N", "eins"),
                ("N", "zwei")
            ])
        ]),
        ("N", "drei")])

    assert expected == produced.tree

    produced = example2tree('eins-zwei-drei-(elab-eins-from-(joint-zwei-and-drei).rs3')
    expected = t('elaboration', [
        ("N", "eins"),
        ("S", [
            ("joint", [
                ("N", "zwei"),
                ("N", "drei")
            ])
        ])
    ])

    assert expected == produced.tree
