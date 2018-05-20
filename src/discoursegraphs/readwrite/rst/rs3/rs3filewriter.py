#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""This module converts `DGParentedTree`s into .rs3 files."""

from __future__ import absolute_import, division, print_function
import codecs
from collections import defaultdict, OrderedDict

from lxml import etree
from lxml.builder import E
import nltk

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

        self.dgtree = dgtree
        self.body = defaultdict(list)  # will be filled by gen_body()
        self.relations = extract_relations(self.dgtree)
        self.treepositions = {treepos:str(i) for i, treepos in
                             enumerate(dgtree.treepositions(), 1)}
        self.etree = self.gen_etree()

        if debug is True:
            print(etree.tostring(self.etree, pretty_print=True))

        if output_filepath is not None:
            with open(output_filepath, 'w') as outfile:
                outfile.write(etree.tostring(
                    self.etree, encoding='UTF-8', xml_declaration=True, pretty_print=True))

    def has_parent(self, treepos):
        """Returns True, iff this node has a parent."""
        return self.get_parent_treepos(treepos) is not None

    def get_node_id(self, treepos):
        """Given the treeposition of a node, return its node ID for rs3."""
        return self.treepositions[treepos]

    @staticmethod
    def get_parent_treepos(treepos):
        """Given a treeposition, return the treeposition of its parent."""
        if treepos == ():  # this is the root node
            return None
        return treepos[:-1]

    def get_children_treepos(self, treepos):
        """Given a treeposition, return the treepositions of its children."""
        children_treepos = []
        for i, child in enumerate(self.dgtree[treepos]):
            if isinstance(child, nltk.Tree):
                children_treepos.append(child.treeposition())
            elif is_leaf(child):
                # we can't call .treeposition() on a leaf node
                treepos_list = list(treepos)
                treepos_list.append(i)
                leaf_treepos = tuple(treepos_list)
                children_treepos.append(leaf_treepos)
        return children_treepos

    def get_siblings_treepos(self, treepos):
        """Given a treeposition, return the treepositions of its siblings."""
        parent_pos = self.get_parent_treepos(treepos)
        siblings_treepos = []

        if parent_pos is not None:
            for child_treepos in self.get_children_treepos(parent_pos):
                if child_treepos != treepos:
                    siblings_treepos.append(child_treepos)
        return siblings_treepos

    def get_cousins_treepos(self, treepos):
        """Given a treeposition, return the treeposition of its siblings."""
        cousins_pos = []

        mother_pos = self.get_parent_treepos(treepos)
        if mother_pos is not None:
            aunts_pos = self.get_siblings_treepos(mother_pos)
            for aunt_pos in aunts_pos:
                cousins_pos.extend( self.get_children_treepos(aunt_pos) )
        return cousins_pos

    def get_parent_label(self, treepos):
        """Given the treeposition of a node, return the label of its parent.
        Returns None, if the tree has no parent.
        """
        parent_pos = self.get_parent_treepos(treepos)
        if parent_pos is not None:
            parent = self.dgtree[parent_pos]
            return parent.label()
        else:
            return None

    def get_children_labels(self, treepos):
        """Given the treeposition of a node, return the labels of its children."""
        children_labels = []
        node = self.dgtree[treepos]
        for child in node:
            if is_leaf(child):
                # we can't call .label() on a leaf node
                children_labels.append(child)
            else:
                children_labels.append(child.label())
        return children_labels

    def get_reltype(self, relname):
        """Given a relation name, return its type, i.e. 'rst' or 'multinuc'
        Returns 'span' if the relname is not known / None.
        """
        return self.relations.get(relname, 'span')

    def gen_etree(self):
        """convert an RST tree (DGParentedTree -> lxml etree)"""
        relations_elem = self.gen_relations()
        header = E('header')
        header.append(relations_elem)

        self.gen_body()

        tree = E('rst')
        tree.append(header)

        # The <body> contains both <segment>, as well as <group> elements.
        # While the order of the elements should theoretically be irrelevant,
        # rs3 files usually list the segments before the groups.
        body = E('body')
        for segment in self.body['segments']:
            body.append(segment)
        for group in self.body['groups']:
            body.append(group)

        tree.append(body)
        return tree

    def gen_relations(self):
        """Create the <relations> etree element of an RS3 file.
        This represents all relation types (both 'rst' and 'multinuc').

        Example relation:
            <rel name="circumstance" type="rst" />
        """
        relations_elem = E('relations')
        for relname in sorted(self.relations):
            relations_elem.append(
                E('rel', OrderedDict([('name', relname), ('type', self.relations[relname])])))
        return relations_elem

    def gen_body(self):
        """Create the <body> etree element of an RS3 file (contains segments
        and groups) given a DGParentedTree.
        """
        # We need to sort the treepositions, as RSTTool relies on <segment>
        # elements to be in linear order of the EDUs in the text.
        for treepos in sorted(self.treepositions):
            node = self.dgtree[treepos]
            node_id = self.get_node_id(treepos)
            node_type = get_node_type(node)

            if node_type in (TreeNodeTypes.leaf_node,
                             TreeNodeTypes.relation_node):
                relname, parent_id = self.get_relname_and_parent(treepos)

                attrib_list = [('id', node_id)]
                if parent_id is not None:
                    attrib_list.extend([('parent', parent_id), ('relname', relname)])

                if node_type == TreeNodeTypes.leaf_node:
                    self.body['segments'].append(E('segment', node, OrderedDict(attrib_list)))

                else:  # node_type == TreeNodeTypes.relation_node:
                    group_type = self.get_group_type(treepos)
                    # insert 'type' attrib between 'id' and 'parent'
                    attrib_list.insert(1, ('type', group_type))
                    self.body['groups'].append(E('group', OrderedDict(attrib_list)))

    def get_group_type(self, treepos):
        node = self.dgtree[treepos]
        assert get_node_type(node) == TreeNodeTypes.relation_node
        labels = self.get_children_labels(treepos)
        if (len(labels) == 2) and ('S' in labels):
            return 'span'
        elif (len(labels) > 1) and set(labels) == {'N'}:
            return 'multinuc'
        else:
            raise ValueError("Unknown group type of node '{}'.".format(node))

    def get_relname_and_parent(self, treepos):
        """Return the (relation name, parent ID) tuple that a node is in.
        Return None if this node is not in a relation.
        """
        node = self.dgtree[treepos]
        node_type = get_node_type(node)
        assert node_type in (TreeNodeTypes.relation_node, TreeNodeTypes.leaf_node)

        parent_pos = self.get_parent_treepos(treepos)
        if parent_pos is None:  # a root node has no upward relation
            return None, None
        else:
            parent_label = self.get_parent_label(treepos)
            grandparent_pos = self.get_parent_treepos(parent_pos)

            if grandparent_pos is None:
                # a tree with only one EDU/leaf and a 'N' parent but no relation
                return None, None
            else:
                grandparent_id = self.get_node_id(grandparent_pos)
                grandparent_label = self.get_parent_label(parent_pos)
                reltype = self.get_reltype(grandparent_label)

                if reltype == 'rst':
                    if parent_label == 'N':
                        return 'span', grandparent_id
                    elif parent_label == 'S':
                        cousins_pos = self.get_cousins_treepos(treepos)
                        assert len(cousins_pos) == 1
                        cousin_id = self.get_node_id(cousins_pos[0])
                        return grandparent_label, cousin_id
                elif reltype == 'multinuc':
                    return grandparent_label, grandparent_id


def write_rs3(dgtree, output_file):
    """Convert a DGParentedTree representation of an RST tree into an .rs3 file"""
    RS3FileWriter(dgtree, debug=False, output_filepath=output_file)
