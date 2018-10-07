#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module converts a *.hilda file (i.e. the output of the HILDA RST parser
into a HILDARSTTree.
"""

import argparse
import re
import sys
import os

from nltk.tree import Tree

from discoursegraphs.readwrite.rst import RSTBaseTree
from discoursegraphs.readwrite.tree import DGParentedTree, word_wrap_tree

# relation name followed by nuclearity of its child notes, e.g. Contrast[S][N]
HILDA_REL_RE = re.compile(r"^(.*)\[(N|S)\]\[(N|S)\]$")


class HILDARSTTree(RSTBaseTree):
    """A HILDARSTTree is a DGParentedTree representation (Rhetorical Structure tree)
    parsed from a .hilda file."""
    def __init__(self, hilda_filepath, word_wrap=0, debug=False):
        self.debug = debug
        self.filepath = hilda_filepath

        with open(hilda_filepath, 'r') as hilda_file:
            hilda_str = hilda_file.read()
            self.hildafile_tree = self.hildastr2hildatree(hilda_str)

            tree = self.hildatree2dgparentedtree()
            self.tree = word_wrap_tree(tree, width=word_wrap)

    @staticmethod
    def hildastr2hildatree(parse_tree_str):
        """convert the output of the HILDA RST parser into a DGParentedTree
        representation of that parse tree.

        Parameters:
        parse_tree_str : str
            HILDA RST parser output

        Returns:
        tree : nltk.tree.Tree
            parse tree object of HILDA's output string
        """
        # This is basically a poor man's typecast.
        # (ParseTree is a subclass of nltk.tree.ParentedTree that is only used by HILDA.
        # DGParentedTree is a subclass of nltk.tree.ParentedTree that is only used by discoursegraphs.)
        parented_tree_str = re.sub('ParseTree', 'Tree', parse_tree_str)
        # Try this in golang, suckers!
        return eval(parented_tree_str)

    def hildatree2dgparentedtree(self):
        """Convert the tree from HILDA's format into a conventional binary tree,
        which can be easily converted into output formats like RS3.
        """
        def transform(hilda_tree):
            """Transform a HILDA parse tree into a more conventional parse tree.

            The input tree::

                                  Contrast[S][N]
                         _______________|______________
                  Although they                  they accepted
                did n't like it ,                 the offer .

            is converted into::

                                  Contrast
                         ____________|___________
                        S                        N
                        |                        |
                  Although they            they accepted
                did n't like it ,           the offer .
            """
            if isinstance(hilda_tree, basestring) or not hasattr(hilda_tree, 'label'):
                return hilda_tree
            assert len(hilda_tree) == 2, "We can only handle binary trees."

            match = HILDA_REL_RE.match(hilda_tree.label())
            assert match, "Relation '{}' does not match regex '{}'".format(hilda_tree.label(), HILDA_REL_RE)
            relname, left_child_nuc, right_child_nuc = match.groups()
            hilda_tree._label = relname

            for i, child_nuclearity in enumerate([left_child_nuc, right_child_nuc]):
                child = hilda_tree[i]
                hilda_tree[i] = Tree(child_nuclearity, [transform(child)])
            return hilda_tree

        tree = transform(self.hildafile_tree)
        return DGParentedTree.convert(tree)


# pseudo-function to create a document tree from a RST (.hilda) file
read_hilda = HILDARSTTree


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file',
                        help='*.hilda RST file to be converted')
    args = parser.parse_args(sys.argv[1:])

    assert os.path.isfile(args.input_file), \
        "'{}' isn't a file".format(args.input_file)

    HILDARSTTree(args.input_file).pretty_print()
