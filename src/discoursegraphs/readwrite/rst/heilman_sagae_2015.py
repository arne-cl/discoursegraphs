#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module converts a the output of the Heilman and Sagae (2015) discoure
parser into a networkx-based directed graph (``DiscourseDocumentGraph``).

This module contains some MIT licensed code from
github.com/EducationalTestingService/discourse-parsing .
"""

import os
from collections import defaultdict
import json
import re

import nltk
from nltk.tree import Tree, ParentedTree

from discoursegraphs import DiscourseDocumentGraph, EdgeTypes
from discoursegraphs.readwrite.rst import RSTBaseTree
from discoursegraphs.readwrite.tree import DGParentedTree, word_wrap_tree, t


HS2015_REL_RE = re.compile(r"^(?P<nuclearity>nucleus|satellite):(?P<relname>.*)$")


def get_class_attribs(my_class):
    return [elem for elem in dir(my_class)
            if elem not in ('__doc__', '__module__')]


class SubtreeType:
    """Enum class of subtree types"""
    root = 'root'
    nucleus = 'nucleus'
    satellite = 'satellite'
    text = 'text'
    leaf = 'leaf'

SUBTREE_TYPES = get_class_attribs(SubtreeType)


class NucType:
    """Enum class of nuclearity types"""
    nucsat = 'nucsat'  # 1 nuc, 1 sat
    multinuc = 'multinuc'  # 2+ nucs, no satellites
    multisat = 'multisat'  # 1 nuc, 2+ satellites
    edu = 'edu'  # no relation, just an EDU

NUC_TYPES = get_class_attribs(NucType)


class HS2015RSTTree(RSTBaseTree):
    """A HS2015RSTTree is a DGParentedTree representation (Rhetorical Structure tree)
    parsed from a .hs2015 file."""
    def __init__(self, hs2015_filepath, word_wrap=0, debug=False):
        self.debug = debug
        self.filepath = hs2015_filepath

        self.hs2015file_tree, self.edus = parse_hs2015(hs2015_filepath)

        tree = self.hs2015tree2dgparentedtree()
        self.tree = word_wrap_tree(tree, width=word_wrap)

    def hs2015tree2dgparentedtree(self):
        """Convert the tree from Heilman/Sagae 2015 format into a conventional binary tree,
        which can be easily converted into output formats like RS3.
        """
        def transform(hs2015_tree):
            """Transform a HS2015 parse tree into a more conventional parse tree.

            The input tree::

                                 ROOT
                        __________|________
                satellite:contra      nucleus:span
                       st                  |
                       |                   |
                      text                text
                       |                   |
                    Although              they
                    they did            accepted
                    n't like           the offer
                      it ,                 .

                                  Contrast
                         ____________|___________
                        S                        N
                        |                        |
                  Although they            they accepted
                did n't like it ,           the offer .
            """
            if is_leaf_node(hs2015_tree):
                return hs2015_tree

            tree_type = get_tree_type(hs2015_tree)
            if tree_type in (SubtreeType.root, SubtreeType.nucleus, SubtreeType.satellite):
                child_types = get_child_types(hs2015_tree)
                rel_nuc_type = get_nuclearity_type(child_types)
                if rel_nuc_type == NucType.nucsat:
                    nuc_id = child_types['nucleus'][0]
                    sat_id = child_types['satellite'][0]
                    return get_nucsat_subtree(hs2015_tree, nuc_id, sat_id)

                elif rel_nuc_type == NucType.multinuc:
                    transformed_subtrees = [Tree('N', [transform(st)]) for st in hs2015_tree]
                    # in a multinuc, all nucs will carry the relation name
                    relname = get_capitalized_relname(hs2015_tree, 0)
                    return Tree(relname, transformed_subtrees)

                elif rel_nuc_type == NucType.multisat:
                    # In RST, multiple satellites (at least adjacent ones)
                    # can be in a relation with the same nucleus.
                    # To express this in a tree, we convert this schema to
                    # a left-branching structure, e.g. (((N S) S) S).
                    nuc_id = child_types['nucleus'][0]
                    first_sat_id in child_types['satellite'][0]

                    multisat_subtree = get_nucsat_subtree(hs2015_tree, nuc_id, first_sat_id)
                    for sat_id in child_types['satellite'][1:]:
                        sat_subtree = hs2015_tree[sat_id]
                        relname = get_capitalized_relname(hs2015_tree, sat_id)
                        multisat_subtree = Tree(relname, [
                            Tree('N', [multisat_subtree]),
                            Tree('S', [transform(sat_subtree)])
                        ])
                    return multisat_subtree

                elif rel_nuc_type == NucType.edu:
                    # return the EDU text string
                    return hs2015_tree[0][0]

                else:
                    raise ValueError("Unknown nuclearity type: {}".format(rel_nuc_type))

            else:
                assert tree_type == SubtreeType.text

        def get_nucsat_subtree(tree, nuc_id, sat_id):
            nuc_subtree = tree[nuc_id]
            sat_subtree = tree[sat_id]
            relname = get_capitalized_relname(tree, sat_id)

            # determine order of subtrees
            if nuc_id < sat_id:
                return Tree(relname, [
                    Tree('N', [transform(nuc_subtree)]),
                    Tree('S', [transform(sat_subtree)])
                ])
            else:
                return Tree(relname, [
                    Tree('S', [transform(sat_subtree)]),
                    Tree('N', [transform(nuc_subtree)])
                ])

        tree = transform(self.hs2015file_tree)
        return DGParentedTree.convert(tree)


def get_capitalized_relname(tree, subtree_index):
    """Returns the capitalized relation name from a tree's satellite
    subtree label, e.g. 'satellite:contrast' becomes 'Contrast'.
    """
    match = HS2015_REL_RE.match(tree[subtree_index].label())
    relname = match.group('relname')
    return relname.capitalize()


def parse_hs2015(heilman_filepath):
    """convert the output of the Heilman and Sagae (2015) discourse parser
    into a nltk.ParentedTree instance.

    Parameters
    ----------
    heilman_filepath : str
        path to a file containing the output of Heilman and Sagae's 2015
        discourse parser

    Returns
    -------
    parented_tree : nltk.ParentedTree
        nltk.ParentedTree representation of the given Heilman/Sagae RST tree
    edus : list(list(unicode))
        a list of EDUs, where each EDU is represented as
        a list of tokens
    """
    with open(heilman_filepath, 'r') as parsed_file:
        heilman_json = json.load(parsed_file)

    edus = heilman_json['edu_tokens']

    # the Heilman/Sagae parser can theoretically produce more than one parse,
    # but I've never seen more than one, so we'll just the that.
    scored_rst_tree = heilman_json['scored_rst_trees'][0]
    tree_str = scored_rst_tree['tree']

    parented_tree = nltk.ParentedTree.fromstring(tree_str)
    _add_edus_to_tree(parented_tree, edus)
    return parented_tree, edus


def get_edu_text(text_subtree):
    """return the text of the given EDU subtree"""
    assert text_subtree.label() == SubtreeType.text
    return u' '.join(word.decode('utf-8') for word in text_subtree.leaves())


def get_tree_type(tree):
    """Return the (sub)tree type: 'root', 'nucleus', 'satellite', 'text' or 'leaf'

    Parameters
    ----------
    tree : nltk.tree.ParentedTree
        a tree representing a rhetorical structure (or a part of it)
    """
    if is_leaf_node(tree):
        return SubtreeType.leaf

    tree_type = tree.label().lower().split(':')[0]
    assert tree_type in SUBTREE_TYPES
    return tree_type


def get_relation_type(tree):
    """Return the RST relation type attached to the parent node of an
    RST relation, e.g. `span`, `elaboration` or `antithesis`.

    Parameters
    ----------
    tree : nltk.tree.ParentedTree
        a tree representing a rhetorical structure (or a part of it)

    Returns
    -------
    relation_type : str
        the type of the rhetorical relation that this (sub)tree represents
    """
    return tree.label().split(':')[1]


def get_child_types(tree):
    """Take a tree and check what types of children (i.e. 'nucleus' or
    'satellite') it has. Returns a map from child tree type to the indices of
    all children with that type.
    """
    child_types = defaultdict(list)
    for i, child in enumerate(tree):
        child_types[get_tree_type(child)].append(i)
    return child_types


def get_nuclearity_type(child_types):
    """Returns the nuclearity type of an RST relation (i.e. 'multinuc',
    'nucsat' or 'multisat') or 'edu' if the node is below the relation
    level.
    """
    if 'text' in child_types and len(child_types) == 1:
        return NucType.edu

    assert 'nucleus' in child_types, \
        "This is not a relational node. child_types: {}".format(child_types)

    if 'satellite' not in child_types:
        assert len(child_types['nucleus']) > 1
        return NucType.multinuc

    else:  # 'satellite' in child_types
        assert len(child_types['nucleus']) == 1
        if len(child_types['satellite']) == 1:
            return NucType.nucsat
        else:
            assert len(child_types['satellite']) > 1
            return NucType.multisat


def get_node_type(tree):
    """Return the node type ('leaf' or 'span') of a subtree
    (i.e. a nucleus or a satellite).

    Parameters
    ----------
    tree : nltk.tree.ParentedTree
        a tree representing a rhetorical structure (or a part of it)
    """
    return SubtreeType.leaf if tree[0].label() == SubtreeType.text else 'span'


def is_leaf_node(tree):
    """Return True iff the given tree is a leaf node (i.e. a string the
    contains the tokens of an EDU).

    Parameters
    ----------
    tree : nltk.tree.ParentedTree or basestring
        a tree representing a rhetorical structure (or a part of it) OR
        an EDU
    """
    return isinstance(tree, basestring) or not hasattr(tree, 'label')


def _add_edus_to_tree(parented_tree, edus):
    """replace EDU indices with the text of the EDUs
    in a parented tree.

    Parameters
    ----------
    parented_tree : nltk.ParentedTree
        a parented tree that only contains EDU indices
        as leaves
    edus : list(list(unicode))
        a list of EDUs, where each EDU is represented as
        a list of tokens
    """
    for i, child in enumerate(parented_tree):
        if isinstance(child, nltk.Tree):
            _add_edus_to_tree(child, edus)
        else:
            edu_index = int(child)
            edu_tokens = edus[edu_index]
            parented_tree[i] = u" ".join(edu_tokens)


# pseudo-function to create a ParentedTree from a RST (HS2015) file
read_hs2015tree = HS2015RSTTree


if __name__ == '__main__':
    generic_converter_cli(RSTHS2015DocumentGraph, 'RST (rhetorical structure)')


