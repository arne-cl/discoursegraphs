#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module converts a *.stagedp file (i.e. the output of the StageDP
RST parser (Wang et al. 2017).
"""

import argparse
import re
import sys
import os

from nltk.tree import Tree

from discoursegraphs.readwrite.rst import RSTBaseTree
from discoursegraphs.readwrite.tree import DGParentedTree, t, word_wrap_tree

# nuclearity of the child nodes, followed by the relation name, e.g. 'NS-Contrast'
STAGEDP_REL_RE = re.compile(r"^(N|S)(N|S)-(.*)$")


class StageDPRSTTree(RSTBaseTree):
    """A StageDPRSTTree is a DGParentedTree representation (Rhetorical Structure tree)
    parsed from a .stagedp file."""
    def __init__(self, stagedp_filepath, word_wrap=0):
        self.filepath = stagedp_filepath

        with open(stagedp_filepath, 'r') as stagedp_file:
            stagedp_str = stagedp_file.read()
            self.stagedp_file_tree = self.stagedp2tree(stagedp_str)
            tree = self.stagedptree2dgparentedtree()
            self.tree = word_wrap_tree(tree, width=word_wrap)
 
    def stagedp2tree(self, parse_string):
        """convert the output of the StageDP RST parser into a DGParentedTree
        representation of that parse tree.

        Parameters:
        parse_tree_str : str
            StageDP RST parser output

        Returns:
        tree : nltk.tree.Tree
            parse tree object of StageDP's output string
        """
        tree = Tree.fromstring(parse_string)

        for i, leaf in enumerate(tree.leaves()):
            leaf_pos = tree.leaf_treeposition(i)
            tree[leaf_pos] = self.cleanup_edu_text(tree[leaf_pos])
        return tree   

    @staticmethod
    def cleanup_edu_text(text):
        """Given a StageDP-formatted EDU, return a human-readable version without markup."""
        return ' '.join(tok for tok in text[2:-2].split('_')
                        if tok not in ('<P>', '<S>'))

    def stagedptree2dgparentedtree(self):
        """Convert the tree from StageDP's format into a conventional binary tree,
        which can be easily converted into output formats like RS3.
        """
        def transform(stagedp_tree, is_tree_root=False):
            """Transform a StageDP parse tree into a more conventional parse tree.

            The input tree::

                                NS-Explanation                 
                        _______________|_______________          
                      EDU                             EDU       
                       |                               |         
                 They did n't                   Two weeks later 
                like the offer .                they were found 
                                                     dead .

            is converted into::

                                   Explanation                 
                        _______________|_______________          
                       N                               S       
                       |                               |         
                 They did n't                   Two weeks later 
                like the offer .                they were found 
                                                     dead .
            """
            if isinstance(stagedp_tree, basestring) or not hasattr(stagedp_tree, 'label'):
                return stagedp_tree

            if len(stagedp_tree) == 1:
                assert stagedp_tree.label() == 'EDU'
                if is_tree_root: 
                    # This is not really an RST tree, but parsers sometimes produce output
                    # that only consists of one EDU.
                    #
                    # TODO/FIXME: only do this if this tree has no parent
                    # either by using a parented tree, or, if that's not possible,
                    # by adding a parameter to the recursive transform() func
                    stagedp_tree.set_label('N')
                    return stagedp_tree
                else:  # a leaf nucleus or satellite
                    return stagedp_tree[0] # we remove the 'EDU' node above the actual leaf node

            elif len(stagedp_tree) == 2:  # handle normal binary tree case 
                match = STAGEDP_REL_RE.match(stagedp_tree.label())
                assert match, "Relation '{}' does not match regex '{}'".format(stagedp_tree.label(), STAGEDP_REL_RE)
                left_child_nuc, right_child_nuc, relname = match.groups()
                stagedp_tree.set_label(relname)

                for i, child_nuclearity in enumerate([left_child_nuc, right_child_nuc]):
                    transformed_child_tree = transform(stagedp_tree[i])
                    stagedp_tree[i] = Tree(child_nuclearity, [transformed_child_tree])
                return stagedp_tree
            else:
                raise ValueError("We can't handle trees with more than two children.")

        # ~ import pudb; pudb.set_trace()
        tree = transform(self.stagedp_file_tree, is_tree_root=True)
        return DGParentedTree.convert(tree)


# pseudo-function to create a document tree from a RST (.stagedp) file
read_stagedp = StageDPRSTTree


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file',
                        help='*.stagedp RST file to be converted')
    args = parser.parse_args(sys.argv[1:])

    assert os.path.isfile(args.input_file), \
        "'{}' isn't a file".format(args.input_file)

    StageDPRSTTree(args.input_file).pretty_print()

