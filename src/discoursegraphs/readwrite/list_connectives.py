#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from collections import OrderedDict
from lxml import etree
import argparse
import re


REDUCE_WHITESPACE_RE = re.compile(' +')

def get_connectives(tree):
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
        default=sys.stdin)
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'),
        default=sys.stdout)

    parser.add_argument('-f', '--format', dest='outformat',
        help="output file format: normal relations units" + \
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
            #pudb.set_trace()
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
