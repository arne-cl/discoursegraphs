#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module converts a *.dis file (used by old versions of RSTTool to
annotate rhetorical structure) into a networkx-based directed graph
(``DiscourseDocumentGraph``).

This module contains some MIT licensed code from
github.com/EducationalTestingService/discourse-parsing .
"""

import os
import re
from collections import defaultdict

from nltk.tree import ParentedTree

from discoursegraphs import DiscourseDocumentGraph, EdgeTypes
from discoursegraphs.readwrite.ptb import PTB_BRACKET_MAPPING


SUBTREE_TYPES = ('Root', 'Nucleus', 'Satellite')
NODE_TYPES = ('leaf', 'span')


class RSTLispDocumentGraph(DiscourseDocumentGraph):
    """
    A directed graph with multiple edges (based on a networkx
    MultiDiGraph) that represents the rhetorical structure of a
    document. It is generated from a *.dis file.

    Attributes
    ----------
    name : str
        name, ID of the document or file name of the input file
    ns : str
        the namespace of the document (default: rst)
    root : str
        name of the document root node ID
    tokens : list of str
        sorted list of all token node IDs contained in this document graph
    """
    def __init__(self, dis_filepath, name=None, namespace='rst',
                 tokenize=True, precedence=False):
        """
        Creates an RSTLispDocumentGraph from a Rhetorical Structure *.dis file and adds metadata
        to it.

        Parameters
        ----------
        dis_filepath : str
            absolute or relative path to the Rhetorical Structure *.dis file to be
            parsed.
        name : str or None
            the name or ID of the graph to be generated. If no name is
            given, the basename of the input file is used.
        namespace : str
            the namespace of the document (default: rst)
        precedence : bool
            If True, add precedence relation edges
            (root precedes token1, which precedes token2 etc.)
        """
        # super calls __init__() of base class DiscourseDocumentGraph
        super(RSTLispDocumentGraph, self).__init__()

        self.name = name if name else os.path.basename(dis_filepath)
        self.ns = namespace
        self.root = 0
        self.add_node(self.root, layers={self.ns}, label=self.ns+':root_node')
        if 'discoursegraph:root_node' in self:
            self.remove_node('discoursegraph:root_node')

        self.tokenized = tokenize
        self.tokens = []
        self.rst_tree = self.disfile2tree(dis_filepath)
        self.parse_rst_tree(self.rst_tree)

    @staticmethod
    def disfile2tree(dis_filepath):
        """converts a *.dis file into a ParentedTree (NLTK) instance"""
        with open(dis_filepath) as f:
            rst_tree_str = f.read().strip()
            rst_tree_str = fix_rst_treebank_tree_str(rst_tree_str)
            rst_tree_str = convert_parens_in_rst_tree_str(rst_tree_str)
            return ParentedTree.fromstring(rst_tree_str)

    def parse_rst_tree(self, rst_tree, indent=0):
        """parse an RST ParentedTree into this document graph"""
        tree_type = self.get_tree_type(rst_tree)
        assert tree_type in SUBTREE_TYPES
        if tree_type == 'Root':
            span, children = rst_tree[0], rst_tree[1:]
            for child in children:
                self.parse_rst_tree(child, indent=indent+1)

        else: # tree_type in ('Nucleus', 'Satellite')
            node_id = self.get_node_id(rst_tree)
            node_type = self.get_node_type(rst_tree)
            relation_type = self.get_relation_type(rst_tree)
            if node_type == 'leaf':
                edu_text = self.get_edu_text(rst_tree[-1])
                self.add_node(node_id, attr_dict={
                    self.ns+':text': edu_text,
                    'label': u'{0}: {1}'.format(node_id, edu_text[:20])})
                if self.tokenized:
                    edu_tokens = edu_text.split()
                    for i, token in enumerate(edu_tokens):
                        token_node_id = '{0}_{1}'.format(node_id, i)
                        self.tokens.append(token_node_id)
                        self.add_node(token_node_id, attr_dict={self.ns+':token': token,
                                                                'label': token})
                        self.add_edge(node_id, '{0}_{1}'.format(node_id, i))

            else: # node_type == 'span'
                self.add_node(node_id, attr_dict={self.ns+':rel_type': relation_type,
                                                   self.ns+':node_type': node_type})
                children = rst_tree[3:]
                child_types = self.get_child_types(children)

                expected_child_types = set(['Nucleus', 'Satellite'])
                unexpected_child_types = set(child_types).difference(expected_child_types)
                assert not unexpected_child_types, \
                    "Node '{0}' contains unexpected child types: {1}\n".format(node_id, unexpected_child_types)

                if 'Satellite' not in child_types:
                    # span only contains nucleii -> multinuc
                    for child in children:
                        child_node_id = self.get_node_id(child)
                        self.add_edge(node_id, child_node_id, attr_dict={self.ns+':rel_type': relation_type})

                elif len(child_types['Satellite']) == 1 and len(children) == 1:
                    if tree_type == 'Nucleus':
                        child = children[0]
                        child_node_id = self.get_node_id(child)
                        self.add_edge(
                            node_id, child_node_id,
                            attr_dict={self.ns+':rel_type': relation_type},
                            edge_type=EdgeTypes.dominance_relation)
                    else:
                        assert tree_type == 'Satellite'
                        raise NotImplementedError("I don't know how to combine two satellites")

                elif len(child_types['Satellite']) == 1 and len(child_types['Nucleus']) == 1:
                    # standard RST relation, where one satellite is dominated by one nucleus
                    nucleus_index = child_types['Nucleus'][0]
                    satellite_index = child_types['Satellite'][0]

                    nucleus_node_id = self.get_node_id(children[nucleus_index])
                    satellite_node_id = self.get_node_id(children[satellite_index])
                    self.add_edge(node_id, nucleus_node_id, attr_dict={self.ns+':rel_type': 'span'},
                                  edge_type=EdgeTypes.spanning_relation)
                    self.add_edge(nucleus_node_id, satellite_node_id,
                                  attr_dict={self.ns+':rel_type': relation_type},
                                  edge_type=EdgeTypes.dominance_relation)
                else:
                    raise ValueError("Unexpected child combinations: {}\n".format(child_types))

                for child in children:
                    self.parse_rst_tree(child, indent=indent+1)

    def get_child_types(self, children):
        """
        maps from (sub)tree type (i.e. Nucleus or Satellite) to a list
        of all children of this type
        """
        child_types = defaultdict(list)
        for i, child in enumerate(children):
            child_types[self.get_tree_type(child)].append(i)
        return child_types

    @staticmethod
    def get_edu_text(text_subtree):
        """return the text of the given EDU subtree"""
        assert text_subtree.label() == 'text'
        return u' '.join(word.decode('utf-8') for word in text_subtree.leaves())

    @staticmethod
    def get_tree_type(tree):
        """
        returns the type of the (sub)tree: Root, Nucleus or Satellite

        Parameters
        ----------
        tree : nltk.tree.ParentedTree
            a tree representing a rhetorical structure (or a part of it)
        """
        tree_type = tree.label()
        assert tree_type in SUBTREE_TYPES
        return tree_type

    @staticmethod
    def get_node_type(tree):
        """
        returns the node type (leaf or span) of a subtree (i.e. Nucleus or Satellite)

        Parameters
        ----------
        tree : nltk.tree.ParentedTree
            a tree representing a rhetorical structure (or a part of it)
        """
        node_type = tree[0].label()
        assert node_type in NODE_TYPES
        return node_type

    @staticmethod
    def get_relation_type(tree):
        """
        returns the RST relation type attached to the parent node of an RST relation,
        e.g. `span`, `elaboration` or `antithesis`.

        Parameters
        ----------
        tree : nltk.tree.ParentedTree
            a tree representing a rhetorical structure (or a part of it)

        Returns
        -------
        relation_type : str
            the type of the rhetorical relation that this (sub)tree represents
        """
        return tree[1][0]

    def get_node_id(self, nuc_or_sat):
        """return the node ID of the given nucleus or satellite"""
        node_type = self.get_node_type(nuc_or_sat)
        if node_type == 'leaf':
            leaf_id = nuc_or_sat[0].leaves()[0]
            return '{0}:{1}'.format(self.ns, leaf_id)
        else: # node_type == 'span'
            span_start = nuc_or_sat[0].leaves()[0]
            span_end = nuc_or_sat[0].leaves()[1]
            return '{0}:span:{1}-{2}'.format(self.ns, span_start, span_end)


def fix_rst_treebank_tree_str(rst_tree_str):
    '''
    This removes some unexplained comments in two files that cannot be parsed.
    - data/RSTtrees-WSJ-main-1.0/TRAINING/wsj_2353.out.dis
    - data/RSTtrees-WSJ-main-1.0/TRAINING/wsj_2367.out.dis

    source: github.com/EducationalTestingService/discourse-parsing
    original license: MIT
    '''
    return re.sub(r'\)//TT_ERR', ')', rst_tree_str)


def convert_parens_in_rst_tree_str(rst_tree_str):
    '''
    This converts any brackets and parentheses in the EDUs of the RST discourse
    treebank to look like Penn Treebank tokens (e.g., -LRB-),
    so that the NLTK tree API doesn't crash when trying to read in the
    RST trees.

    source: github.com/EducationalTestingService/discourse-parsing
    original license: MIT
    '''
    for bracket_type, bracket_replacement in PTB_BRACKET_MAPPING.items():
        rst_tree_str = \
            re.sub('(_![^_(?=!)]*)\\{}([^_(?=!)]*_!)'.format(bracket_type),
                   '\\g<1>{}\\g<2>'.format(bracket_replacement),
                   rst_tree_str)
    return rst_tree_str


# pseudo-function to create a document graph from a RST (.dis) file
read_dis = RSTLispDocumentGraph


if __name__ == '__main__':
    generic_converter_cli(RSTLispDocumentGraph, 'RST (rhetorical structure)')

