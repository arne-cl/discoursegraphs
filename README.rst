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

So far, the following formats can be imported and merged:

* `TigerXML`_ (a format for representing tree-like syntax graphs with
  secondary edges)
* RS3 (a format used by `RSTTool`_ to
  annotate documents with Rhetorical Structure Theory)
* an ad-hoc plain text format for annotating expletives (you're probably not
  interested in)

.. _`TigerXML`: http://www.ims.uni-stuttgart.de/forschung/ressourcen/werkzeuge/TIGERSearch/doc/html/TigerXML.html
.. _`RSTTool`: http://www.wagsoft.com/RSTTool/


Installation
------------

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

Right now, there's only a primitive command line interface that will
merge the syntax, RST and expletive annotation layers into one
graph and generates a dot file from it.

::

    discoursegraphs syntax/doc.xml rst/doc.rs3 expletives/doc.txt doc.dot
    dot -Tpdf doc.dot > discoursegraph.pdf # generates a PDF from the dot file

If you're interested in working with just one of those layers, you'll
have to call the code directly::

    from discoursegraphs import readwrite
    tiger_docgraph = readwrite.TigerDocumentGraph('syntax/doc.xml')
    rst_docgraph = readwrite.RSTGraph('rst/doc.rs3')
    expletives_docgraph = readwrite.AnaphoraDocumentGraph('expletives/doc.txt')

All the document graphs generated in this example are derived from the
`networkx.MultiDiGraph`_ class, so you should be able to use all of its
methods.

.. _`networkx.MultiDiGraph`: http://networkx.lanl.gov/reference/classes.multidigraph.html



Requirements
------------

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

- `SaltNPepper`_ (a converter framework for various linguistic data formats)

.. _`SaltNPepper`: https://korpling.german.hu-berlin.de/p/projects/saltnpepper/wiki/
