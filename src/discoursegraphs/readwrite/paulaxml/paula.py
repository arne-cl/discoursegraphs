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
                             select_edges_by, tokens2text)
from discoursegraphs.util import create_dir, natural_sort_key


NSMAP={'xlink': 'http://www.w3.org/1999/xlink',
       'xml': 'http://www.w3.org/XML/1998/namespace'}


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
        self.primary_text = self.__generate_primary_text_file(docgraph)
        self.tokenization = self.__generate_tokenization_file(docgraph)

        self.span_markable_files = []
        for top_level_layer in get_top_level_layers(docgraph):
            self.span_markable_files.append(
                self.__add_span_markables_file(docgraph, top_level_layer,
                                               human_readable=human_readable))

    def __generate_primary_text_file(self, docgraph):
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
        tree = self.E('paula', version='1.1')
        tree.append(self.E('header', paula_id='{}.text'.format(docgraph.name)))
        body = self.E('body')
        primary_text = get_text(docgraph)
        body.text = primary_text
        tree.append(body)
        return tree

    def __generate_tokenization_file(self, docgraph):
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
        E = ElementMaker(nsmap=NSMAP)
        tree = E('paula', version='1.1')
        tree.append(E('header', paula_id='{}.tok'.format(docgraph.name)))
        mlist = E('markList', {'type': 'tok',
                               '{%s}base' % NSMAP['xml']: '{}.{}.text.xml'.format(self.corpus_name, docgraph.name)})
        tok_tuples = docgraph.get_tokens()
        for (tid, onset, tlen) in get_onsets(tok_tuples):
            xp = "#xpointer(string-range(//body,'',{},{}))".format(onset, tlen)
            mlist.append(E('mark', {'id': tid,
                                    '{%s}href' % NSMAP['xlink']: xp}))
        tree.append(mlist)
        return tree

    def etree_to_string(self, tree):
        return etree.tostring(tree, pretty_print=True, xml_declaration=True,
                              encoding="UTF-8",
                              doctype='<!DOCTYPE paula SYSTEM "paula_text.dtd">',
                              standalone='no',
                              xml_version='1.0')

    def __add_span_markables_file(self, docgraph, layer, human_readable=True):
        """
        """
        E = ElementMaker(nsmap=NSMAP)
        tree = E('paula', version='1.1')
        tree.append(E('header', paula_id='{}.{}_{}_seg'.format(self.corpus_name, docgraph.name, layer)))
        mlist = E('markList', {'type': 'tok',
                               '{%s}base' % NSMAP['xml']: '{}.{}.tok.xml'.format(self.corpus_name, docgraph.name)})

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
