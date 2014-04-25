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
