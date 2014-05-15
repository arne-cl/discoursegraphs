#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

import os
import sys
import argparse
from networkx import write_dot


def generic_converter_cli(docgraph_class, file_descriptor=''):
    """
    generic command line interface for importers. Will convert the file
    specified on the command line into a dot representation of the
    corresponding DiscourseDocumentGraph and write the output to stdout
    or a file specified on the command line.

    Parameters
    ----------
    docgraph_class : class
        a DiscourseDocumentGraph (or a class derived from it), not an
        instance of it!
    file_descriptor : str
        string descring the input format, e.g. 'TigerXML (syntax)'
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file',
                        help='{} file to be converted'.format(file_descriptor))
    parser.add_argument('output_file', nargs='?', default=sys.stdout)
    args = parser.parse_args(sys.argv[1:])

    assert os.path.isfile(args.input_file), \
        "'{}' isn't a file".format(args.input_file)
    docgraph = docgraph_class(args.input_file)
    write_dot(docgraph, args.output_file)
