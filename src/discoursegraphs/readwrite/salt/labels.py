#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module handles the parsing of SALT labels.

There are three types of labels (SFeature, SElementId, SAnnotation).
Labels can occur as children of these elements: 'layers', 'nodes', 'edges'
and '{sDocumentStructure}SDocumentGraph'.
"""

from elements import SaltElement, get_element_name, get_xsi_type


def get_namespace(label):
    """
    returns the namespace of an etree element or None, if the element
    doesn't have that attribute.
    """
    if 'namespace' in label.attrib:
        return label.attrib['namespace']
    else:
        return None

def get_annotation(label):
    """
    returns an annotation (key, value) tuple given an etree element
    (with tag 'labels' and xsi type 'SAnnotation'), e.g. ('tiger.pos', 'ART')
    """
    assert get_xsi_type(label) == 'SAnnotation'
    return (label.attrib['name'], label.attrib['valueString'])

