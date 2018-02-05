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


class RS3FileWriter(object):
    def __init__(self, dgtree, debug=True, output_filepath=None):
        # dgtree is an RSTTree or DisTree (and contains a DGParentedTree)
        if hasattr(dgtree, 'tree') and isinstance(dgtree.tree, DGParentedTree):
            dgtree = dgtree.tree

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
        relations = self.gen_relations(dgtree)
        header = E('header')
        header.append(relations)

        body = self.gen_body(dgtree)

        tree = E('rst')
        tree.append(header)
        tree.append(body)
        return tree

    @staticmethod
    def gen_relations(dgtree):
        """Create the <relations> etree element of an RS3 file.
        This represents all relation types (both 'rst' and 'multinuc').

        Example:
            <rel name="circumstance" type="rst" />
        """
        relations = E('relations')
        relations_dict = extract_relations(dgtree)
        for relname in sorted(relations_dict):
            relations.append(
                E('rel', name=relname, type=relations_dict[relname]))
        return relations

    def gen_body(self, dgtree, body=None,
                 this_node_id=None, node_ids=None,
                 parent_id=None, parent_label=None):
        """Create the <body> etree element of an RS3 file (contains segments
        and groups) given a DGParentedTree.
        """
        if body is None:
            body = E('body')
        if node_ids is None:
            node_ids = set()
        if this_node_id is None:
            this_node_id = self.gen_node_id(parent_id, node_ids)

        if is_leaf(dgtree):  # this node represents an EDU
            if (parent_id is None) or (parent_id == this_node_id):
                attribs = {}
            else:
                attribs = {'parent': parent_id, 'relname': parent_label}
            body.append(E('segment', dgtree, id=this_node_id, **attribs))

        elif dgtree.label() in NUCLEARITY_LABELS:
            # child of a 'nuclearity' node: either 'EDU' or 'relation' node
            leaf_node_id = self.gen_node_id(this_node_id, node_ids)
            self.gen_body(dgtree[0], body=body, this_node_id=leaf_node_id,
                     node_ids=node_ids, parent_id=parent_id,
                     parent_label=parent_label)

        elif dgtree.label() == '':  # the tree is empty
            assert dgtree == DGParentedTree('', []), \
                "The tree has no root label, but isn't empty: {}".format(dgtree)

        else: # dgtree is a 'relation' node
            assert isinstance(dgtree, (RSTTree, DGParentedTree)), type(dgtree)

            relation = dgtree.label()
            # FIXME: calculate relations only once per tree
            relations = extract_relations(dgtree)
            assert relation in relations, relation
            reltype = relations[relation]

            if parent_id is not None: # this is neither a root nor a leaf node
                body.append(E('group', id=this_node_id, type=reltype, parent=parent_id, relname=parent_label))

            children = []
            for i, child in enumerate(dgtree):
                child_label = child.label()
                assert child_label in NUCLEARITY_LABELS
                child_node_id = self.gen_node_id(this_node_id, node_ids)
                children.append((child_label, child_node_id))

            if reltype == 'rst':

                #~ if parent_id is None:
                    # this is a the RST root node and the nucleus of a nucsat relation
                    #~ child = dgtree[0][0]
                    #~ if is_leaf(child): # the RST root node is a segment / an EDU
                        #~ body.append(E('segment', child, id=this_node_id))
                    #~ else:
                    #~ body.append(E('group', id=this_node_id))

                for i, (node_label, node_id) in enumerate(children):
                    if node_label == 'N':
                        nuc_node_id = node_id
                        nuc_index = i

                for i, child in enumerate(dgtree):
                    _, child_node_id = children[i]
                    if i != nuc_index:  # this child is the satellite of an rst relation
                        parent_id = nuc_node_id # FIXME: calculate this
                        parent_label = relation
                    self.gen_body(child[0], body=body, this_node_id=child_node_id,
                             node_ids=node_ids, parent_id=parent_id,
                             parent_label=parent_label)

            else:
                assert reltype == 'multinuc', reltype

                if parent_id is None: # this is a multinuc relation and the tree root
                    body.append(E('group', id=this_node_id, type=reltype))

                # each child of a 'multinuc' relation node is
                # an 'N' nuclearity node, whose only child is either
                # an EDU node or another relation node
                for i, child in enumerate(dgtree):
                    _, child_node_id = children[i]
                    self.gen_body(child[0], body=body,
                             this_node_id=child_node_id, node_ids=node_ids,
                             parent_id=this_node_id, parent_label=relation)
        return body

    @staticmethod
    def gen_node_id(parent_id, node_ids):
        """Return the ID to be assigned current node, given its parent ID
        and a list of already assigned node IDs.
        """
        if parent_id is not None:
            node_id = str(int(parent_id) + 1)
        else:
            node_id = '1'

        while node_id in node_ids:
            node_id = str(int(node_id) + 1)
        node_ids.add(node_id)
        return node_id

