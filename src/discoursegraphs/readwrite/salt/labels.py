#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module handles the parsing of SALT labels.

There are three types of labels (SFeature, SElementId, SAnnotation).
Labels can occur as children of these elements: 'layers', 'nodes', 'edges'
and '{sDocumentStructure}SDocumentGraph'.
"""

from lxml.builder import ElementMaker
from discoursegraphs.readwrite.salt.util import (get_xsi_type, string2xmihex,
                                                 NAMESPACES)

XSI = "http://www.w3.org/2001/XMLSchema-instance"


class SaltLabel(object):
    """
    Two or more ``SaltLabel``s are attached to each element in a SaltXMI
    file: one label representing the name (``SNAME``) of the element, one
    representing its ID and one label for each kind of annotation associated
    with that element.
    """
    def __init__(self, name, value, xsi_type, namespace=None, hexvalue=None):
        """
        create a SaltLabel from scratch.

        Parameters
        ----------
        name : str
            the name of the label, e.g. ``SNAME`` or ``id``
        namespace : str or None
            the namespace of the label, e.g. ``salt`` or ``graph``
        value : str
            the actual label value, e.g. ``sSpan19`` or ``NP``
        hexvalue: str or None
            a weird hex-based representation of the value, which always starts
            with ``ACED00057``. If it is not set, we can automatically generate
            it, but we can't guarantee that it matches the value SaltNPepper
            would have generated.
        xsi_type : str
            the type of the label, e.g. ``saltCore:SFeature`` or
            ``saltCore:SAnnotation``
        """
        self.xsi_type = xsi_type
        self.namespace = namespace if namespace else None
        self.name = name
        self.value = value
        self.hexvalue = hexvalue if hexvalue else string2xmihex(value)

    @classmethod
    def from_etree(cls, etree_element):
        """
        creates a ``SaltLabel`` from an etree element representing a label
        element in a SaltXMI file.

        A label element in SaltXMI looks like this::

            <labels xsi:type="saltCore:SFeature" namespace="salt"
                name="SNAME" value="ACED0005740007735370616E3139"
                valueString="sSpan19"/>

        Parameters
        ----------
        etree_element : lxml.etree._Element
            an etree element parsed from a SaltXMI document
        """
        return cls(name=etree_element.attrib['name'],
                   value=etree_element.attrib['valueString'],
                   xsi_type=get_xsi_type(etree_element),
                   namespace=etree_element.attrib.get('namespace'),
                   hexvalue=etree_element.attrib['value'])

    def to_etree(self):
        """
        creates an etree element of a ``SaltLabel`` that mimicks a SaltXMI
        <labels> element
        """
        attribs = {
            '{{{pre}}}type'.format(pre=NAMESPACES['xsi']): self.xsi_type,
            'namespace': self.namespace, 'name': self.name,
            'value': self.hexvalue, 'valueString': self.value}
        non_empty_attribs = {key: val for (key, val) in attribs.items()
                             if val is not None}
        E = ElementMaker()
        return E('labels', non_empty_attribs)


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
    assert get_xsi_type(label) == 'saltCore:SAnnotation'
    return (label.attrib['name'], label.attrib['valueString'])
