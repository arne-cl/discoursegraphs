#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

"""
The ``discoursegraph`` module specifies a ``DisourseDocumentGraph``,
the fundamential data structure used in this package. It is a slightly
modified ``networkx.MultiDiGraph``, which enforces every node and edge to have
a ``layers`` attribute (which maps to the set of layers (str) it belongs to).

TODO: implement a DiscourseCorpusGraph
"""

from collections import defaultdict
from enum import Enum
from networkx import MultiDiGraph
from discoursegraphs.relabel import relabel_nodes
from discoursegraphs.util import natural_sort_key


class EdgeTypes(Enum):
    pointing_relation = 'points_to'
    # reverse_pointing_relation = 'is_pointed_to_by' # not needed right now
    dominance_relation = 'dominates'
    reverse_dominance_relation = 'is_dominated_by'
    spanning_relation = 'spans'
    # reverse_spanning_relation = 'is_part_of' # not needed right now
    precedence_relation = 'precedes'


class DiscourseDocumentGraph(MultiDiGraph):
    """
    Base class for representing annotated documents as directed graphs
    with multiple edges.

    Attributes
    ----------
    ns : str
        the namespace of the graph (default: discoursegraph)
    root : str
        name of the document root node ID
        (default: self.ns+':root_node')
    sentences : list of str
        sorted list of all sentence root node IDs (of sentences
        contained in this document graph -- iff the document was annotated
        for sentence boundaries in one of the layers present in this graph)
    tokens : list of int
        a list of node IDs (int) which represent the tokens in the
        order they occur in the text

    TODO list:

    - allow layers to be a single str or set of str
    - allow adding a layer by including it in ``**attr``
    - add consistency check that would allow adding a node that
      already exists in the graph, but only if the new graph has
      different attributes (layers can be the same though)
    - outsource layer assertions to method?
    """
    def __init__(self, name='', namespace='discoursegraph'):
        """
        Initialized an empty directed graph which allows multiple edges.

        Parameters
        ----------
        name : str or None
            the name or ID of the graph to be generated.
        namespace : str
            the namespace of the graph (default: discoursegraph)
        """
        # super calls __init__() of base class MultiDiGraph
        super(DiscourseDocumentGraph, self).__init__()
        self.name = name
        self.ns = namespace
        self.root = self.ns+':root_node'
        self.sentences = []
        self.tokens = []

    def add_node(self, n, layers, attr_dict=None, **attr):
        """Add a single node n and update node attributes.

        Parameters
        ----------
        n : node
            A node can be any hashable Python object except None.
        layers : set of str
            the set of layers the node belongs to,
            e.g. {'tiger:token', 'anaphoricity:annotation'}
        attr_dict : dictionary, optional (default= no attributes)
            Dictionary of node attributes.  Key/value pairs will
            update existing data associated with the node.
        attr : keyword arguments, optional
            Set or change attributes using key=value.

        See Also
        --------
        add_nodes_from

        Examples
        --------
        >>> from discoursegraphs import DiscourseDocumentGraph
        >>> d = DiscourseDocumentGraph()
        >>> d.add_node(1, {'node'})

        # adding the same node with a different layer
        >>> d.add_node(1, {'number'})
        >>> d.nodes(data=True)
        [(1, {'layers': {'node', 'number'}})]

        Use keywords set/change node attributes:

        >>> d.add_node(1, {'node'}, size=10)
        >>> d.add_node(3, layers={'num'}, weight=0.4, UTM=('13S',382))
        >>> d.nodes(data=True)
        [(1, {'layers': {'node', 'number'}, 'size': 10}),
         (3, {'UTM': ('13S', 382), 'layers': {'num'}, 'weight': 0.4})]

        Notes
        -----
        A hashable object is one that can be used as a key in a Python
        dictionary. This includes strings, numbers, tuples of strings
        and numbers, etc.

        On many platforms hashable items also include mutables such as
        NetworkX Graphs, though one should be careful that the hash
        doesn't change on mutables.
        """
        assert isinstance(layers, set), \
            "'layers' parameter must be given as a set of strings."
        assert all((isinstance(layer, str) for layer in layers)), \
            "All elements of the 'layers' set must be strings."
        # add layers to keyword arguments dict
        attr.update({'layers': layers})

        # set up attribute dict
        if attr_dict is None:
            attr_dict = attr
        else:
            try:
                attr_dict.update(attr)
            except AttributeError as e:
                raise AttributeError("The attr_dict argument must be "
                                     "a dictionary: ".format(e))

        # if there's no node with this ID in the graph, yet
        if n not in self.succ:
            self.succ[n] = {}
            self.pred[n] = {}
            self.node[n] = attr_dict
        else:  # update attr even if node already exists
            # if a node exists, its attributes will be updated, except
            # for the layers attribute. the value of 'layers' will
            # be the union of the existing layers set and the new one.
            existing_layers = self.node[n]['layers']
            all_layers = existing_layers.union(layers)
            attrs_without_layers = {k: v for (k, v) in attr_dict.items()
                                    if k != 'layers'}
            self.node[n].update(attrs_without_layers)
            self.node[n].update({'layers': all_layers})

    def add_nodes_from(self, nodes, **attr):
        """Add multiple nodes.

        Parameters
        ----------
        nodes : iterable container
            A container of nodes (list, dict, set, etc.).
            OR
            A container of (node, attribute dict) tuples.
            Node attributes are updated using the attribute dict.
        attr : keyword arguments, optional (default= no attributes)
            Update attributes for all nodes in nodes.
            Node attributes specified in nodes as a tuple
            take precedence over attributes specified generally.

        See Also
        --------
        add_node

        Examples
        --------
        >>> from discoursegraphs import DiscourseDocumentGraph
        >>> d = DiscourseDocumentGraph()
        >>> d.add_nodes_from([(1, {'layers':{'token'}, 'word':'hello'}), \
                (2, {'layers':{'token'}, 'word':'world'})])
        >>> d.nodes(data=True)
        [(1, {'layers': {'token'}, 'word': 'hello'}),
         (2, {'layers': {'token'}, 'word': 'world'})]

        Use keywords to update specific node attributes for every node.

        >>> d.add_nodes_from(d.nodes(data=True), weight=1.0)
        >>> d.nodes(data=True)
        [(1, {'layers': {'token'}, 'weight': 1.0, 'word': 'hello'}),
         (2, {'layers': {'token'}, 'weight': 1.0, 'word': 'world'})]

        Use (node, attrdict) tuples to update attributes for specific
        nodes.

        >>> d.add_nodes_from([(1, {'layers': {'tiger'}})], size=10)
        >>> d.nodes(data=True)
        [(1, {'layers': {'tiger', 'token'}, 'size': 10, 'weight': 1.0,
              'word': 'hello'}),
         (2, {'layers': {'token'}, 'weight': 1.0, 'word': 'world'})]
        """
        additional_attribs = attr  # will be added to each node
        for n in nodes:
            try:  # check, if n is a node_id or a (node_id, attrib dict) tuple
                newnode = n not in self.succ  # is node in the graph, yet?
            except TypeError:  # n is a (node_id, attribute dict) tuple
                node_id, ndict = n
                assert 'layers' in ndict, \
                    "Every node must have a 'layers' attribute."
                layers = ndict['layers']
                assert isinstance(layers, set), \
                    "'layers' must be specified as a set of strings."
                assert all((isinstance(layer, str) for layer in layers)), \
                    "All elements of the 'layers' set must be strings."

                if node_id not in self.succ:  # node doesn't exist, yet
                    self.succ[node_id] = {}
                    self.pred[node_id] = {}
                    newdict = additional_attribs.copy()
                    newdict.update(ndict)  # all given attribs incl. layers
                    self.node[node_id] = newdict
                else:  # node already exists
                    existing_layers = self.node[node_id]['layers']
                    all_layers = existing_layers.union(layers)

                    self.node[node_id].update(ndict)
                    self.node[node_id].update(additional_attribs)
                    self.node[node_id].update({'layers': all_layers})
                continue  # process next node

            # newnode check didn't raise an exception
            if newnode:  # n is a node_id and it's not in the graph, yet
                self.succ[n] = {}
                self.pred[n] = {}
                self.node[n] = attr.copy()
                # since the node isn't represented as a
                # (node_id, attribute dict) tuple, we don't know which layers
                # it is part of. Therefore, we'll add the namespace of the
                # graph as the node layer
                self.node[n].update({'layers': set([self.ns])})
            else:  # n is a node_id and it's already in the graph
                self.node[n].update(attr)

    def add_edge(self, u, v, layers, key=None, attr_dict=None, **attr):
        """Add an edge between u and v.

        An edge can only be added if the nodes u and v already exist.
        This decision was taken to ensure that all nodes are associated
        with at least one (meaningful) layer.

        Edge attributes can be specified with keywords or by providing
        a dictionary with key/value pairs. In contrast to other
        edge attributes, layers can only be added not overwriten or
        deleted.

        Parameters
        ----------
        u,v : nodes
            Nodes can be, for example, strings or numbers.
            Nodes must be hashable (and not None) Python objects.
        layers : set of str
            the set of layers the edge belongs to,
            e.g. {'tiger:token', 'anaphoricity:annotation'}
        key : hashable identifier, optional (default=lowest unused integer)
            Used to distinguish multiedges between a pair of nodes.
        attr_dict : dictionary, optional (default= no attributes)
            Dictionary of edge attributes.  Key/value pairs will
            update existing data associated with the edge.
        attr : keyword arguments, optional
            Edge data (or labels or objects) can be assigned using
            keyword arguments.

        See Also
        --------
        add_edges_from : add a collection of edges

        Notes
        -----
        To replace/update edge data, use the optional key argument
        to identify a unique edge.  Otherwise a new edge will be created.

        NetworkX algorithms designed for weighted graphs cannot use
        multigraphs directly because it is not clear how to handle
        multiedge weights.  Convert to Graph using edge attribute
        'weight' to enable weighted graph algorithms.

        Examples
        --------
        >>> from discoursegraphs import  DiscourseDocumentGraph
        >>> d = DiscourseDocumentGraph()
        >>> d.add_nodes_from([(1, {'layers':{'token'}, 'word':'hello'}), \
                (2, {'layers':{'token'}, 'word':'world'})])

        >>> d.edges(data=True)
        >>> []

        >>> d.add_edge(1, 2, layers={'generic'})

        >>> d.add_edge(1, 2, layers={'tokens'}, weight=0.7)

        >>> d.edges(data=True)
        [(1, 2, {'layers': {'generic'}}),
         (1, 2, {'layers': {'tokens'}, 'weight': 0.7})]

        >>> d.edge[1][2]
        {0: {'layers': {'generic'}}, 1: {'layers': {'tokens'}, 'weight': 0.7}}

        >>> d.add_edge(1, 2, layers={'tokens'}, key=1, weight=1.0)
        >>> d.edges(data=True)
        [(1, 2, {'layers': {'generic'}}),
         (1, 2, {'layers': {'tokens'}, 'weight': 1.0})]

        >>> d.add_edge(1, 2, layers={'foo'}, key=1, weight=1.0)
        >>> d.edges(data=True)
        [(1, 2, {'layers': {'generic'}}),
         (1, 2, {'layers': {'foo', 'tokens'}, 'weight': 1.0})]
        """
        assert isinstance(layers, set), \
            "'layers' parameter must be given as a set of strings."
        assert all((isinstance(layer, str) for layer in layers)), \
            "All elements of the 'layers' set must be strings."
        # add layers to keyword arguments dict
        attr.update({'layers': layers})

        # set up attribute dict
        if attr_dict is None:
            attr_dict = attr
        else:
            try:
                attr_dict.update(attr)
            except AttributeError as e:
                raise AttributeError("The attr_dict argument must be "
                                     "a dictionary: ".format(e))
        for node in (u, v):  # u = source, v = target
            if node not in self.nodes_iter():
                self.add_node(node, layers={self.ns})

        if v in self.succ[u]:  # if there's already an edge from u to v
            keydict = self.adj[u][v]
            if key is None:  # creating additional edge
                # find a unique integer key
                # other methods might be better here?
                key = len(keydict)
                while key in keydict:
                    key += 1
            datadict = keydict.get(key, {})  # works for existing & new edge
            existing_layers = datadict.get('layers', set())
            all_layers = existing_layers.union(layers)

            datadict.update(attr_dict)
            datadict.update({'layers': all_layers})
            keydict[key] = datadict

        else:  # there's no edge between u and v, yet
            # selfloops work this way without special treatment
            if key is None:
                key = 0
            datadict = {}
            datadict.update(attr_dict)  # includes layers
            keydict = {key: datadict}
            self.succ[u][v] = keydict
            self.pred[v][u] = keydict

    def add_edges_from(self, ebunch, attr_dict=None, **attr):
        """Add all the edges in ebunch.

        Parameters
        ----------
        ebunch : container of edges
            Each edge given in the container will be added to the
            graph. The edges can be:

                - 3-tuples (u,v,d) for an edge attribute dict d, or
                - 4-tuples (u,v,k,d) for an edge identified by key k

            Each edge must have a layers attribute (set of str).
        attr_dict : dictionary, optional  (default= no attributes)
            Dictionary of edge attributes.  Key/value pairs will
            update existing data associated with each edge.
        attr : keyword arguments, optional
            Edge data (or labels or objects) can be assigned using
            keyword arguments.


        See Also
        --------
        add_edge : add a single edge

        Notes
        -----
        Adding the same edge twice has no effect but any edge data
        will be updated when each duplicate edge is added.

        An edge can only be added if the source and target nodes are
        already present in the graph. This decision was taken to ensure
        that all edges are associated with at least one (meaningful)
        layer.

        Edge attributes specified in edges as a tuple (in ebunch) take
        precedence over attributes specified otherwise (in attr_dict or
        attr). Layers can only be added (via a 'layers' edge attribute),
        but not overwritten.

        Examples
        --------
        >>> d = DiscourseDocumentGraph()
        >>> d.add_node(1, {'int'})
        >>> d.add_node(2, {'int'})

        >>> d.add_edges_from([(1, 2, {'layers': {'int'}, 'weight': 23})])
        >>> d.add_edges_from([(1, 2, {'layers': {'int'}, 'weight': 42})])

        >>> d.edges(data=True) # multiple edges between the same nodes
        [(1, 2, {'layers': {'int'}, 'weight': 23}),
         (1, 2, {'layers': {'int'}, 'weight': 42})]

        Associate data to edges

        We update the existing edge (key=0) and overwrite its 'weight'
        value. Note that we can't overwrite the 'layers' value, though.
        Instead, they are added to the set of existing layers

        >>> d.add_edges_from([(1, 2, 0, {'layers':{'number'}, 'weight':66})])
        [(1, 2, {'layers': {'int', 'number'}, 'weight': 66}),
         (1, 2, {'layers': {'int'}, 'weight': 42})]
        """
        # set up attribute dict
        if attr_dict is None:
            attr_dict = attr
        else:
            try:
                attr_dict.update(attr)
            except AttributeError as e:
                raise AttributeError("The attr_dict argument must be "
                                     "a dictionary: ".format(e))
        # process ebunch
        for e in ebunch:
            ne = len(e)
            if ne == 4:
                u, v, key, dd = e
            elif ne == 3:
                u, v, dd = e
                key = None
            else:
                raise AttributeError(
                    "Edge tuple %s must be a 3-tuple (u,v,attribs) "
                    "or 4-tuple (u,v,key,attribs)." % (e,))

            assert 'layers' in dd, \
                "Every edge must have a 'layers' attribute."
            layers = dd['layers']
            assert isinstance(layers, set), \
                "'layers' must be specified as a set of strings."
            assert all((isinstance(layer, str)
                        for layer in layers)), \
                "All elements of the 'layers' set must be strings."
            additional_layers = attr_dict.get('layers', {})
            if additional_layers:
                assert isinstance(additional_layers, set), \
                    "'layers' must be specified as a set of strings."
                assert all((isinstance(layer, str)
                            for layer in additional_layers)), \
                    "'layers' set must only contain strings."
            # union of layers specified in ebunch tuples,
            # attr_dict and **attr
            new_layers = layers.union(additional_layers)

            if u in self.adj:  # edge with u as source already exists
                keydict = self.adj[u].get(v, {})
            else:
                keydict = {}
            if key is None:
                # find a unique integer key
                # other methods might be better here?
                key = len(keydict)
                while key in keydict:
                    key += 1
            datadict = keydict.get(key, {})  # existing edge attribs
            existing_layers = datadict.get('layers', set())
            datadict.update(attr_dict)
            datadict.update(dd)
            updated_attrs = {k: v for (k, v) in datadict.items()
                             if k != 'layers'}

            all_layers = existing_layers.union(new_layers)
            # add_edge() checks if u and v exist, so we don't need to
            self.add_edge(u, v, layers=all_layers, key=key,
                          attr_dict=updated_attrs)

    def get_token(self, token_node_id, token_attrib='token'):
        """
        given a token node ID, returns the token unicode string.

        Parameters
        ----------
        token_node_id : str
            the ID of the token node
        token_attrib : str
            name of the node attribute that contains the token string as its
            value (default: token).

        Returns
        -------
        token : unicode
            the token string
        """
        return self.node[token_node_id][self.ns+':'+token_attrib]

    def get_tokens(self, token_attrib='token', token_strings_only=False):
        """
        returns a list of (token node ID, token) which represent the tokens
        of the input document (in the order they occur).

        Parameters
        ----------
        token_attrib : str
            name of the node attribute that contains the token string as its
            value (default: token).

        Yields
        -------
        result : generator of (str, unicode) or generator unicode
            a generator of (token node ID, token string) tuples if
            token_strings_only==False, a generator of token strings otherwise
        """
        if token_strings_only:
            for token_id in self.tokens:
                yield self.get_token(token_id, token_attrib)
        else:
            for token_id in self.tokens:
                yield (token_id, self.get_token(token_id, token_attrib))

    def merge_graphs(self, other_docgraph):
        """
        Merges another document graph into the current one, thereby adding all
        the necessary nodes and edges (with attributes, layers etc.).

        NOTE: This will only work if both graphs have exactly the same
        tokenization.
        """
        # renaming the tokens of the other graph to match this one
        rename_tokens(other_docgraph, self)
        self.add_nodes_from(other_docgraph.nodes(data=True))

        # copy token node attributes to the current namespace
        for node_id, node_attrs in other_docgraph.nodes(data=True):
            if istoken(other_docgraph, node_id):
                if self.ns+':token' not in self.node[node_id]:
                    self.node[node_id].update({self.ns+':token': other_docgraph.get_token(node_id)})
        self.add_edges_from(other_docgraph.edges(data=True))

        # workaround for issues #89 and #96
        # copy the token node IDs / sentence node IDs from the other graph,
        # if this graph doesn't have such lists, yet
        if other_docgraph.name and not self.name:
            self.name = other_docgraph.name
        if other_docgraph.tokens and not self.tokens:
            self.tokens = other_docgraph.tokens
        if other_docgraph.sentences and not self.sentences:
            self.sentences = other_docgraph.sentences

    def add_precedence_relations(self):
        """
        add precedence relations to the document graph (i.e. an edge from the
        root node to the first token node, an edge from the first token node to
        the second one etc.)
        """
        assert len(self.tokens) > 1, \
            "There are no tokens to add precedence relations to."
        self.add_edge(self.root, self.tokens[0],
                      layers={self.ns, self.ns+':precedence'},
                      edge_type=EdgeTypes.precedence_relation)
        for i, token_node_id in enumerate(self.tokens[1:]):
            # edge from token_n to token_n+1
            self.add_edge(self.tokens[i], token_node_id,
                          layers={self.ns, self.ns+':precedence'},
                          edge_type=EdgeTypes.precedence_relation)


def rename_tokens(docgraph_with_old_names, docgraph_with_new_names):
    """
    Renames the tokens of a graph (``docgraph_with_old_names``) in-place,
    using the token names of another document graph
    (``docgraph_with_new_names``). Also updates the ``.tokens`` list of the old
    graph.

    This will only work, iff both graphs have the same tokenization.
    """
    old2new = create_token_mapping(docgraph_with_old_names,
                                   docgraph_with_new_names)
    relabel_nodes(docgraph_with_old_names, old2new, copy=False)
    new_token_ids = old2new.values()

    # new_token_ids could be empty (if docgraph_with_new_names is still empty)
    if new_token_ids:
        docgraph_with_old_names.tokens = new_token_ids


def create_token_mapping(docgraph_with_old_names, docgraph_with_new_names):
    old_token_ids = list(docgraph_with_old_names.get_tokens())
    new_token_ids = docgraph_with_new_names.get_tokens()

    old2new = {}
    for i, (new_tok_id, new_tok) in enumerate(new_token_ids):
        old_tok_id, old_tok = old_token_ids[i]
        if new_tok != old_tok:  # token mismatch
            raise ValueError(
                u"Tokenization mismatch: {0} ({1}) vs. {2} ({3})\n"
                "\t{4} != {5}".format(
                    docgraph_with_new_names.name, docgraph_with_new_names.ns,
                    docgraph_with_old_names.name, docgraph_with_old_names.ns,
                    new_tok, old_tok).encode('utf-8'))
        else:
            old2new[old_tok_id] = new_tok_id
    return old2new



def get_annotation_layers(docgraph):
    """
    WARNING: this is higly inefficient!
    Fix this via Issue #36.

    Returns
    -------
    all_layers : set or dict
        the set of all annotation layers used in the given graph
    """
    node_layers = get_node_annotation_layers(docgraph)
    return node_layers.union(get_edge_annotation_layers(docgraph))


def get_top_level_layers(docgraph):
    """
    WARNING: this is higly inefficient!
    Fix this via Issue #36.

    Returns
    -------
    top_level_layers : set
        the set of all top level annotation layers used in the given graph
        (e.g. 'tiger' or 'rst', but not 'tiger:sentence:root' or 'rst:segment')
    """
    return set(layer.split(':')[0]
               for layer in get_annotation_layers(docgraph))


def get_node_annotation_layers(docgraph):
    """
    WARNING: this is higly inefficient!
    Fix this via Issue #36.

    Returns
    -------
    all_layers : set or dict
        the set of all annotation layers used for annotating nodes in the given
        graph
    """
    all_layers = set()
    for node_id, node_attribs in docgraph.nodes_iter(data=True):
        for layer in node_attribs['layers']:
            all_layers.add(layer)
    return all_layers


def get_edge_annotation_layers(docgraph):
    """
    WARNING: this is higly inefficient!
    Fix this via Issue #36.

    Returns
    -------
    all_layers : set or dict
        the set of all annotation layers used for annotating edges in the given
        graph
    """
    all_layers = set()
    for source_id, target_id, edge_attribs in docgraph.edges_iter(data=True):
        for layer in edge_attribs['layers']:
            all_layers.add(layer)
    return all_layers


def get_span(docgraph, node_id):
    """
    returns all the tokens that are dominated or in a span relation with
    the given node.

    Returns
    -------
    span : list of str
        sorted list of token nodes (token node IDs)
    """
    span = []
    for from_id, to_id, edge_attribs in docgraph.out_edges_iter(node_id,
                                                                data=True):
        if from_id == to_id:
            pass  # ignore self-loops
        # ignore pointing relations
        if edge_attribs['edge_type'] != EdgeTypes.pointing_relation:
            if docgraph.ns+':token' in docgraph.node[to_id]:
                span.append(to_id)
            else:
                span.extend(get_span(docgraph, to_id))
    return sorted(span, key=natural_sort_key)


def get_text(docgraph, node_id=None):
    """
    returns the text (joined token strings) that the given node dominates
    or spans. If no node ID is given, returns the complete text of the
    document
    """
    if node_id:
        tokens = (docgraph.node[node_id][docgraph.ns+':token']
                  for node_id in get_span(docgraph, node_id))
    else:
        tokens = (docgraph.node[token_id][docgraph.ns+':token']
                  for token_id in docgraph.tokens)
    return ' '.join(tokens)


def tokens2text(docgraph, token_ids):
    """
    given a list of token node IDs, returns a their string representation
    (concatenated token strings).
    """
    return ' '.join(docgraph.node[token_id][docgraph.ns+':token']
                    for token_id in token_ids)


def istoken(docgraph, node_id):
    """returns true, iff the given node ID belongs to a token node."""
    return docgraph.ns+':token' in docgraph.node[node_id]


def select_neighbors_by_layer(docgraph, node, layer, data=False):
    """
    Get all neighboring nodes belonging to (any of) the given layer(s),
    A neighboring node is a node that the given node connects to with an
    outgoing edge.

    Parameters
    ----------
    docgraph : DiscourseDocumentGraph
        document graph from which the nodes will be extracted
    layer : str or collection of str
        name(s) of the layer(s)
    data : bool
        If True, results will include node attributes.

    Yields
    ------
    nodes : generator of str or generator of (str, dict) tuple
        If data is False (default), a generator of neighbor node IDs
        that are present in the given layer. If data is True,
        a generator of (node ID, node attrib dict) tuples.
    """
    for node_id in docgraph.neighbors_iter(node):
        node_layers = docgraph.node[node_id]['layers']
        if isinstance(layer, (str, unicode)):
            condition = layer in node_layers
        else:  # ``layer`` is a list/set/dict of layers
            condition = any(l in node_layers for l in layer)

        if condition:
            yield (node_id, docgraph.node[node_id]) if data else (node_id)


def select_nodes_by_layer(docgraph, layer, data=False):
    """
    Get all nodes belonging to (any of) the given layer(s).

    Parameters
    ----------
    docgraph : DiscourseDocumentGraph
        document graph from which the nodes will be extracted
    layer : str or collection of str
        name(s) of the layer(s)
    data : bool
        If True, results will include node attributes.

    Yields
    ------
    nodes : generator of str or generator of (str, dict) tuple
        If data is False (default), a generator of node IDs that are present in
        the given layer. If data is True, a generator of (node ID, node attrib
        dict) tuples.
    """
    for node_id, node_attribs in docgraph.nodes_iter(data=True):
        if isinstance(layer, (str, unicode)):
            condition = layer in node_attribs['layers']
        else:  # ``layer`` is a list/set/dict of layers
            condition = any(l in node_attribs['layers'] for l in layer)
        if condition:
            if data:
                yield (node_id, node_attribs)
            else:
                yield node_id


def select_edges_by(docgraph, layer=None, edge_type=None, data=False):
    """
    get all edges with the given edge type and layer.

    Parameters
    ----------
    docgraph : DiscourseDocumentGraph
        document graph from which the nodes will be extracted
    layer : str
        name of the layer
    edge_type : str
        Type of the edges to be extracted (Edge types are defined in the
        Enum ``EdgeTypes``).
    data : bool
        If True, results will include edge attributes.

    Returns
    -------
    edges : generator of str
        a container/list of edges (represented as (source node ID, target
        node ID) tuples). If data is True, edges are represented as
        (source node ID, target node ID, edge attribute dict) tuples.
    """
    edge_type_eval = "edge_attribs['edge_type'] == '{}'".format(edge_type)
    layer_eval = "'{}' in edge_attribs['layers']".format(layer)

    def select_edges(docgraph, conditions, data):
        """yields all edges that meet the conditions given as eval strings"""
        for (from_id, to_id, edge_attribs) in docgraph.edges(data=True):
            # if all conditions are fulfilled
            # we need to add edge_attribs to the namespace eval is working in
            if all((eval(cond, {'edge_attribs': edge_attribs})
                    for cond in conditions)):
                if data:
                    yield (from_id, to_id, edge_attribs)
                else:
                    yield (from_id, to_id)

    if layer is not None:
        if edge_type is not None:
            return select_edges(docgraph, data=data,
                                conditions=[edge_type_eval, layer_eval])
        else:  # filter by layer, but not by edge type
            return select_edges(docgraph, conditions=[layer_eval], data=data)

    else:  # don't filter layers
        if edge_type is not None:  # filter by edge type, but not by layer
            return select_edges(docgraph, data=data,
                                conditions=[edge_type_eval])
        else:  # neither layer, nor edge type is filtered
            return docgraph.edges(data=data)


def __walk_chain(rel_dict, from_id):
    """
    given a dict of pointing relations and a start node, this function
    will return a list of paths (each path is represented as a list of
    node IDs -- from the first node of the path to the last).

    Parameters
    ----------
    rel_dict : dict
        a dictionary mapping from an edge source node (node ID str)
        to a set of edge target nodes (node ID str)
    from_id : str

    Returns
    -------
    paths_starting_with_id : list of list of str
        each list constains a list of strings (i.e. a list of node IDs,
        which represent a chain of pointing relations)
    """
    paths_starting_with_id = []
    for to_id in rel_dict[from_id]:
        if to_id in rel_dict:
            for tail in __walk_chain(rel_dict, to_id):
                paths_starting_with_id.append([from_id] + tail)
        else:
            paths_starting_with_id.append([from_id, to_id])
    return paths_starting_with_id


def get_pointing_chains(docgraph, layer=None):
    """
    returns a list of chained pointing relations (e.g. coreference chains)
    found in the given document graph.
    """
    pointing_relations = select_edges_by(docgraph, layer=layer,
                                         edge_type=EdgeTypes.pointing_relation)

    # a markable can point to more than one antecedent, cf. Issue #40
    rel_dict = defaultdict(set)
    for from_id, to_id in pointing_relations:
        rel_dict[from_id].add(to_id)

    all_chains = [__walk_chain(rel_dict, from_id)
                  for from_id in rel_dict.iterkeys()]

    # don't return partial chains, i.e. instead of returning [a,b], [b,c] and
    # [a,b,c,d], just return [a,b,c,d]
    unique_chains = []
    for i, from_id_chains in enumerate(all_chains):
        # there will be at least one chain in this list and
        # its first element is the from ID
        from_id = from_id_chains[0][0]

        # chain lists not starting with from_id
        other_chainlists = all_chains[:i] + all_chains[i+1:]
        if not any([from_id in chain
                    for chain_list in other_chainlists
                    for chain in chain_list]):
                        unique_chains.extend(from_id_chains)
    return unique_chains
