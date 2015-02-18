DiscourseGraphs
===============

.. image:: http://img.shields.io/pypi/dm/discoursegraphs.svg
   :alt: PyPI download counter
   :align: right
   :target: https://pypi.python.org/pypi/discoursegraphs#downloads
.. image:: http://img.shields.io/pypi/v/discoursegraphs.svg
   :alt: Latest version
   :align: right
   :target: https://pypi.python.org/pypi/discoursegraphs
.. image:: http://img.shields.io/badge/license-BSD-yellow.svg
   :alt: BSD License
   :align: right
   :target: http://opensource.org/licenses/BSD-3-Clause


This library enables you to process linguistic corpora with multiple levels
of annotations by:

1. converting the different annotation formats into separate graphs and 
2. merging these graphs into a single multidigraph (based on the common
   tokenization of the annotation layers)
3. exporting your (merged) graphs into several output formats
4. `visualizing linguistic graphs`_ directly in an `IPython notebook`_

.. _`visualizing linguistic graphs`: http://nbviewer.ipython.org/github/arne-cl/alt-mulig/blob/master/python/discoursegraphs-visualization-examples.ipynb
.. _`IPython notebook`: http://ipython.org/notebook.html

Import formats
--------------

So far, the following formats can be imported and merged:

* `TigerXML`_ (a format for representing tree-like syntax graphs with
  secondary edges)
* `Penn Treebank <http://www.cis.upenn.edu/~treebank/>`_ format (an s-expressions/lisp/brackets format for representing syntax trees)
* RS3 (a format used by `RSTTool`_ to
  annotate documents with Rhetorical Structure Theory)
* `MMAX2`_ (a format / GUI tool for annotating spans and connections between
  them (e.g. coreferences)
* `CoNLL 2009`_ and `CoNLL 2010`_ formats (used for annotating i.a. dependency parses
  and coreference links)
* ConanoXML (a format for annotating connectives, used by `Conano`_)
* Decour (an XML format used by a corpus of
  `DEceptive statements in Italian COURts <http://www.lrec-conf.org/proceedings/lrec2012/pdf/377_Paper.pdf>`_)
* `EXMARaLDA <http://exmaralda.org/>`_, a format for annotating spans in spoken
  or written language
* an ad-hoc plain text format for annotating expletives (you're probably not
  interested in)

.. _`TigerXML`: http://www.ims.uni-stuttgart.de/forschung/ressourcen/werkzeuge/TIGERSearch/doc/html/TigerXML.html
.. _`RSTTool`: http://www.wagsoft.com/RSTTool/
.. _`MMAX2`: http://mmax2.sourceforge.net/
.. _`CoNLL 2009`: http://ufal.mff.cuni.cz/conll2009-st/task-description.html
.. _`CoNLL 2010`: http://web.archive.org/web/20130119013221/http://www.inf.u-szeged.hu/rgai/conll2010st
.. _`Conano`: http://www.ling.uni-potsdam.de/acl-lab/Forsch/pcc/pcc.html

Export formats
--------------

discoursegraphs can export graphs into the following formats /
for the following tools:

* dot format, which is used by the open source graph visualization software `graphviz <>`_
* geoff format, used by the `neo4j <http://neo4j.com/>`_ graph database (please
  use my fork of the `neonx <https://github.com/arne-cl/neonx>`_ library to make this work)
* direct data export into a running neon4j database (see above)
* `GEFX <http://gexf.net/format/>`_, `GML <http://www.fim.uni-passau.de/index.php?id=17297&L=1>`_
  and `GraphML <http://graphml.graphdrawing.org/>`_ (common interchange formats for graphs used
  by various tools such as `Gephi <https://gephi.github.io/>`_ and
  `Cytoscape <http://www.cytoscape.org/>`_)
* `PAULA XML 1.1 <https://www.sfb632.uni-potsdam.de/en/paula.html>`_, an exchange format
  for linguistic data (exporter is still buggy)
* `EXMARaLDA <http://exmaralda.org/>`_, a tool for annotating spans in spoken
  or written language
* `CoNLL 2009`_ (so far, only tokens, sentence boundaries and coreferences are exported)


Installation
------------

This should work on both Linux and Mac OSX using `Python 2.7`_ and
either `pip`_ or easy_install.

.. _`Python 2.7`: https://www.python.org/downloads/
.. _`pip`: https://pip.pypa.io/en/latest/installing.html

Install from PyPI
~~~~~~~~~~~~~~~~~

::

    pip install discoursegraphs # prepend 'sudo' if needed

or, if you're oldschool:

::

    easy_install discoursegraphs # prepend 'sudo' if needed


Install from source
~~~~~~~~~~~~~~~~~~~

::

    git clone https://github.com/arne-cl/discoursegraphs.git
    cd discoursegraphs
    python setup.py install # prepend 'sudo' if needed


Usage
-----

The command line interface of DiscourseGraphs allows you to
merge syntax, rhetorical structure, connectives and expletives
annotation files into one graph and either uploads it to a running
instance of the `neo4j`_ graph database or generates output in `dot`_
or `geoff`_ format.

.. _`neo4j`:  http://www.neo4j.org/
.. _`dot`: http://www.graphviz.org/content/dot-language
.. _`geoff`: http://www.neo4j.org/develop/python/geoff



::

    discoursegraphs -t syntax/maz-13915.xml -r rst/maz-13915.rs3 -c connectors/maz-13915.xml -a anaphora/tosik/das/maz-13915.txt -o dot
    dot -Tpdf doc.dot > discoursegraph.pdf # generates a PDF from the dot file

If you're interested in working with just one of those layers, you'll
have to call the code directly::

    import discoursegraphs as dg
    tiger_docgraph = dg.read_tiger('syntax/doc.xml')
    rst_docgraph = dg.read_rs3('rst/doc.rs3')
    expletives_docgraph = dg.read_anaphoricity('expletives/doc.txt')

All the document graphs generated in this example are derived from the
`networkx.MultiDiGraph`_ class, so you should be able to use all of its
methods.

.. _`networkx.MultiDiGraph`: http://networkx.lanl.gov/reference/classes.multidigraph.html


Documentation
-------------

Source code documentation is available
`here <https://pythonhosted.org/pypolibox/>`_, but you can always get an
up-to-date local copy using `Sphinx`_.

You can generate an HTML or PDF version by running these commands in
the ``docs`` directory::

    make latexpdf

to produce a PDF (``docs/_build/latex/discoursegraphs.pdf``) and ::

    make html

to produce a set of HTML files (``docs/_build/html/index.html``).

.. _`Sphinx`: http://sphinx-doc.org/


Requirements
------------

- `enum <https://pypi.python.org/pypi/enum34>`_
- `lxml <http://lxml.de/>`_
- `networkx <http://networkx.github.io/>`_

If you'd like to visualize your graphs, you will also need:

- `graphviz <http://graphviz.org/>`_
- `pygraphviz <http://pygraphviz.github.io/>`_


License
-------

3-Clause BSD.

Author
------
Arne Neumann


People who downloaded this also like
------------------------------------

- `SaltNPepper`_: a converter framework for various linguistic data formats
- `educe`_: a library for handling discourse-annotated corpora (SDRT, RST and PDTB)

.. _`SaltNPepper`: https://korpling.german.hu-berlin.de/p/projects/saltnpepper/wiki/
.. _`educe`: https://github.com/kowey/educe
