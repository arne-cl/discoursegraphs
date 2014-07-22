#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann

"""
The ``paula`` module converts a ``DiscourseDocumentGraph`` (possibly
containing multiple annotation layers) into a PAULA XML document. Our goal is
to produce the subset of the PAULA 'specification' that is understood by the
SaltNPepper converter framework

"""

import os
from collections import defaultdict

from lxml import etree
from lxml.builder import ElementMaker
from enum import Enum

from discoursegraphs import (EdgeTypes, get_text, get_top_level_layers,
                             istoken, select_edges_by, select_nodes_by_layer,
                             tokens2text)
from discoursegraphs.util import create_dir, natural_sort_key


NSMAP={'xlink': 'http://www.w3.org/1999/xlink',
       'xml': 'http://www.w3.org/XML/1998/namespace'}

IGNORED_EDGE_ATTRIBS = ('layers', 'label', 'tiger:idref')
IGNORED_NODE_ATTRIBS = ('layers', 'label', 'tokens', 'tiger:id', 'tiger:art_id', 'tiger:orig_id')
IGNORED_TOKEN_ATTRIBS = IGNORED_NODE_ATTRIBS + ('tiger:token', 'tiger:word')


class PaulaDTDs(Enum):
    """
    enumerator for PAULA XML document type definitions (DTDs)

    Attributes
    ----------
    header : dtd
        ???
    struct : dtd
        for annoSet and hierarchical structure (tree/dependency) files
    mark : dtd
        for tokenization and span markable files
    text : dtd
        for primary text files
    feat : dtd
        for all files that use <feat> (instead of <multifeat>!) to annotate
        something, e.g. document/(sub)corpus metadata; annoFeat;
        token/span/struct/(pointing) rel annotation files
    rel : dtd
        for pointing relation files
    multifeat : dtd
        for all files that use <multifeat> to annotate something
    """
    header = 'paula_header.dtd'
    struct = 'paula_struct.dtd'
    mark = 'paula_mark.dtd'
    text = 'paula_text.dtd'
    feat = 'paula_feat.dtd'
    rel = 'paula_rel.dtd'
    multifeat = 'paula_multiFeat.dtd'

class PaulaDocument(object):
    """
    This class converts a DiscourseDocumentGraph into a PAULA XML document
    (i.e. a set of XML files describing one document annotated on multiple
    lebels).
    """
    def __init__(self, docgraph, corpus_name='mycorpus', human_readable=False):
        """
        Parameters
        ----------
        docgraph : DiscourseDocumentGraph
            the document graph to be converted
        corpus_name : str
            name of the corpus this document belongs to
        """
        self.dg = docgraph
        self.human_readable = human_readable
        self.corpus_name = corpus_name
        # map file types to file names
        self.filemap = defaultdict(lambda : defaultdict(str))
        # map file names to etrees
        self.files = {}
        # map file names to DTDs
        self.file2dtd = {}

        self.primary_text = self.__gen_primary_text_file()
        self.tokenization = self.__gen_tokenization_file()
        self.token_annotation = \
            self.__gen_token_anno_file()

        self.span_markable_files = []
        self.hierarchy_files = []
        self.struct_anno_files = []
        self.rel_anno_files = []
        self.pointing_files = []
        self.pointing_anno_files = []
        for top_level_layer in get_top_level_layers(docgraph):
            self.span_markable_files.append(
                self.__gen_span_markables_file(top_level_layer))
            self.hierarchy_files.append(
               self.__gen_hierarchy_file(top_level_layer))
            self.struct_anno_files.append(
               self.__gen_struct_anno_files(top_level_layer))
            self.rel_anno_files.append(
               self.__gen_rel_anno_file(top_level_layer))
            self.pointing_files.append(
                self.__gen_pointing_file(top_level_layer))
            self.pointing_anno_files.append(
                self.__gen_pointing_anno_file(top_level_layer))


    def __gen_primary_text_file(self):
        """
        generate the PAULA file that contains the primary text of the document
        graph.

        Example
        -------
        <?xml version="1.0" standalone="no"?>
        <!DOCTYPE paula SYSTEM "paula_text.dtd">
        <paula version="1.1">
            <header paula_id="maz-1423.text" type="text"/>
            <body>Zum Angewöhnen ...</body>
        </paula>
        """
        paula_id = '{}.{}.text'.format(self.corpus_name, self.dg.name)
        paula_fname = paula_id+'.xml'
        E, tree = gen_paula_etree(paula_id)
        tree.append(E.body(get_text(self.dg)))
        self.files[paula_fname] = tree
        self.file2dtd[paula_fname] = PaulaDTDs.text
        return paula_fname

    def __gen_tokenization_file(self):
        """
        generate the PAULA file that contains the tokenization of the document
        graph.

        Example
        -------
        <?xml version="1.0" standalone="no"?>
        <!DOCTYPE paula SYSTEM "paula_mark.dtd">
        <paula version="1.1">
            <header paula_id="nolayer.maz-1423.tok"/>
            <markList xmlns:xlink="http://www.w3.org/1999/xlink" type="tok" xml:base="maz-1423.text.xml">
                <mark id="sTok1" xlink:href="#xpointer(string-range(//body,'',1,3))" />
                <mark id="sTok2" xlink:href="#xpointer(string-range(//body,'',5,10))" />
                ...
            </markList>
        </paula>
        ...
        """
        paula_id = '{}.{}.tok'.format(self.corpus_name, self.dg.name)
        paula_fname = paula_id+'.xml'
        E, tree = gen_paula_etree(paula_id)
        self.filemap['tokenization'] = paula_id+'.xml'

        basefile = '{}.{}.text.xml'.format(self.corpus_name, self.dg.name)
        mlist = E('markList', {'type': 'tok',
                               '{%s}base' % NSMAP['xml']: basefile})
        tok_tuples = self.dg.get_tokens()
        for (tid, onset, tlen) in get_onsets(tok_tuples):
            xp = "#xpointer(string-range(//body,'',{},{}))".format(onset, tlen)
            mlist.append(E('mark', {'id': tid,
                                    '{%s}href' % NSMAP['xlink']: xp}))
        tree.append(mlist)
        self.files[paula_fname] = tree
        self.file2dtd[paula_fname] = PaulaDTDs.mark
        return paula_fname

    def __gen_span_markables_file(self, layer):
        """
        """
        paula_id = '{}.{}.{}_{}_seg'.format(layer, self.corpus_name,
                                            self.dg.name, layer)
        paula_fname = paula_id+'.xml'
        E, tree = gen_paula_etree(paula_id)
        basefile = '{}.{}.tok.xml'.format(self.corpus_name, self.dg.name)
        mlist = E('markList', {'type': 'tok',
                               '{%s}base' % NSMAP['xml']: basefile})

        span_dict = defaultdict(lambda : defaultdict(str))
        edges = select_edges_by(self.dg, layer=layer,
                                edge_type=EdgeTypes.spanning_relation,
                                data=True)
        for source_id, target_id, edge_attrs in edges:
            span_dict[source_id][target_id] = edge_attrs

        target_dict = defaultdict(list)
        for source_id in span_dict:
            target_ids = sorted(span_dict[source_id], key=natural_sort_key)
            xp = '(#xpointer(id({})/range-to(id({}))))'.format(target_ids[0],
                                                               target_ids[-1])
            mark = E('mark', {'{%s}href' % NSMAP['xlink']: xp})
            if self.human_readable:
                # add <!-- comments --> containing the token strings
                mark.append(etree.Comment(tokens2text(self.dg, target_ids)))
                target_dict[target_ids[0]].append(mark)
            else:
                mlist.append(mark)

        if self.human_readable:  # order <mark> elements by token ordering
            for target in sorted(target_dict, key=natural_sort_key):
                for mark in target_dict[target]:
                    mlist.append(mark)

        tree.append(mlist)
        self.files[paula_fname] = tree
        self.file2dtd[paula_fname] = PaulaDTDs.mark
        return paula_fname

    def __gen_token_anno_file(self):
        """
        creates an etree representation of a multiFeat file that describes all
        the annotations that only span one token (e.g. POS, lemma etc.)
        """
        basefile = '{}.{}.tok.xml'.format(self.corpus_name, self.dg.name)
        paula_id = '{}.{}.tok_multiFeat'.format(self.corpus_name,
                                                self.dg.name)
        paula_fname = paula_id+'.xml'
        E, tree = gen_paula_etree(paula_id)
        mflist = E('multiFeatList', {'{%s}base' % NSMAP['xml']: basefile})

        for token_id in self.dg.tokens:
            mfeat = E('multiFeat',
                      {'{%s}href' % NSMAP['xlink']: '#{}'.format(token_id)})
            token_dict = self.dg.node[token_id]
            for feature in token_dict:
                if feature not in IGNORED_TOKEN_ATTRIBS:
                    mfeat.append(
                        E('feat',
                          {'name': feature, 'value': token_dict[feature]}))
            if self.human_readable:  # adds token string as a <!-- comment -->
                mfeat.append(etree.Comment(token_dict[self.dg.ns+':token']))
            mflist.append(mfeat)
        tree.append(mflist)
        self.files[paula_fname] = tree
        self.file2dtd[paula_fname] = PaulaDTDs.multifeat
        return paula_fname

    def __gen_hierarchy_file(self, layer):
        """
        """
        paula_id = '{}.{}.{}_{}'.format(layer, self.corpus_name, self.dg.name,
                                        layer)
        paula_fname = paula_id+'.xml'
        self.filemap['hierarchy'][layer] = paula_id+'.xml'
        E, tree = gen_paula_etree(paula_id)

        dominance_edges = select_edges_by(self.dg, layer=layer,
                                edge_type=EdgeTypes.dominance_relation,
                                data=True)
        span_edges = select_edges_by(self.dg, layer=layer,
                        edge_type=EdgeTypes.spanning_relation,
                        data=True)
        dominance_dict = defaultdict(lambda : defaultdict(str))
        for source_id, target_id, edge_attrs in dominance_edges:
            if source_id != layer+':root_node':
                dominance_dict[source_id][target_id] = edge_attrs

        # in PAULA XML, token spans are also part of the hierarchy
        for source_id, target_id, edge_attrs in span_edges:
            if istoken(self.dg, target_id):
                dominance_dict[source_id][target_id] = edge_attrs

        slist = E('structList', {'type': layer})
        for source_id in dominance_dict:
            struct = E('struct',
                       {'id': source_id})
            if self.human_readable:
                struct.append(etree.Comment(self.dg.node[source_id].get('label')))

            for target_id in dominance_dict[source_id]:
                if istoken(self.dg, target_id):
                    href = '{}#{}'.format(self.filemap['tokenization'], target_id)
                else:
                    href = '#{}'.format(target_id)

                rel = E('rel',
                        {'id': 'rel_{}_{}'.format(source_id, target_id),
                         'type': dominance_dict[source_id][target_id]['edge_type'],
                         '{%s}href' % NSMAP['xlink']: href})
                struct.append(rel)
                if self.human_readable:
                    struct.append(etree.Comment(self.dg.node[target_id].get('label')))

            slist.append(struct)
        tree.append(slist)
        self.files[paula_fname] = tree
        self.file2dtd[paula_fname] = PaulaDTDs.struct
        return paula_fname

    def __gen_struct_anno_files(self, top_level_layer):
        """
        A struct annotation file contains node (struct) attributes (of
        non-token nodes). It is e.g. used to annotate the type of a syntactic
        category (NP, VP etc.).
        """
        paula_id = '{}.{}.{}_{}_struct'.format(top_level_layer,
                                               self.corpus_name, self.dg.name,
                                               top_level_layer)
        paula_fname = paula_id+'.xml'
        E, tree = gen_paula_etree(paula_id)

        basefile = self.filemap['hierarchy'][top_level_layer]
        mflist = E('multiFeatList', {'{%s}base' % NSMAP['xml']: basefile})

        for node_id in select_nodes_by_layer(self.dg, top_level_layer):
            if not istoken(self.dg, node_id):
                mfeat = E('multiFeat',
                          {'{%s}href' % NSMAP['xlink']: '#{}'.format(node_id)})
                node_dict = self.dg.node[node_id]
                for attr in node_dict:
                    if attr not in IGNORED_NODE_ATTRIBS:
                        mfeat.append(
                            E('feat',
                              {'name': attr, 'value': node_dict[attr]}))
                if self.human_readable:  # adds node label as a <!-- comment -->
                    mfeat.append(etree.Comment(node_dict.get('label')))
                mflist.append(mfeat)
        tree.append(mflist)
        self.files[paula_fname] = tree
        self.file2dtd[paula_fname] = PaulaDTDs.multifeat
        return paula_fname

    def __gen_rel_anno_file(self, top_level_layer):
        """
        A rel annotation file contains edge (rel)
        attributes. It is e.g. used to annotate the type of a dependency
        relation (subj, obj etc.).
        """
        paula_id = '{}.{}.{}_{}_rel'.format(top_level_layer, self.corpus_name,
                                            self.dg.name, top_level_layer)
        paula_fname = paula_id+'.xml'
        E, tree = gen_paula_etree(paula_id)

        dominance_edges = select_edges_by(self.dg, layer=top_level_layer,
                                edge_type=EdgeTypes.dominance_relation,
                                data=True)
        dominance_dict = defaultdict(lambda : defaultdict(str))
        for source_id, target_id, edge_attrs in dominance_edges:
            if source_id != top_level_layer+':root_node':
                dominance_dict[source_id][target_id] = edge_attrs

        basefile = self.filemap['hierarchy'][top_level_layer]
        mflist = E('multiFeatList', {'{%s}base' % NSMAP['xml']: basefile})
        for source_id in dominance_dict:
            for target_id in dominance_dict[source_id]:
                rel_href = '#rel_{}_{}'.format(source_id, target_id)
                mfeat = E('multiFeat',
                          {'{%s}href' % NSMAP['xlink']: rel_href})
            edge_attrs = dominance_dict[source_id][target_id]
            for edge_attr in edge_attrs:
                if edge_attr not in IGNORED_EDGE_ATTRIBS:
                    try:
                        mfeat.append(
                            E('feat',
                              {'name': edge_attr, 'value': edge_attrs[edge_attr]}))
                    except KeyError as e:
                        print "DEBUG KeyError: attr = {}; edge_dict = {}".format(edge_attr, edge_attrs)

            if self.human_readable:  # adds edge label as a <!-- comment -->
                mfeat.append(etree.Comment(edge_attrs.get('label')))
            mflist.append(mfeat)
        tree.append(mflist)
        self.files[paula_fname] = tree
        self.file2dtd[paula_fname] = PaulaDTDs.multifeat
        return paula_fname

    def __gen_pointing_file(self, top_level_layer):
        """
        Creates etree representations of PAULA XML files modeling pointing
        relations. Pointing relations are ahierarchical edges between any
        two nodes (``tok``, ``mark`` or ``struct``). They are used to signal
        pointing relations between tokens (e.g. in a dependency parse tree)
        or the coreference link between anaphora and antecedent.
        """
        paula_id = '{}.{}.{}.{}_pointing'.format(top_level_layer,
                                              self.corpus_name, self.dg.name,
                                              top_level_layer)
        paula_fname = paula_id+'.xml'
        self.filemap['pointing'][top_level_layer] = paula_id+'.xml'
        E, tree = gen_paula_etree(paula_id)

        pointing_edges = select_edges_by(self.dg, layer=top_level_layer,
                                         edge_type=EdgeTypes.pointing_relation,
                                         data=True)
        pointing_dict = defaultdict(lambda : defaultdict(str))
        for source_id, target_id, edge_attrs in pointing_edges:
            pointing_dict[source_id][target_id] = edge_attrs

        # NOTE: we don't add a base file here, because the nodes could be
        # tokens or structural nodes
        rlist = E('relList')
        for source_id in pointing_dict:
            for target_id in pointing_dict[source_id]:
                source_href = self.__gen_node_href(top_level_layer, source_id)
                target_href = self.__gen_node_href(top_level_layer, target_id)
                rel = E('rel',
                        {'id': 'rel_{}_{}'.format(source_id, target_id),
                         '{%s}href' % NSMAP['xlink']: source_href,
                         'target': target_href})

                # adds source/target node labels as a <!-- comment -->
                if self.human_readable:
                    source_label = self.dg.node[source_id].get('label')
                    target_label = self.dg.node[target_id].get('label')
                    rel.append(etree.Comment(u'{} - {}'.format(source_label,
                                                              target_label)))
                rlist.append(rel)
        tree.append(rlist)
        self.files[paula_fname] = tree
        self.file2dtd[paula_fname] = PaulaDTDs.rel
        return paula_fname

    def __gen_pointing_anno_file(self, top_level_layer):
        """
        A pointing relation annotation file contains edge (rel)
        attributes. It is e.g. used to annotate the type of a pointing relation.

        TODO: merge code with __gen_rel_anno_file() if possible!
        """
        paula_id = '{}.{}.{}_{}_pointing'.format(top_level_layer,
                                                 self.corpus_name,
                                                 self.dg.name, top_level_layer)
        paula_fname = paula_id+'.xml'
        E, tree = gen_paula_etree(paula_id)

        pointing_edges = select_edges_by(self.dg, layer=top_level_layer,
                                         edge_type=EdgeTypes.pointing_relation,
                                         data=True)
        pointing_dict = defaultdict(lambda : defaultdict(str))
        for source_id, target_id, edge_attrs in pointing_edges:
            pointing_dict[source_id][target_id] = edge_attrs

        basefile = self.filemap['pointing'][top_level_layer]
        mflist = E('multiFeatList', {'{%s}base' % NSMAP['xml']: basefile})
        for source_id in pointing_dict:
            for target_id in pointing_dict[source_id]:
                rel_href = '#rel_{}_{}'.format(source_id, target_id)
                mfeat = E('multiFeat',
                          {'{%s}href' % NSMAP['xlink']: rel_href})
            edge_attrs = pointing_dict[source_id][target_id]
            for edge_attr in edge_attrs:
                if edge_attr not in IGNORED_EDGE_ATTRIBS:
                    try:
                        mfeat.append(
                            E('feat',
                              {'name': edge_attr, 'value': edge_attrs[edge_attr]}))
                    except KeyError as e:
                        print "DEBUG KeyError: attr = {}; edge_dict = {}".format(edge_attr, edge_attrs)

            if self.human_readable:  # adds edge label as a <!-- comment -->
                mfeat.append(etree.Comment(edge_attrs.get('label')))
            mflist.append(mfeat)
        tree.append(mflist)
        self.files[paula_fname] = tree
        self.file2dtd[paula_fname] = PaulaDTDs.multifeat
        return paula_fname

    def __gen_node_href(self, layer, node_id):
        """
        generates a complete xlink:href for any node (token node,
        structure node etc.) in the docgraph. This will only work AFTER
        the corresponding PAULA files have been created (and their file names
        are registered in ``self.filemap``).
        """
        if istoken(self.dg, node_id):
            basefile = self.filemap['tokenization']
        else:
            basefile = self.filemap['hierarchy'][layer]
        return '{}#{}'.format(basefile, node_id)

    def write(self, output_rootdir):
        """
        Parameters
        ----------
        output_rootdir : str
            in the output root directory, a directory (with the name of the
            document ID) will be created. This document directory will contain
            all the annotations in PAULA XML format.

        """
        create_dir(output_rootdir)
        raise NotImplementedError

def paula_etree_to_string(tree, dtd_filename):
    return etree.tostring(
        tree, pretty_print=True, xml_declaration=True,
        encoding="UTF-8", standalone='no',
        doctype='<!DOCTYPE paula SYSTEM "{}">'.format(dtd_filename))

def gen_paula_etree(paula_id):
    """
    creates an element tree representation of an empty PAULA XML file.
    """
    E = ElementMaker(nsmap=NSMAP)
    tree = E('paula', version='1.1')
    tree.append(E('header', paula_id=paula_id))
    return E, tree

def get_onsets(token_tuples):
    """
    Parameters
    ----------
    token_tuples : list of (str, unicode)
        a list/generator of (token ID, token string) tuples

    Returns
    -------
    onset_tuples : generator of (str, int, int)
        A list/generator of (token ID, onset, token length) tuples.
        Note that PAULA starts counting string onsets with 1!
    """
    onset = 1
    for (token_id, token) in token_tuples:
        yield (token_id, onset, len(token))
        onset += (len(token) + 1)

def write_paula(docgraph, output_root_dir):
    """
    converts a DiscourseDocumentGraph into a set of PAULA XML files
    representing the same document.

    Parameters
    ----------
    docgraph : DiscourseDocumentGraph
        the document graph to be converted
    """
    paula_document = PaulaDocument(docgraph)
    error_msg = ("Please specify an output directory.\nPaula documents consist"
                 " of multiple files, so we can't just pipe them to STDOUT.")
    assert isinstance(output_root_dir, str), error_msg
    if not os.path.isdir(output_root_dir):
        create_dir(output_root_dir)
    for file_name in paula_document.files:
        with open(os.path.join(output_root_dir, file_name), 'w') as outfile:
            outfile.write(
                paula_etree_to_string(paula_document.files[file_name],
                                      paula_document.file2dtd[file_name]))
