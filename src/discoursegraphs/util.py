#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module contains a number of helper functions.
"""

import os
import re
from lxml import etree

INTEGER_RE = re.compile('([0-9]+)')


def natural_sort_key(s):
    """
    returns a key that can be used in sort functions.

    Example:

    >>> items = ['A99', 'a1', 'a2', 'a10', 'a24', 'a12', 'a100']

    The normal sort function will ignore the natural order of the
    integers in the string:

    >>> print sorted(items)
    ['A99', 'a1', 'a10', 'a100', 'a12', 'a2', 'a24']

    When we use this function as a key to the sort function,
    the natural order of the integer is considered.

    >>> print sorted(items, key=natural_sort_key)
    ['A99', 'a1', 'a2', 'a10', 'a12', 'a24', 'a100']
    """
    return [int(text) if text.isdigit() else text
            for text in re.split(INTEGER_RE, s)]


def ensure_unicode(str_or_unicode):
    """
    tests, if the input is ``str`` or ``unicode``. if it is ``str``, it
    will be decoded from ``UTF-8`` to unicode.
    """
    if isinstance(str_or_unicode, str):
        return str_or_unicode.decode('utf-8')
    elif isinstance(str_or_unicode, unicode):
        return str_or_unicode
    else:
        raise ValueError("Input '{0}' should be a string or unicode, "
                         "but its of type {1}".format(str_or_unicode,
                                                      type(str_or_unicode)))


def ensure_utf8(str_or_unicode):
    """
    tests, if the input is ``str`` or ``unicode``. if it is ``unicode``,
    it will be encoded from ``unicode`` to ``utf-8``. otherwise, the
    input string is returned.
    """
    if isinstance(str_or_unicode, str):
        return str_or_unicode
    elif isinstance(str_or_unicode, unicode):
        return str_or_unicode.encode('utf-8')
    else:
        raise ValueError(
            "Input '{0}' should be a string or unicode, but it is of "
            "type {1}".format(str_or_unicode, type(str_or_unicode)))


def ensure_ascii(str_or_unicode):
    """
    tests, if the input is ``str`` or ``unicode``. if it is ``unicode``,
    it will be encoded from ``unicode`` to 7-bit ``latin-1``.
    otherwise, the input string is converted from ``utf-8`` to 7-bit
    ``latin-1``. 7-bit latin-1 doesn't even contain umlauts, but
    XML/HTML-style escape sequences (e.g. ``ä`` becomes ``&auml;``).
    """
    if isinstance(str_or_unicode, str):
        return str_or_unicode.decode('utf-8').encode('ascii',
                                                     'xmlcharrefreplace')
    elif isinstance(str_or_unicode, unicode):
        return str_or_unicode.encode('ascii', 'xmlcharrefreplace')
    else:
        raise ValueError(
            "Input '{0}' should be a string or unicode, but it is of "
            "type {1}".format(str_or_unicode, type(str_or_unicode)))


def add_prefix(dict_like, prefix):
    """
    takes a dict (or dict-like object, e.g. etree._Attrib) and adds the
    given prefix to each key. Always returns a dict (via a typecast).

    Parameters
    ----------
    dict_like : dict (or similar)
        a dictionary or a container that implements .items()
    prefix : str
        the prefix string to be prepended to each key in the input dict

    Returns
    -------
    prefixed_dict : dict
        A dict, in which each key begins with the given prefix.
    """
    if not isinstance(dict_like, dict):
        try:
            dict_like = dict(dict_like)
        except Exception as e:
            raise ValueError("{0}\nCan't convert container to dict: "
                             "{1}".format(e, dict_like))
    return {prefix + k: v for (k, v) in dict_like.items()}


def create_dir(path):
    """
    Creates a directory. Warns, if the directory can't be accessed. Passes,
    if the directory already exists.

    @author: tzot (http://stackoverflow.com/a/600612)

    @param path: path to the directory to be created
    @type path: C{str}
    """
    import errno
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        elif exc.errno == errno.EACCES:
            print "Cannot create [%s]! Check Permissions" % path
        else:
            raise


def sanitize_string(string_or_unicode):
    """
    remove leading/trailing whitespace and always return unicode.
    """
    if isinstance(string_or_unicode, unicode):
        return string_or_unicode.strip()
    else:
        return string_or_unicode.decode('utf-8').strip()


def xmlprint(element):
    """
    pretty prints an ElementTree (or an Element of it), or the XML
    representation of a SaltDocument (or an element
    thereof, e.g. a node, edge, layer etc.)
    """
    if isinstance(element, (etree._Element, etree._ElementTree)):
        print etree.tostring(element, pretty_print=True)
    else:
        if hasattr(element, 'xml'):
            print etree.tostring(element.xml, pretty_print=True)


def make_labels_explicit(docgraph):
    """
    Appends the node ID to each node label and appends the edge type to each
    edge label in the given document graph. This can be used to debug a
    graph visually with ``networkx.write_dot``.

    Parameters
    ----------
    docgraph : DiscourseDocumentGraph
        document graph from which the nodes will be extracted

    Returns
    -------
    explicit_docgraph : DiscourseDocumentGraph
        document graph with explicit node and edge labels
    """
    def make_nodelabels_explicit(docgraph):
        for node_id, node_attribs in docgraph.nodes(data=True):
            if 'label' in docgraph.node[node_id]:
                docgraph.node[node_id]['label'] =  \
                    u"{}_{}".format(node_attribs['label'], node_id)
        return docgraph

    def make_edgelabels_explicit(docgraph):
        for from_id, to_id, edge_attribs in docgraph.edges(data=True):
            for edge_num in docgraph.edge[from_id][to_id]:
                if 'label' in docgraph.edge[from_id][to_id][edge_num]:
                    docgraph.edge[from_id][to_id][edge_num]['label'] = \
                        u"{}_{}".format(edge_attribs['label'],
                                        edge_attribs['edge_type'])
                else:
                    docgraph.edge[from_id][to_id][edge_num]['label'] = \
                        edge_attribs['edge_type']
        return docgraph
    return make_edgelabels_explicit(make_nodelabels_explicit(docgraph))
