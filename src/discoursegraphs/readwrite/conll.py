#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann

"""
The ``conll`` module converts a ``DiscourseDocumentGraph`` (possibly
containing multiple annotation layers) into an CoNLL 2009 tab-separated file.

TODO: write a generic_merging_cli() and a generic write_format() function.
Coordinate this with
    issue #43: add write_formatname function for each output format
"""

import os
import sys

from discoursegraphs.util import create_dir


class Conll2009File(object):
    """
    This class converts a DiscourseDocumentGraph into a CoNLL 2009 file.
    """
    def __init__(self, docgraph):
        """
        Parameters
        ----------
        docgraph : DiscourseDocumentGraph
            the document graph to be converted
        """
        raise NotImplementedError

    def __str__(self):
        """
        returns the generated CoNLL 2009 file as a string.
        """
        raise NotImplementedError

    def write(self, output_filepath):
        """
        Parameters
        ----------
        output_filepath : str
            relative or absolute path to the CoNLL 2009 file to be created
        """
        with open(output_filepath, 'w') as out_file:
            out_file.write(self.__str__())


def write_conll(docgraph, output_file):
    """
    converts a DiscourseDocumentGraph into a tab-separated CoNLL 2009 file and
    writes it to the given file (or file path).
    """
    conll_file = Conll2009File(docgraph)
    assert isinstance(output_file, (str, file))
    if isinstance(output_file, str):
        path_to_file = os.path.dirname(output_file)
        if not os.path.isdir(path_to_file):
            create_dir(path_to_file)
        conll_file.write(output_file)
    else:  # output_file is a file object
        output_file.write(conll_file.__str__())


if __name__ == "__main__":
    import argparse
    import cPickle as pickle

    parser = argparse.ArgumentParser()
    parser.add_argument('input_file',
                        help='pickle file of a document graph to be converted')
    parser.add_argument('output_file', nargs='?', default=sys.stdout)
    args = parser.parse_args(sys.argv[1:])

    assert os.path.isfile(args.input_file), \
        "'{}' isn't a file".format(args.input_file)

    with open(args.input_file, 'rb') as docgraph_file:
        docgraph = pickle.load(docgraph_file)
    write_conll(docgraph, args.output_file)


