#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
This module contains a number of helper functions.
"""

import os
import fnmatch
import re
from collections import Counter
from operator import itemgetter
from types import GeneratorType

from lxml import etree

INTEGER_RE = re.compile('([0-9]+)')
FORBIDDEN_XPOINTER_RE = re.compile(':')


class TokenMapper(object):
    """
    Attributes
    ----------
    id2index : dict of (int, str)
        maps from token indices (int) to token IDs (str)
    index2id : dict of (str, int)
        maps from token IDs (str) to token indices (int)
    """
    def __init__(self, docgraph):
        """
        given a document graph, creates a bidirectional mapping from
        token IDs (str) to token indices (int).
        """
        self.id2index = {}
        self.index2id = {}
        for token_index, token_id in enumerate(docgraph.tokens):
            self.id2index[token_id] = token_index
            self.index2id[token_index] = token_id


def get_segment_token_offsets(segment_token_list, token_map):
    """
    given a list of token node IDs, returns the index of its first and last
    elements. this actually calculates the int indices, as there are weird
    formats like RS3, which use unordered / wrongly ordered IDs.

    Parameters
    ----------
    segment_token_list : list of str
        sorted list of token IDs (i.e. the tokens
        that this segment spans)
    token_map : dict of (str, int)
        a map from token IDs to token indices

    Returns
    -------
    first_token_index : int
        index of the first token of the segment
    last_token_index : int
        index of the last token of the segment
    """
    token_indices = [token_map[token_id] for token_id in segment_token_list]
    # we need to foolproof this for nasty RS3 files or other input formats
    # with unordered or wrongly orderd IDs
    return min(token_indices), max(token_indices)


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
            for text in re.split(INTEGER_RE, str(s))]


def ensure_unicode(str_or_unicode):
    """
    tests, if the input is ``bytes`` or ``str``. if it is ``bytes``, it
    will be decoded from ``UTF-8`` to unicode (str).

    In Python 3, str is unicode by default. This function handles both
    str and bytes input.
    """
    if isinstance(str_or_unicode, bytes):
        return str_or_unicode.decode('utf-8')
    elif isinstance(str_or_unicode, str):
        return str_or_unicode
    else:
        raise ValueError("Input '{0}' should be a string or unicode, "
                         "but its of type {1}".format(str_or_unicode,
                                                      type(str_or_unicode)))


def ensure_utf8(str_or_unicode):
    """
    tests, if the input is ``str`` or ``bytes``. if it is ``str`` (unicode),
    it will be encoded to ``utf-8`` bytes. If it's already bytes, return as-is.

    In Python 3, str is unicode by default.
    """
    if isinstance(str_or_unicode, bytes):
        return str_or_unicode
    elif isinstance(str_or_unicode, str):
        return str_or_unicode.encode('utf-8')
    else:
        raise ValueError(
            "Input '{0}' should be a string or unicode, but it is of "
            "type {1}".format(str_or_unicode, type(str_or_unicode)))


def ensure_ascii(str_or_unicode):
    """
    tests, if the input is ``bytes`` or ``str`` (unicode). if it is ``str``,
    it will be encoded to 7-bit ASCII with XML character references.
    If it's bytes, it will be decoded from UTF-8 first, then encoded to ASCII.

    7-bit ASCII doesn't contain umlauts, but uses XML/HTML-style escape
    sequences (e.g. ``ä`` becomes ``&#228;``).

    In Python 3, str is unicode by default.
    """
    if isinstance(str_or_unicode, bytes):
        return str_or_unicode.decode('utf-8').encode('ascii',
                                                     'xmlcharrefreplace')
    elif isinstance(str_or_unicode, str):
        return str_or_unicode.encode('ascii', 'xmlcharrefreplace')
    else:
        raise ValueError(
            "Input '{0}' should be a string or unicode, but it is of "
            "type {1}".format(str_or_unicode, type(str_or_unicode)))


def ensure_xpointer_compatibility(node_id):
    """
    makes a given node ID xpointer compatible.
    xpointer identifiers must not contain ':', so we'll
    replace it by '_'.

    Parameters
    ----------
    node_id : str or unicode or int
        a node or edge ID

    Returns
    -------
    xpointer_id : str or unicode or int
        int IDs are returned verbatim, str/unicode IDs are
        returned with ':' replaced by '_'
    """
    assert isinstance(node_id, (int, str)),\
        "node ID must be an int, str or unicode, not".format(type(node_id))
    if isinstance(node_id, str):
        return FORBIDDEN_XPOINTER_RE.sub('_', node_id)
    else:
        return node_id


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
    return {prefix + k: v for (k, v) in list(dict_like.items())}


def create_dir(path):
    """
    Creates a directory. Warns, if the directory can't be accessed. Passes,
    if the directory already exists.

    modified from http://stackoverflow.com/a/600612

    Parameters
    ----------
    path : str
        path to the directory to be created
    """
    import sys
    import errno

    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST:
            if os.path.isdir(path):
                pass
            else: # if something exists at the path, but it's not a dir
                raise
        elif exc.errno == errno.EACCES:
            sys.stderr.write("Cannot create [{0}]! Check Permissions".format(path))
            raise
        else:
            raise


def find_files(dir_or_filelist, pattern='*'):
    """
    If given a path to a directory, finds files recursively,
    e.g. all *.txt files in a given directory (or its subdirectories).
    If given a list of files, yields all of the files that match the given
    pattern.

    adapted from: http://stackoverflow.com/a/2186673
    """
    import os
    import fnmatch

    if isinstance(dir_or_filelist, str):
        directory = dir_or_filelist

        abspath = os.path.abspath(os.path.expanduser(directory))
        for root, dirs, files in os.walk(abspath):
            for basename in files:
                if fnmatch.fnmatch(basename, pattern):
                    filename = os.path.join(root, basename)
                    yield filename
    else:
        filelist = dir_or_filelist
        for filepath in filelist:
            if fnmatch.fnmatch(filepath, pattern):
                yield filepath


def sanitize_string(string_or_unicode):
    """
    remove leading/trailing whitespace and always return unicode.
    """
    if isinstance(string_or_unicode, str):
        return string_or_unicode.strip()
    elif isinstance(string_or_unicode, str):
        return string_or_unicode.decode('utf-8').strip()
    else:  # e.g. if input is None
        return ''


def xmlprint(element):
    """
    pretty prints an ElementTree (or an Element of it), or the XML
    representation of a SaltDocument (or an element
    thereof, e.g. a node, edge, layer etc.)
    """
    if isinstance(element, (etree._Element, etree._ElementTree)):
        print(etree.tostring(element, pretty_print=True))
    else:
        if hasattr(element, 'xml'):
            print(etree.tostring(element.xml, pretty_print=True))


def make_labels_explicit(docgraph):
    """
    Appends the node ID to each node label and appends the edge type to each
    edge label in the given document graph. This can be used to debug a
    graph visually with ``write_dot``.

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
            if 'label' in docgraph.nodes[node_id]:
                docgraph.nodes[node_id]['label'] =  \
                    "{0}_{1}".format(node_attribs['label'], node_id)
        return docgraph

    def make_edgelabels_explicit(docgraph):
        for from_id, to_id, edge_attribs in docgraph.edges(data=True):
            for edge_num in docgraph.edges[from_id][to_id]:
                if 'label' in docgraph.edges[from_id][to_id][edge_num]:
                    docgraph.edges[from_id][to_id][edge_num]['label'] = \
                        "{0}_{1}".format(edge_attribs['label'],
                                          edge_attribs['edge_type'])
                else:
                    docgraph.edges[from_id][to_id][edge_num]['label'] = \
                        edge_attribs['edge_type']
        return docgraph
    return make_edgelabels_explicit(make_nodelabels_explicit(docgraph))


def plot_attribute_distribution(docgraph, elements, attribute,
                                ignore_missing=True):
    '''
    creates and prints a barplot (using matplotlib) for all values that an
    attribute can have, e.g. counts of POS tags for all token nodes in a
    document graph.

    docgraph : DiscourseDocumentGraph
        the document graph from which we'll extract node/edge attributes
    elements : collections.Iterable
        an iterable of nodes or edges
    attribute : str
        name of the attribute to count (e.g. ``penn:pos``)
    ignore_missing : bool
        If True, doesn't count all those elements that don't have the given
        attribute. If False, counts them using the attribute ``NOT_PRESENT``.
    '''
    value_counts = Counter()

    if isinstance(elements, GeneratorType):
        elements = list(elements)

    if isinstance(elements[0], (str, int)):
        element_type = 'node'
    elif isinstance(elements[0], tuple):
        element_type = 'edge'
    else:
        raise ValueError('Unknown element type: '.format(element[0]))

    if element_type == 'node':
        # count all nodes with the given attribute
        for element in elements:
            try:
                value_counts[docgraph.nodes[element][attribute]] += 1
            except KeyError:
                if not ignore_missing:
                    value_counts['NOT_PRESENT'] += 1
    else: # element_type == 'edge':
        # count all edges with the given attribute
        for element in elements:
            source, target = element
            try:
                for edge in docgraph.edges[source][target]: # multidigraph
                    value_counts[docgraph.edges[source][target][edge][attribute]] += 1
            except KeyError:
                if not ignore_missing:
                    value_counts['NOT_PRESENT'] += 1

    sorted_value_counts = sorted(iter(value_counts.items()), key=itemgetter(1),
                                 reverse=True)

    # generate plot
    x = np.arange(len(sorted_value_counts))
    plt.bar(x, [attrib_count for attrib_name, attrib_count in sorted_value_counts])
    # set positions of the attribute value labels on the x-axis
    # (shifted to the right, words arranged upwards)
    _xticks = plt.xticks(
        x + 0.5,
        [attrib_name for attrib_name, attrib_count in sorted_value_counts],
        rotation=90)
    plt.show()


def create_multiple_replace_func(*args, **kwds):
    """
    You can call this function and pass it a dictionary, or any other
    combination of arguments you could pass to built-in dict in order to
    construct a dictionary. The function will return a xlat closure that
    takes as its only argument text the string on which the substitutions
    are desired and returns a copy of text with all the substitutions
    performed.

    Source: Python Cookbook 2nd ed, Chapter 1.18. Replacing Multiple Patterns
    in a Single Pass.
    https://www.safaribooksonline.com/library/view/python-cookbook-2nd/0596007973/ch01s19.html
    """
    adict = dict(*args, **kwds)
    rx = re.compile('|'.join(map(re.escape, adict)))
    def one_xlat(match):
        return adict[match.group(0)]
    def xlat(text):
        return rx.sub(one_xlat, text)
    return xlat
