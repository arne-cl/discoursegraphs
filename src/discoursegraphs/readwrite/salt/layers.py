#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module handles the parsing of SALT layers.
"""

import re
from lxml import etree

from discoursegraphs.readwrite.salt.elements import SaltElement

DIGITS = re.compile('\d+')

class SaltLayer(SaltElement):
    """
    A ``SaltLayer`` instances describes a Salt XML layer. In Salt, a layer groups
    nodes and edges belonging to the same annotation level, e.g. syntax or
    information structure.
    """
    def __init__(self, element, element_id, doc_id):
        """
        Parameters
        ----------
        element : lxml.etree._Element
            an `etree._Element` is the XML representation of a Salt element.
            here: a `layer` element
        element_id : int
            the index of the element (used to connect edges to nodes)
        doc_id : str
            the ID of the SaltXML document

        Attributes
        ----------
        name : str
            represents the type of the layer, e.g. `tiger` or `mmax`
        nodes : list of int
            a list of node indices which point to the nodes belonging to this
            layer
        layer_id : int
            the index of the layer
        type : str
            is always 'SLayer' (the type of the corresponding SaltXML element)
        xml : etree._Element
            etree element representing this Salt layer
        """
        super(SaltLayer, self).__init__(element, doc_id)
        nodes_str = element.xpath('@nodes')[0]
        self.nodes = [int(node_id) for node_id in DIGITS.findall(nodes_str)]
        self.layer_id = element_id

