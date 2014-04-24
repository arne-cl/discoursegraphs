# This is your "setup.py" file.
# See the following sites for general guide to Python packaging:
#   * `The Hitchhiker's Guide to Packaging <http://guide.python-distribute.org/>`_
#   * `Python Project Howto <http://infinitemonkeycorps.net/docs/pph/>`_

from setuptools import setup, find_packages
import sys, os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
NEWS = open(os.path.join(here, 'NEWS.rst')).read()


version = '0.1.0'

install_requires = [
    # List your project dependencies here.
    # For more details, see:
    # http://packages.python.org/distribute/setuptools.html#declaring-dependencies
    "lxml", "networkx", "pygraphviz"
]


setup(name='discoursegraphs',
    version=version,
    description="graph-based processing of multi-level annotated corpora",
    long_description=README + '\n\n' + NEWS,
    # Get classifiers from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    # classifiers=[c.strip() for c in """
    #     Development Status :: 4 - Beta
    #     License :: OSI Approved :: MIT License
    #     Operating System :: OS Independent
    #     Programming Language :: Python :: 2.6
    #     Programming Language :: Python :: 2.7
    #     Programming Language :: Python :: 3
    #     Topic :: Software Development :: Libraries :: Python Modules
    #     """.split('\n') if c.strip()],
    # ],
    keywords='corpus linguistics nlp graph networkx annotation',
    author='Arne Neumann',
    author_email='discoursegraphs.programming@arne.cl',
    url='https://github.com/arne-cl/discoursegraphs',
    license='3-Clause BSD License',
    packages=find_packages("src"),
    package_dir = {'': "src"},include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    entry_points={
        'console_scripts':
            ['discoursegraphs=discoursegraphs:main']
    }
)
