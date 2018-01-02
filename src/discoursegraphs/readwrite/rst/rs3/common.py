#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module contains helper functions to deal with .rs3 files that are
used by several rs3-related modules.
"""

def extract_relationtypes(rs3_xml_tree):
    """
    extracts the allowed RST relation names and relation types from
    an RS3 XML file.

    Parameters
    ----------
    rs3_xml_tree : lxml.etree._ElementTree
        lxml ElementTree representation of an RS3 XML file

    Returns
    -------
    relations : dict of (str, str)
        Returns a dictionary with RST relation names as keys (str)
        and relation types (either 'rst' or 'multinuc') as values
        (str).
    """
    return {rel.attrib['name']: rel.attrib['type']
            for rel in rs3_xml_tree.iter('rel')
            if 'type' in rel.attrib}


# FIXME: implement parentedtree2rs3()
def parentedtree2rs3(dgparented_tree, output_filepath=None):
    """Converts a DGParentedTree (representing an RST tree) to a .rs3 file.
    If no `output_filepath` is given, returns the .rs3 file content as a string.
    """
    if output_filepath is None:
        # TODO: return string representation of RS3 FILE
        raise NotImplementedError
    else:
        # TODO: write rs3 file
        raise NotImplementedError
