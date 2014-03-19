#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann

"""
This script parses a Conano XML file, extracts all connectives and
writes them to an output file. You can choose between three output
formats.

- normal: one connective per line
- relations: each line contains one connective and the type of relation
  it belongs to (tab-separated)
- units: prints the connective as well as its units, e.g.

'''
=====
Aber

Dass darunter einige wenige leiden müssen , ist leider unvermeidbar .

Aber das muss irgendwann ein Ende haben .
'''
"""

import os
import sys
from collections import OrderedDict
from lxml import etree
import argparse
import re

REDUCE_WHITESPACE_RE = re.compile(' +')

def get_connectives(tree):
	"""
	extracts connectives from a Conano XML file.

	Parameters
	----------
	tree : lxml.etree._ElementTree
		an element tree representing the Conano XML file to be parsed

	Returns
	-------
	connectives : OrderedDict
		an ordered dictionary which maps from a connective ID (int) to a
		dictionary of two features ('text', which maps to the
		connective (str) and 'relation', which maps to the relation
		(str) the connective is part of
	"""
	connectives = OrderedDict()
	connective_elements = tree.findall('//connective')
	for element in connective_elements:
		try:
			connectives[int(element.attrib['id'])] = {'text': element.text,
				'relation': element.attrib['relation']}
		except KeyError as e:
			sys.stderr.write("Something's wrong in file {0}. {1}\n{2}\n".format(tree.docinfo.URL, e, etree.tostring(element)))
	return connectives

def get_units(tree):
	"""
	extracts connectives and their internal and external units from a
	Conano XML file.

	Parameters
	----------
	tree : lxml.etree._ElementTree
		an element tree representing the Conano XML file to be parsed

	Returns
	-------
	ext_units : OrderedDict
		an ordered dictionary which maps from a connective ID (int) to
		the external unit (str) of that connective
	int_units : OrderedDict
		an ordered dictionary which maps from a connective ID (int) to
		the internal unit (str) of that connective
	"""
    ext_units = OrderedDict()
    int_units = OrderedDict()
    for unit in tree.findall('//unit'):
        unit_str = etree.tostring(unit, encoding='utf8', method='text').replace('\n', ' ')
        cleaned_str = REDUCE_WHITESPACE_RE.sub(' ', unit_str).strip()

        if unit.attrib['type'] == 'ext':
            ext_units[int(unit.attrib['id'])] = cleaned_str
        else:
            int_units[int(unit.attrib['id'])] = cleaned_str
    return ext_units, int_units


if __name__ == "__main__":
    desc = "This script extracts connectives (and its relation" + \
        " type, and int/ext-units) from Conano XML files."
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
        default=sys.stdin, help='the Conano XML file to be parsed. If no filename is given: read from stdin.')
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'),
        default=sys.stdout, help='the output file that shall contain the connectives. If no filename is given: write to stdout.')

    parser.add_argument('-f', '--format', dest='outformat',
        help="output file format: 'normal', 'relations' or 'units'" + \
        "\nDefaults to normal, which just prints the connectives. ")

    args = parser.parse_args()
    conano_file = args.infile
    output_file = args.outfile

    try:
        tree = etree.parse(conano_file)
        connectives = get_connectives(tree)

        if args.outformat in (None, 'normal'):
            with output_file:
                for cid in connectives:
                    connective = connectives[cid]['text'].encode('utf8')
                    output_file.write(connective + '\n')

        elif args.outformat == 'relations':
            with output_file:
                for cid in connectives:
                    connective = connectives[cid]['text'].encode('utf8')
                    relation = connectives[cid]['relation'].encode('utf8')
                    output_file.write(connective + '\t' + relation + '\n')

        elif args.outformat == 'units':
            ext_units, int_units = get_units(tree)
            with output_file:
                for cid in connectives:
                    connective = connectives[cid]['text'].encode('utf8')
                    try:
                        extunit = ext_units[cid]
                    except KeyError as e:
                        sys.stderr.write("{0} has no ext-unit with ID {1}\n".format(tree.docinfo.URL, cid))
                    try:
                        intunit = int_units[cid]
                    except KeyError as e:
                        sys.stderr.write("{0} has no int-unit with ID {1}\n".format(tree.docinfo.URL, cid))
                    output_file.write('=====\n' + connective + '\n\n' + extunit + '\n\n' + intunit + '\n\n\n')

        else:
            sys.stderr.write("Unsupported output format.\n")
            parser.print_help()
            sys.exit(1)

    except etree.XMLSyntaxError as e:
        sys.stderr.write("Can't parse file {0}. {1}\n".format(conano_file, e))
