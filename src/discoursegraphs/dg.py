#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arne Neumann <discoursegraphs.programming@arne.cl>

from networkx import MultiDiGraph


class DiscourseDocumentGraph(MultiDiGraph):

    """
    Base class for representing annotated documents as directed graphs
    with multiple edges.

    TODO: allow layers to be a single str or set of str
    TODO: allow adding a layer by including it in **attr
    TODO: add consistency check that would allow adding a node that
        already exists in the graph, but only if the new graph has
        different attributes (layers can be the same though)
    TODO: outsource layer assertions to method?
    """

    def __init__(self):
        """
        Initialized an empty directed graph which allows multiple edges.
        """
        # super calls __init__() of base class MultiDiGraph
        super(DiscourseDocumentGraph, self).__init__()

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
        nodes : iterable container of (node, attribute dict) tuples.
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
        [(1, {'layers': {'tiger', 'token'}, 'size': 10, 'weight': 1.0, 'word': 'hello'}),
         (2, {'layers': {'token'}, 'weight': 1.0, 'word': 'world'})]
        """
        additional_attribs = attr  # will be added to each node
        for n in nodes:
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
        assert u in self.succ, "from-node doesn't exist, yet"
        assert v in self.succ, "to-node doesn't exist, yet"

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
