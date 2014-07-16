#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann

"""
The ``paula`` module converts a ``DiscourseDocumentGraph`` (possibly
containing multiple annotation layers) into a PAULA XML document. Our goal is
to produce the subset of the PAULA 'specification' that is understood by the
SaltNPepper converter framework

"""


from lxml import etree
from lxml.builder import ElementMaker

from discoursegraphs import get_text
from discoursegraphs.util import create_dir


NSMAP={'xlink': 'http://www.w3.org/1999/xlink',
       'xml': 'http://www.w3.org/XML/1998/namespace'}


class PaulaDocument(object):
    """
    This class converts a DiscourseDocumentGraph into a PAULA XML document
    (i.e. a set of XML files describing one document annotated on multiple
    lebels).
    """
    def __init__(self, docgraph):
        """
        Parameters
        ----------
        docgraph : DiscourseDocumentGraph
            the document graph to be converted
        """
        self.E = ElementMaker()
        self.primary_text = self.__generate_primary_text_file(docgraph)
        self.tokenization = self.__generate_tokenization_file(docgraph)

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
                               '{%s}base' % NSMAP['xml']: 'maz-1423.text.xml'})
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
