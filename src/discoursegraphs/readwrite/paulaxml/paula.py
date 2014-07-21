#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann

"""
The ``paula`` module converts a ``DiscourseDocumentGraph`` (possibly
containing multiple annotation layers) into a PAULA XML document. Our goal is
to produce the subset of the PAULA 'specification' that is understood by the
SaltNPepper converter framework

"""

from collections import defaultdict

from lxml import etree
from lxml.builder import ElementMaker

from discoursegraphs import (EdgeTypes, get_text, get_top_level_layers,
                             istoken, select_edges_by, tokens2text)
from discoursegraphs.util import create_dir, natural_sort_key


NSMAP={'xlink': 'http://www.w3.org/1999/xlink',
       'xml': 'http://www.w3.org/XML/1998/namespace'}

IGNORED_EDGE_ATTRIBS = ('layers', 'label', 'tiger:idref')
IGNORED_NODE_ATTRIBS = ('layers', 'label', 'tokens', 'tiger:id', 'tiger:art_id', 'tiger:orig_id')
IGNORED_TOKEN_ATTRIBS = IGNORED_NODE_ATTRIBS + ('tiger:token', 'tiger:word')



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
        self.corpus_name = corpus_name
        self.E = ElementMaker()
        self.files = defaultdict(str)  # map file types to file names

        self.primary_text = self.__gen_primary_text_file(docgraph)
        self.tokenization = self.__gen_tokenization_file(docgraph)
        self.token_annotation = \
            self.__gen_token_annotation_file(docgraph,
                                             human_readable=human_readable)

        self.span_markable_files = []
        self.hierarchy_files = []
        for top_level_layer in get_top_level_layers(docgraph):
            self.span_markable_files.append(
                self.__gen_span_markables_file(docgraph, top_level_layer,
                                               human_readable=human_readable))
            self.hierarchy_files.append(
               self.__gen_hierarchical_annotation_file(docgraph, top_level_layer,
                                                       human_readable=human_readable))

    def __gen_primary_text_file(self, docgraph):
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
        paula_id = '{}.text'.format(docgraph.name)
        E, tree = gen_paula_etree(paula_id)
        tree.append(E.body(get_text(docgraph)))
        return tree

    def __gen_tokenization_file(self, docgraph):
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
        paula_id = '{}.{}.tok'.format(self.corpus_name, docgraph.name)
        E, tree = gen_paula_etree(paula_id)
        self.files['tokenization'] = paula_id+'.xml'

        basefile = '{}.{}.text.xml'.format(self.corpus_name, docgraph.name)
        mlist = E('markList', {'type': 'tok',
                               '{%s}base' % NSMAP['xml']: basefile})
        tok_tuples = docgraph.get_tokens()
        for (tid, onset, tlen) in get_onsets(tok_tuples):
            xp = "#xpointer(string-range(//body,'',{},{}))".format(onset, tlen)
            mlist.append(E('mark', {'id': tid,
                                    '{%s}href' % NSMAP['xlink']: xp}))
        tree.append(mlist)
        return tree

    def __gen_span_markables_file(self, docgraph, layer, human_readable=True):
        """
        """
        paula_id = '{}.{}_{}_seg'.format(self.corpus_name, docgraph.name,
                                         layer)
        E, tree = gen_paula_etree(paula_id)
        basefile = '{}.{}.tok.xml'.format(self.corpus_name, docgraph.name)
        mlist = E('markList', {'type': 'tok',
                               '{%s}base' % NSMAP['xml']: basefile})

        span_dict = defaultdict(lambda : defaultdict(str))
        edges = select_edges_by(docgraph, layer=layer,
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
            if human_readable:
                # add <!-- comments --> containing the token strings
                mark.append(etree.Comment(tokens2text(docgraph, target_ids)))
                target_dict[target_ids[0]].append(mark)
            else:
                mlist.append(mark)

        if human_readable:  # order <mark> elements by token ordering
            for target in sorted(target_dict, key=natural_sort_key):
                for mark in target_dict[target]:
                    mlist.append(mark)

        tree.append(mlist)
        return tree

    def __gen_token_annotation_file(self, docgraph, human_readable=True):
        """
        creates an etree representation of a multiFeat file that describes all
        the annotations that only span one token (e.g. POS, lemma etc.)
        """
        basefile = '{}.{}.tok.xml'.format(self.corpus_name, docgraph.name)
        paula_id = '{}.{}.tok_multiFeat'.format(self.corpus_name,
                                                docgraph.name)
        E, tree = gen_paula_etree(paula_id)
        mflist = E('multiFeatList', {'{%s}base' % NSMAP['xml']: basefile})

        for token_id in docgraph.tokens:
            mfeat = E('multiFeat',
                      {'{%s}href' % NSMAP['xlink']: '#{}'.format(token_id)})
            token_dict = docgraph.node[token_id]
            for feature in token_dict:
                if feature not in IGNORED_TOKEN_ATTRIBS:
                    mfeat.append(
                        E('feat',
                          {'name': feature, 'value': token_dict[feature]}))
            if human_readable:  # adds token string as a <!-- comment -->
                mfeat.append(etree.Comment(token_dict[docgraph.ns+':token']))
            mflist.append(mfeat)
        tree.append(mflist)
        return tree

    def __gen_hierarchical_annotation_file(self, docgraph, layer,
                                           human_readable=True):
        """
        """
        paula_id = '{}.{}_{}'.format(self.corpus_name, docgraph.name, layer)
        self.files['hierarchy'][layer] = paula_id+'.xml'
        E, tree = gen_paula_etree(paula_id)

        dominance_edges = select_edges_by(docgraph, layer=layer,
                                edge_type=EdgeTypes.dominance_relation,
                                data=True)
        span_edges = select_edges_by(docgraph, layer=layer,
                        edge_type=EdgeTypes.spanning_relation,
                        data=True)
        dominance_dict = defaultdict(lambda : defaultdict(str))
        for source_id, target_id, edge_attrs in dominance_edges:
            if source_id != layer+':root_node':
                dominance_dict[source_id][target_id] = edge_attrs

        # in PAULA XML, token spans are also part of the hierarchy
        for source_id, target_id, edge_attrs in span_edges:
            if istoken(docgraph, target_id):
                dominance_dict[source_id][target_id] = edge_attrs

        slist = E('structList', {'type': layer})
        for source_id in dominance_dict:
            struct = E('struct',
                       {'id': source_id})
            if human_readable:
                struct.append(etree.Comment(docgraph.node[source_id].get('label')))

            for target_id in dominance_dict[source_id]:
                if istoken(docgraph, target_id):
                    href = '{}#{}'.format(self.files['tokenization'], target_id)
                else:
                    href = '#{}'.format(target_id)

                rel = E('rel',
                        {'id': 'rel_{}_{}'.format(source_id, target_id),
                         'type': dominance_dict[source_id][target_id]['edge_type'],
                         '{%s}href' % NSMAP['xlink']: href})
                struct.append(rel)
                if human_readable:
                    struct.append(etree.Comment(docgraph.node[target_id].get('label')))

            slist.append(struct)
        tree.append(slist)
        return tree

    def etree_to_string(self, tree):
        return etree.tostring(tree, pretty_print=True, xml_declaration=True,
                              encoding="UTF-8",
                              doctype='<!DOCTYPE paula SYSTEM "paula_text.dtd">',
                              standalone='no',
                              xml_version='1.0')

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
