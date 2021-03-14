.. This is your project NEWS file which will contain the release notes.
.. Example: http://www.python.org/download/releases/2.6/NEWS.txt
.. The content of this file, along with README.rst, will appear in your
.. project's PyPI page.

News
====

0.4.14 (2021-03-14)
-------------------

*Release date: 14-March-2021*

* minor: renamed fixture for clarity

0.4.13 (2021-03-12)
-------------------

*Release date: 12-March-2021*

* fix for parsing DPLP trees with only one EDU

0.4.12 (2021-02-22)
-------------------

*Release date: 22-February-2021*

* added support for StageDP RST parser

0.4.11 (2020-12-10)
-------------------

*Release date: 10-December-2020*

* fix rs3 parser for files produced by isanlp_rst

0.4.10 (2020-06-03)
-------------------

*Release date: 06-June-2020*

* added standard RST relations to every rs3 file

0.4.9 (2020-05-10)
------------------

*Release date: 10-May-2020*

* added option to write_svgtree() to return SVG image as a string

0.4.8 (2020-04-25)
------------------

*Release date: 25-April-2020*

* fixed dependencies in 0.4.7

0.4.7 (2020-04-23)
------------------

*Release date: 23-April-2020*

* fixed dependencies in 0.4.6

0.4.6 (2020-04-21)
------------------

*Release date: 21-April-2020*

* added write_svgtree (create SVG files from nltk trees)

0.4.5 (2019-05-16)
------------------

*Release date: 12-May-2019*

* fixed rstlatex nested tree generation

0.4.4 (2019-05-11)
------------------

*Release date: 11-May-2019*

* fixed rstlatex formatting / inheritance bug

0.4.3 (2019-05-10)
------------------

*Release date: 10-May-2019*

* fixed rstlatex file export

0.4.2 (2019-05-10)
------------------

*Release date: 10-May-2019*

* fixed dependency in setup.py

0.4.1 (2019-04-27)
------------------

*Release date: 27-April-2019*

* added exporter for RST trees in Latex

0.4.0 (2019-04-25)
------------------

*Release date: 25-April-2019*

* almost three years of additions/fixes (mostly RST-related importers/exporters,
  e.g. URML, dis, rs3, HILDA, DPLP, Heilman and Sagae (2015))


0.3.2 (2016-05-30)
------------------

*Release date: 30-May-2016*

* second attempt to fix the distribution of the data directory with the package
* added exporter for `FREQT`_, which extracts frequent embedded subtrees

.. _`FREQT`: http://chasen.org/~taku/software/freqt/

0.3.1 (2016-05-07)
------------------

*Release date: 7-May-2016*

* attempt to fix the distribution of the data directory with the package
* document graphs can be converted into PTB-style strings (readwrite/tree.py)
* node/edge collections are now ordered (OrderedDict)

0.3.0 (2016-04-30)
------------------

*Release date: 30-April-2016*

* almost two years and countless commits later, finally a new official release
* added lots of importers and exporters and simplified the API
* added 80+ tests (py.test), continuous integration (Travis) and docker support

0.1.2 (2014-05-13)
------------------

*Release date: 13-May-2014*

* added basic `Geoff`_ and `Neo4j`_ exporter (not yet available via the command
  line)
* added sphinx-based documentation

.. _`Geoff`: http://www.neo4j.org/develop/python/geoff
.. _`Neo4j`: http://www.neo4j.org/

0.1.1 (2014-04-25)
------------------

*Release date: 25-Apr-2014*

* small improvements
* added usage examples to readme
* discoursegraphs script now uses the commandline interface of the merging module

0.1.0 (2014-04-24)
------------------

*Release date: 24-Apr-2014*

* first public release
* imports: RS3, TigerXML and an ad-hoc format for expletive annotation
* merge these formats/files into a single multidigraph
* generates simple dot/graphviz-based visualization

