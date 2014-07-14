#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann

"""
This module contains utility functions (and global variables) for dealing with
SaltXMI files.
"""

NAMESPACES = {'xmi': 'http://www.omg.org/XMI',
              'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
              'sDocumentStructure': 'sDocumentStructure',
              'saltCore': 'saltCore'}

def get_xsi_type(element):
    """
    returns the type of an element of the XML tree (incl. its namespace),
    i.e. nodes, edges, layers etc.), raises an exception if the element has no
    'xsi:type' attribute.
    """
    nsdict = NAMESPACES
    #.xpath() always returns a list, so we need to select the first element
    try:
        return element.xpath('@xsi:type', namespaces=nsdict)[0]
    except:
        raise Exception, ("The '{0}' element has no 'xsi:type' but has these "
            "attribs:\n{1}").format(element.tag, element.attrib)
