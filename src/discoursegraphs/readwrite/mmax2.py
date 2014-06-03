#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann

import os
from lxml import etree
from networkx import MultiDiGraph


class MMAXProject(object):
    """
    represents an MMAX annotation project, which may contain one or more
    files annotated on zero or more levels.
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


class MMAXDocumentGraph(MultiDiGraph):
    """
    """
    def __init__(self, mmax_rootdir, mmax_base_file):
        """
        """
        # super calls __init__() of base class MultiDiGraph
        super(MMAXDocumentGraph, self).__init__()
        self.name = os.path.basename(mmax_base_file)
        self.add_node('mmax:root_node', layers={'mmax'})

        mmax_project = MMAXProject(mmax_rootdir)
        words_file = self.get_word_file(mmax_project, mmax_base_file)
        self.add_token_layer(words_file)

        for layer_name in mmax_project.annotations:
            layer_dict = mmax_project.annotations[layer_name]
            file_id = self.get_file_id(mmax_base_file)
            annotation_file = os.path.join(
                mmax_rootdir,
                mmax_project.paths['markable'],
                file_id+layer_dict['file_extension'])
            self.add_annotation_layer(annotation_file)

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

    def add_token_layer(self, words_file):
        """
        parses a _words.xml file, adds every token to the document graph
        and adds an edge from the MMAX root node to it.

        TODO: enforce utf-8 or unicode for tokens
        """
        for word in etree.parse(words_file).iterfind('//word'):
            self.add_node(word.attrib['id'], token=word.text,
                          layers={'mmax', 'mmax:token'})
            self.add_edge('mmax:root_node', word.attrib['id'],
                          layers={'mmax', 'mmax:token'})

    def add_annotation_layer(self, annotation_file):
        """
        """
        assert os.path.isfile(annotation_file), \
            "Annotation doesn't exist: {}".format(annotation_file)
        pass

    def span2tokens(span_string):
        """
        converts a span of tokens (str, e.g. 'word_88..word_91') into a list of
        token IDs (e.g. ['word_88', 'word_89', 'word_90', 'word_91'])
        """
        pass

    def get_annotation_type():
        """
        TODO: watch out for cross-layer annotations,
        e.g. 'anaphor_antecedent="secmark:markable_18"'
        """
        pass


def span2tokens(span_string):
    """
    converts a span of tokens (str, e.g. 'word_88..word_91')
    into a list of token IDs (e.g. ['word_88', 'word_89', 'word_90', 'word_91']
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
    MMAX_ROOTDIR = \
        os.path.expanduser("~/repos/pcc-annis-merged/maz176/coreference")
    COMMON_PATHS_FILE = os.path.join(MMAX_ROOTDIR, "common_paths.xml")
    BASEDATA_DIR = os.path.join(MMAX_ROOTDIR,
                                MMAXProject(MMAX_ROOTDIR).paths['basedata'])
    EXAMPLE_WORDS_FILE = os.path.join(BASEDATA_DIR, 'pocos.maz-5010_words.xml')

    mp = MMAXProject(MMAX_ROOTDIR)

    for layer in mp.annotations:
        print layer, mp.annotations[layer]

    print span2tokens('word_1')
    print span2tokens('word_2,word_3')
    print span2tokens('word_7..word_11')
    print span2tokens('word_2,word_3,word_7..word_11')
    print span2tokens('word_2,word_3,word_7..word_11,word_15,word_17..word_19')
