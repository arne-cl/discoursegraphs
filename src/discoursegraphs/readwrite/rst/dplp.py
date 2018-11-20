#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module converts the output of the DPLP RST parser into a DPLPRSTTree.
"""

import argparse
from collections import defaultdict
import re
import sys
import os

from nltk.tree import Tree, ParentedTree

from discoursegraphs.readwrite.tree import DGParentedTree, word_wrap_tree

# nuclearity of child nodes followed by their parent relation name, e.g. NS-elaboration
DPLP_REL_RE = re.compile(r"^(N|S)(N|S)-(.*)$")


class DPLPRSTTree(object):
    """A DPLPRSTTree is a DGParentedTree representation (Rhetorical Structure tree)
    parsed from the DPLP's parser output"""
    def __init__(self, dplp_filepath, word_wrap=0, debug=False):
        self.debug = debug

        merge_file_str, parsetree_str = self.split_input(dplp_filepath)
        
        # FIXME: dplpstr2dplptree output is no longer a tree
        self.parsetree = self.dplpstr2dplptree(parsetree_str)
        self.edus = self.extract_edus(merge_file_str)

        self.add_edus()
        tree = self.dplptree2dgparentedtree()
        self.tree = word_wrap_tree(tree, width=word_wrap)

    def split_input(self, input_filepath):
        """Splits the input file into the 'merge file' (which contains
        the EDUs) and the 'parsetree file'."""
        with open(input_filepath, 'r') as input_file:
            input_file_str = input_file.read()
            merge_file_str, parsetree_str = input_file_str.split('ParentedTree', 1)
            return merge_file_str, 'ParentedTree' + parsetree_str

    @staticmethod
    def dplpstr2dplptree(parse_tree_str):
        """convert the output of the DPLP RST parser into a DGParentedTree
        representation of that parse tree.

        Parameters:
        parse_tree_str : str
            DPLP RST parser output

        Returns:
        tree : nltk.tree.Tree
            parse tree object of DPLP's output string
        """
        # This is basically a poor man's typecast used to avoid errors like:
        # ValueError: Can not insert a subtree that already has a parent.
        parented_tree_str = re.sub('ParentedTree', 'Tree', parse_tree_str)
        return eval(parented_tree_str)


    @staticmethod
    def extract_edus(merge_file_str):
        """Extract EDUs from DPLPs .merge output files.

        Returns
        -------
        edus : dict from EDU IDs (int) to words (list(str))
        """
        lines = merge_file_str.splitlines()

        edus = defaultdict(list)
        for line in lines:
            if line.strip():  # ignore empty lines
                token = line.split('\t')[2]
                edu_id = int(line.split('\t')[9])
                edus[edu_id].append(token)
        return edus

    def add_edus(self):
        leaf_positions = self.parsetree.treepositions('leaves')

        for leaf_pos in leaf_positions:
            edu_id = int(self.parsetree[leaf_pos])
            edu_tokens = self.edus[edu_id]
            parent_pos = leaf_pos[:-1]
            self.parsetree[parent_pos] = u" ".join(edu_tokens)

    def dplptree2dgparentedtree(self):
        """Convert the tree from DPLP's format into a conventional binary tree,
        which can be easily converted into output formats like RS3.
        """
        def transform(dplp_tree):
            """Transform a DPLP parse tree into a more conventional parse tree."""
            if isinstance(dplp_tree, basestring) or not hasattr(dplp_tree, 'label'):
                return dplp_tree
            assert len(dplp_tree) == 2, "We can only handle binary trees."

            match = DPLP_REL_RE.match(dplp_tree.label())
            assert match, "Relation '{}' does not match regex '{}'".format(dplp_tree.label(), DPLP_REL_RE)
            left_child_nuc, right_child_nuc, relname = match.groups()
            dplp_tree._label = relname

            for i, child_nuclearity in enumerate([left_child_nuc, right_child_nuc]):
                child = dplp_tree[i]
                dplp_tree[i] = Tree(child_nuclearity, [transform(child)])
            return dplp_tree

        tree = transform(self.parsetree)
        return DGParentedTree.convert(tree)

    def _repr_png_(self):
        """This PNG representation will be automagically used inside
        IPython notebooks.
        """
        return self.tree._repr_png_()

    def __str__(self):
        return self.tree.__str__()

    def label(self):
        """Return the label of the tree's root element."""
        return self.tree.label()

    def pretty_print(self):
        """Return a pretty-printed representation of the RSTTree."""
        return self.tree.pretty_print()

    def __getitem__(self, key):
        return self.tree.__getitem__(key)


# pseudo-function to create a document tree from a RST (.dplp) file
read_dplp = DPLPRSTTree


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('parsetree_file',
                        help='*.parsetree DPLP RST file to be converted')
    parser.add_argument('merge_file',
                        help='*.merge DPLP RST file to be converted')
    args = parser.parse_args(sys.argv[1:])

    for filename in (args.parsetree_file, args.merge_file):
        assert os.path.isfile(filename), \
            "'{}' isn't a file".format(filename)

    DPLPRSTTree(args.parsetree_file, args.merge_file).pretty_print()
