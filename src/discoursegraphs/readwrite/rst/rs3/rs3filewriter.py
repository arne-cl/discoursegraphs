#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""This module converts `DGParentedTree`s into .rs3 files."""

from __future__ import absolute_import, division, print_function
import codecs

from lxml import etree
from lxml.builder import E

from discoursegraphs.readwrite.tree import DGParentedTree
from discoursegraphs.readwrite.rst.rs3.rs3tree import (
    extract_relations, is_leaf, NUCLEARITY_LABELS, RSTTree)


class TreeNodeTypes(object):
    """Enum of node types of DGParentedTree"""
    empty_tree = 'empty_tree'
    leaf_node = 'leaf_node'
    nuclearity_node = 'nuclearity_node'
    relation_node = 'relation_node'


def get_node_type(dgtree):
    """Returns the type of the root node of a DGParentedTree."""
    if is_leaf(dgtree):
        return TreeNodeTypes.leaf_node

    root_label = dgtree.label()
    if root_label == '':
        assert dgtree == DGParentedTree('', []), \
            "The tree has no root label, but isn't empty: {}".format(dgtree)
        return TreeNodeTypes.empty_tree
    elif root_label in NUCLEARITY_LABELS:
        return TreeNodeTypes.nuclearity_node
    else:
        assert isinstance(dgtree, (RSTTree, DGParentedTree)), type(dgtree)
        return TreeNodeTypes.relation_node


class RS3FileWriter(object):
    def __init__(self, dgtree, debug=True, output_filepath=None):
        # dgtree is an RSTTree or DisTree (and contains a DGParentedTree)
        if hasattr(dgtree, 'tree') and isinstance(dgtree.tree, DGParentedTree):
            dgtree = dgtree.tree

        self.body = E('body')  # will be filled by gen_body()
        self.node_ids = set()  # will be filled by gen_body()
        self.relations = extract_relations(dgtree)
        self.etree = self.gen_etree(dgtree)

        if debug is True:
            print(etree.tostring(self.etree, pretty_print=True))

        if output_filepath is None:
            return self.etree
        else:
            with codecs.open(output_filepath, 'w', 'utf-8') as outfile:
                outfile.write(etree.tostring(self.etree))

    def gen_etree(self, dgtree):
        """convert an RST tree (DGParentedTree -> lxml etree)"""
        relations_elem = self.gen_relations(dgtree)
        header = E('header')
        header.append(relations_elem)

        self.gen_body(dgtree)

        tree = E('rst')
        tree.append(header)
        tree.append(self.body)
        return tree

    def gen_relations(self, dgtree):
        """Create the <relations> etree element of an RS3 file.
        This represents all relation types (both 'rst' and 'multinuc').

        Example relation:
            <rel name="circumstance" type="rst" />
        """
        relations_elem = E('relations')
        for relname in sorted(self.relations):
            relations_elem.append(
                E('rel', name=relname, type=self.relations[relname]))
        return relations_elem

    def gen_body(self, dgtree,
                 this_node_id=None,
                 parent_id=None, parent_label=None):
        """Create the <body> etree element of an RS3 file (contains segments
        and groups) given a DGParentedTree.

        This method will be called recursively to traverse the whole
        DGParentedTree
        """
        if this_node_id is None:
            this_node_id = self.gen_node_id(parent_id)

        node_type = get_node_type(dgtree)

        if node_type == TreeNodeTypes.leaf_node:
            self.handle_leaf_node(dgtree, this_node_id, parent_id, parent_label)

        elif node_type == TreeNodeTypes.nuclearity_node:
            self.handle_nuclearity_node(
                dgtree, this_node_id, parent_id, parent_label)

        elif node_type == TreeNodeTypes.empty_tree:
            assert dgtree == DGParentedTree('', []), \
                "The tree has no root label, but isn't empty: {}".format(dgtree)

        elif node_type == TreeNodeTypes.relation_node:
            self.handle_relation_node(
                dgtree, this_node_id, parent_id, parent_label)

        else:
            raise NotImplementedError('Unknown node type: {}'.format())

    def handle_leaf_node(self, dgtree, this_node_id, parent_id, parent_label):
        """Converts a leaf node into corresponding <body> elements."""
        # this node is an EDU / segment
        if (parent_id is None) or (parent_id == this_node_id):
            # this node is also a root node
            attribs = {}
        else:
            attribs = {'parent': parent_id, 'relname': parent_label}
        self.body.append(E('segment', dgtree, id=this_node_id, **attribs))

    def handle_nuclearity_node(self, dgtree, this_node_id,
                                parent_id, parent_label):
        """Converts a nuclearity node into corresponding <body> elements."""
        # child of a 'nuclearity' node: either 'EDU' or 'relation' node
        leaf_node_id = self.gen_node_id(this_node_id)
        self.gen_body(dgtree[0], this_node_id=leaf_node_id,
                 parent_id=parent_id,
                 parent_label=parent_label)

    def handle_relation_node(self, dgtree, this_node_id,
                              parent_id, parent_label):
        assert isinstance(dgtree, (RSTTree, DGParentedTree)), type(dgtree)

        relation = dgtree.label()
        assert relation in self.relations, relation
        reltype = self.relations[relation]

        if parent_id is not None: # this is neither a root nor a leaf node
            self.body.append(E('group', id=this_node_id, type=reltype, parent=parent_id, relname=parent_label))

        children = []
        for i, child in enumerate(dgtree):
            child_label = child.label()
            assert child_label in NUCLEARITY_LABELS
            child_node_id = self.gen_node_id(this_node_id)
            children.append((child_label, child_node_id))

        if reltype == 'rst':

            #~ if parent_id is None:
                # this is a the RST root node and the nucleus of a nucsat relation
                #~ child = dgtree[0][0]
                #~ if is_leaf(child): # the RST root node is a segment / an EDU
                    #~ self.body.append(E('segment', child, id=this_node_id))
                #~ else:
                #~ self.body.append(E('group', id=this_node_id))

            for i, (node_label, node_id) in enumerate(children):
                if node_label == 'N':
                    nuc_node_id = node_id
                    nuc_index = i

            for i, child in enumerate(dgtree):
                _, child_node_id = children[i]
                if i != nuc_index:  # this child is the satellite of an rst relation
                    parent_id = nuc_node_id # FIXME: calculate this
                    parent_label = relation
                self.gen_body(child[0], this_node_id=child_node_id,
                         parent_id=parent_id,
                         parent_label=parent_label)

        else:
            assert reltype == 'multinuc', reltype

            if parent_id is None: # this is a multinuc relation and the tree root
                self.body.append(E('group', id=this_node_id, type=reltype))

            # each child of a 'multinuc' relation node is
            # an 'N' nuclearity node, whose only child is either
            # an EDU node or another relation node
            for i, child in enumerate(dgtree):
                _, child_node_id = children[i]
                self.gen_body(child[0],
                         this_node_id=child_node_id,
                         parent_id=this_node_id, parent_label=relation)

    def gen_node_id(self, parent_id):
        """Return the ID to be assigned current node, given its parent ID
        and a list of already assigned node IDs.
        """
        if parent_id is not None:
            node_id = str(int(parent_id) + 1)
        else:
            node_id = '1'

        while node_id in self.node_ids:
            node_id = str(int(node_id) + 1)
        self.node_ids.add(node_id)
        return node_id

