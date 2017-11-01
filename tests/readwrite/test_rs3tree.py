#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""Basic tests for the ``rs3tree`` module"""

import os

import pytest

from discoursegraphs import t
from discoursegraphs.readwrite.rst.rs3 import RSTTree
import discoursegraphs as dg


# files to test
"""
['eins-zwei-drei-(joint-eins-and-zwei-and-drei).rs3',

 'eins-zwei-drei-(circ-(circ-eins-to-zwei)-from-drei).rs3',
 'foo-bar-only-segments.rs3',
 'foo-bar-circ-foo-to-bar.rs3',
 'eins-zwei-drei-(circ-(joint-eins-and-zwei)-to-drei).rs3',
 'eins-zwei-drei-(elab-eins-from-(joint-zwei-and-drei).rs3',
 'foo-bar-foo-conj-bar.rs3',
 'eins-zwei-drei-(circ-eins-from-(joint-zwei-and-drei).rs3',
 'eins-zwei-drei-only-segments.rs3',
 'eins-zwei-drei-(circ-(circ-eins-to-zwei)-to-drei.rs3',
 'eins-zwei-drei-(circ-(joint-eins-and-zwei)-from-drei).rs3',
 'eins-zwei-drei-(circ-eins-to-(joint-zwei-and-drei).rs3',
 'foo-bar-elab-foo-to-bar.rs3',
 'foo-bar-circ-bar-to-foo.rs3',

 'foo-bar-foo-joint-bar.rs3',
 'foo-bar-elab-bar-to-foo.rs3',
 'eins-zwei-drei-(circ-(circ-eins-from-zwei)-from-drei).rs3',
 'eins-zwei-drei-(circ-(circ-eins-from-zwei)-to-drei).rs3']"""

def get_filepath(rs3tree_example_filename):
    """Return the absolute path of an example file."""
    return os.path.join(
        dg.DATA_ROOT_DIR, 'rs3tree', rs3tree_example_filename)


def test_segments_only_trees():
    """Files without a single root must get a virtual one."""

    # minimal case: file without any segments
    rs3_file = get_filepath("empty.rs3")
    produced = RSTTree(rs3_file)
    expected = t("")

    assert expected == produced.tree

    # one lonely segment
    rs3_file = get_filepath('only-one-segment.rs3')
    produced = RSTTree(rs3_file)
    expected = t("foo")

    assert expected == produced.tree

    # two segments w/out a root
    rs3_file = get_filepath("foo-bar-only-segments.rs3")
    produced = RSTTree(rs3_file)
    expected = t("virtual-root",
                 [("N", "foo"), ("N", "bar")])

    assert expected == produced.tree

    # three segments w/out a root
    rs3_file = get_filepath('eins-zwei-drei-only-segments.rs3')
    produced = RSTTree(rs3_file)
    expected = t("virtual-root",
                 [("N", "eins"), ("N", "zwei"), ("N", "drei")])

    assert expected == produced.tree
