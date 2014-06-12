#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann

"""
This module converts an MMAX2-annotated document into a networkx-based directed
graph (``DiscourseDocumentGraph``).
"""

import os
from lxml import etree
from discoursegraphs import DiscourseDocumentGraph, EdgeTypes
from discoursegraphs.util import ensure_unicode, add_prefix
from discoursegraphs.readwrite.generic import generic_converter_cli


class MMAXProject(object):
    """
    represents an MMAX annotation project, which may contain one or more
    files annotated on zero or more levels.

    TODO: refactor this into an MMAXCorpusGraph(DiscourseCorpusGraph)
    """
    def __init__(self, project_path):
        self.paths, self.annotations, self.stylesheet = \
            self._parse_common_paths_file(project_path)

    def _parse_common_paths_file(self, project_path):
        """
        Parses a common_paths.xml file and returns a dictionary of paths,
        a dictionary of annotation level descriptions and the filename
        of the style file.

        Parameters
        ----------
        project_path : str
            path to the root directory of the MMAX project

        Returns
        -------
        paths : dict
            maps from MMAX file types (str, e.g. 'basedata' or 'markable')
            to the relative path (str) containing files of this type
        annotations : dict
            maps from MMAX annotation level names (str, e.g. 'sentence',
            'primmark') to a dict of features.
            The features are: 'schemefile' (maps to a file),
            'customization_file' (ditto) and 'file_extension' (maps to the
            file name ending used for all annotations files of this level)
        stylefile : str
            name of the (default) style file used in this MMAX project
        """
        common_paths_file = os.path.join(project_path, 'common_paths.xml')
        tree = etree.parse(common_paths_file)

        paths = {}
        path_vars = ['basedata', 'scheme', 'style', 'style', 'customization',
                     'markable']
        for path_var in path_vars:
            paths[path_var] = tree.find('//{}_path'.format(path_var)).text
        paths['project_path'] = project_path

        annotations = {}
        for level in tree.iterfind('//level'):
            annotations[level.attrib['name']] = {
                'schemefile': level.attrib['schemefile'],
                'customization_file': level.attrib['customization_file'],
                'file_extension': level.text[1:]}

        stylesheet = tree.find('//stylesheet').text
        return paths, annotations, stylesheet


class MMAXDocumentGraph(DiscourseDocumentGraph):
    """
    represents a MMAX2-annotated document as a multidigraph.

    Attributes
    ----------
    ns : str
        the namespace of the graph (default: mmax)
    tokens : list of int
        a list of node IDs (int) which represent the tokens in the
        order they occur in the text
    root : str
        name of the document root node ID
        (default: 'mmax:root_node')
    """
    def __init__(self, mmax_base_file, name=None, namespace='mmax',
                 precedence=True, connected=False):
        """
        Parameters
        ----------
        mmax_base_file : str
            relative or absolute path to an MMAX2 document base file (*.mmax)
        name : str or None
            the name or ID of the graph to be generated. If no name is
            given, the basename of the input *.mmax file is used.
        namespace : str
            the namespace of the graph (default: mmax)
        precedence : bool
            add precedence relation edges (root precedes token1, which precedes
            token2 etc.)
        connected : bool
            Make the graph connected, i.e. add an edge from root to each
            token. This doesn't do anything, if
            precendence=True.
        """
        # super calls __init__() of base class DiscourseDocumentGraph
        super(MMAXDocumentGraph, self).__init__()

        if name is None:
            self.name = os.path.basename(mmax_base_file)
        self.ns = namespace
        self.root = self.ns+':root_node'
        self.add_node(self.root, layers={self.ns})
        self.tokens = []

        mmax_rootdir, _ = os.path.split(mmax_base_file)

        mmax_project = MMAXProject(mmax_rootdir)
        words_file = self.get_word_file(mmax_project, mmax_base_file)

        if precedence:
            self.add_token_layer(words_file, connected=False)
            self.add_precedence_relations()
        else:
            self.add_token_layer(words_file, connected)

        for layer_name in mmax_project.annotations:
            layer_dict = mmax_project.annotations[layer_name]
            file_id = self.get_file_id(mmax_base_file)
            annotation_file = os.path.join(
                mmax_rootdir,
                mmax_project.paths['markable'],
                file_id+layer_dict['file_extension'])
            self.add_annotation_layer(annotation_file, layer_name)

    def get_file_id(self, mmax_base_file):
        """
        given an MMAX base file (*.mmax), returns its file ID.
        """
        # removes '.mmax' from filename
        return os.path.basename(mmax_base_file)[:-5]

    def get_word_file(self, mmax_project, mmax_base_file):
        """
        parses an MMAX base file (*.mmax) and returns the path
        to the corresponding _words.xml file (which contains
        the tokens of the document).
        """
        return os.path.join(mmax_project.paths['project_path'],
                            mmax_project.paths['basedata'],
                            etree.parse(mmax_base_file).find('//words').text)

    def add_token_layer(self, words_file, connected):
        """
        parses a _words.xml file, adds every token to the document graph
        and adds an edge from the MMAX root node to it.

        Parameters
        ----------
        connected : bool
            Make the graph connected, i.e. add an edge from root to each
            token.
        """
        for word in etree.parse(words_file).iterfind('//word'):
            token_node_id = word.attrib['id']
            self.tokens.append(token_node_id)
            token_str = ensure_unicode(word.text)
            self.add_node(token_node_id,
                          layers={self.ns, self.ns+':token'},
                          attr_dict={self.ns+':token': token_str,
                                     'label': token_str})
            if connected:
                self.add_edge(self.root, token_node_id,
                              layers={self.ns, self.ns+':token'})

    def add_annotation_layer(self, annotation_file, layer_name):
        """
        """
        assert os.path.isfile(annotation_file), \
            "Annotation doesn't exist: {}".format(annotation_file)
        tree = etree.parse(annotation_file)
        root = tree.getroot()
        # avoids eml.org namespace handling
        for markable in root.iterchildren():
            markable_node_id = markable.attrib['id']
            markable_attribs = add_prefix(markable.attrib, self.ns+':')
            self.add_node(markable_node_id,
                          layers={self.ns, self.ns+':markable'},
                          attr_dict=markable_attribs,
                          label=markable_node_id+':'+layer_name)
            for to_node_id in span2tokens(markable.attrib['span']):
                # manually add to_node if it's not in the graph, yet
                # cf. issue #39
                if to_node_id not in self:
                    self.add_node(to_node_id,
                                  layers={self.ns, self.ns+':markable'},
                                  label=to_node_id+':'+layer_name)

                self.add_edge(markable_node_id, to_node_id,
                              layers={self.ns, self.ns+':markable'},
                              edge_type=EdgeTypes.spanning_relation,
                              label=self.ns+':'+layer_name)

            # this is a workaround for Chiarcos-style MMAX files
            if 'anaphor_antecedent' in markable.attrib \
            and markable.attrib['anaphor_antecedent'] != 'empty':
                antecedent_pointer = markable.attrib['anaphor_antecedent']
                # mmax2 supports weird double antecedents,
                # e.g. "markable_1000131;markable_1000132", cf. Issue #40
                for antecedent in antecedent_pointer.split(';'):
                    antecedent_split = antecedent.split(":")
                    if len(antecedent_split) == 2:
                        # mark group:markable_n or secmark:markable_n as such
                        edge_label = '{}:antecedent'.format(antecedent_split[0])
                    else:
                        edge_label = ':antecedent'

                    # handles both 'markable_n' and 'layer:markable_n'
                    antecedent_node_id = antecedent_split[-1]

                    # manually add antecedent node if it's not in the graph, yet
                    # cf. issue #39
                    if antecedent_node_id not in self:
                        self.add_node(antecedent_node_id,
                                      layers={self.ns, self.ns+':markable'})
                    self.add_edge(markable_node_id, antecedent_node_id,
                                  layers={self.ns, self.ns+':markable'},
                                  edge_type=EdgeTypes.pointing_relation,
                                  label=self.ns+edge_label)

    def get_annotation_type():
        """
        TODO: watch out for cross-layer annotations,
        e.g. 'anaphor_antecedent="secmark:markable_18"'
        """
        raise NotImplementedError

def span2tokens(span_string):
    """
    converts a span of tokens (str, e.g. 'word_88..word_91')
    into a list of token IDs (e.g. ['word_88', 'word_89', 'word_90', 'word_91']

    Examples
    --------
    >>> from discoursegraphs.readwrite.mmax2 import span2tokens
    >>> span2tokens('word_1')
    ['word_1']
    >>> span2tokens('word_2,word_3')
    ['word_2', 'word_3']
    >>> span2tokens('word_7..word_11')
    ['word_7', 'word_8', 'word_9', 'word_10', 'word_11']
    >>> span2tokens('word_2,word_3,word_7..word_9')
    ['word_2', 'word_3', 'word_7', 'word_8', 'word_9']
    >>> span2tokens('word_7..word_9,word_15,word_17..word_19')
    ['word_7', 'word_8', 'word_9', 'word_15', 'word_17', 'word_18', 'word_19']
    """
    tokens = []

    spans = span_string.split(',')
    for span in spans:
        span_elements = span.split('..')
        if len(span_elements) == 1:
            tokens.append(span_elements[0])
        elif len(span_elements) == 2:
            start, end = span_elements
            start_id = int(start[5:])  # removes 'word_'
            end_id = int(end[5:])
            tokens.extend(['word_'+str(token_id)
                           for token_id in range(start_id, end_id+1)])
        else:
            raise ValueError("Can't parse span '{}'".format(span_string))
    return tokens


if __name__ == "__main__":
    generic_converter_cli(MMAXDocumentGraph,
                          '*.mmax file (MMAX2 annotation file)')
