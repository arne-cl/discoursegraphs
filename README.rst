DiscourseGraphs
===============

.. image:: http://img.shields.io/pypi/v/discoursegraphs.svg
   :alt: Latest version
   :align: right
   :target: https://pypi.python.org/pypi/discoursegraphs
.. image:: http://img.shields.io/badge/license-BSD-yellow.svg
   :alt: BSD License
   :align: right
   :target: http://opensource.org/licenses/BSD-3-Clause

.. image:: https://travis-ci.org/arne-cl/discoursegraphs.svg?branch=master
   :alt: Build status
   :align: right
   :target: https://travis-ci.org/arne-cl/discoursegraphs
.. image:: https://codecov.io/github/arne-cl/discoursegraphs/coverage.svg?branch=master
   :alt: Test coverage
   :align: right
   :target: https://codecov.io/github/arne-cl/discoursegraphs?branch=master
.. image:: https://www.quantifiedcode.com/api/v1/project/3076854b9ea74bed867f12808d98f437/badge.svg
   :alt: Code Issues
   :align: right
   :target: https://www.quantifiedcode.com/app/project/3076854b9ea74bed867f12808d98f437
.. image:: https://img.shields.io/docker/build/nlpbox/charniak.svg
   :alt: Docker build status
   :align: right
   :target: https://hub.docker.com/r/nlpbox/charniak


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
* `NeGra Export Format`_ (a format used i.a. for the TüBa-D/Z Treebank)
* `Penn Treebank <http://www.cis.upenn.edu/~treebank/>`_ format (an s-expressions/lisp/brackets format for representing syntax trees)
* a number of formats for Rhetorical Structure Theory:

  - RS3 (a format used by `RSTTool`_ to annotate documents with Rhetorical Structure Theory)
  - the .dis "LISP" format used by the RST-DT corpus
  - `URML`_ (a format for underspecified rhetorical structure trees)
  
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
.. _`NeGra Export Format`: http://www.sfs.uni-tuebingen.de/resources/exformat3.ps 
.. _`RSTTool`: http://www.wagsoft.com/RSTTool/
.. _`URML`: http://www.david-reitter.com/compling/urml/index.html
.. _`MMAX2`: http://mmax2.sourceforge.net/
.. _`CoNLL 2009`: http://ufal.mff.cuni.cz/conll2009-st/task-description.html
.. _`CoNLL 2010`: http://web.archive.org/web/20130119013221/http://www.inf.u-szeged.hu/rgai/conll2010st
.. _`Conano`: http://www.ling.uni-potsdam.de/acl-lab/Forsch/pcc/pcc.html

Export formats
--------------

discoursegraphs can export graphs into the following formats /
for the following tools:

* dot format, which is used by the open source graph visualization software `graphviz`_
* geoff format, used by the `neo4j`_ graph database
* `GEXF <http://gexf.net/format/>`_  and `GraphML <http://graphml.graphdrawing.org/>`_
  (common interchange formats for graphs used by various tools such as
  `Gephi <https://gephi.github.io/>`_ and `Cytoscape <http://www.cytoscape.org/>`_)
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

    sudo apt-get install python-dev libxml2-dev libxslt-dev pkg-config graphviz-dev libgraphviz-dev -y
    sudo easy_install -U setuptools
    git clone https://github.com/arne-cl/discoursegraphs.git
    cd discoursegraphs
    sudo python setup.py install


Usage
-----

The command line interface of DiscourseGraphs allows you to
merge syntax, rhetorical structure, connectives and expletives
annotation files into one graph and to  store this graph in one of several
output formats (e.g. the `geoff`_ format used by the `neo4j`_ graph database
or the `dot`_ format used by the graphviz plotting tool).

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

- `lxml <http://lxml.de/>`_
- `networkx <http://networkx.github.io/>`_

If you'd like to visualize your graphs, you will also need:

- `graphviz <http://graphviz.org/>`_
- `pygraphviz <http://pygraphviz.github.io/>`_


License and Citation
--------------------

This software is released under a 3-Clause BSD license. If you use
discoursegraphs in your academic work, please cite the following paper:

Neumann, A. 2015. discoursegraphs: A graph-based merging tool and converter
for multilayer annotated corpora. In *Proceedings of the 20th Nordic Conference
of Computational Linguistics (NODALIDA 2015)*, pp. 309-312.

::

    @inproceedings{neumann2015discoursegraphs,
      title={discoursegraphs: A graph-based merging tool and converter for multilayer annotated corpora},
      author={Neumann, Arne},
      booktitle={Proceedings of the 20th Nordic Conference of Computational Linguistics (NODALIDA 2015)},
      pages={309-312},
      year={2015}
    }

Author
------
Arne Neumann


People who downloaded this also like
------------------------------------

- `SaltNPepper`_: a converter framework for various linguistic data formats
- `educe`_: a library for handling discourse-annotated corpora (SDRT, RST and PDTB)
- `treetools`_: a library for converting treebanks and grammar extraction (supports
  i.a. TigerXML and Negra/Tüba-Export formats)
- `TCFnetworks`_: library for creating graphs from annotated text corpora (based on TCF).

.. _`SaltNPepper`: https://korpling.german.hu-berlin.de/p/projects/saltnpepper/wiki/
.. _`educe`: https://github.com/irit-melodi/educe
.. _`treetools`: https://github.com/wmaier/treetools
.. _`TCFnetworks`: https://github.com/SeNeReKo/TCFnetworks
