# Dockerfile to build a discoursegraphs container image
FROM ubuntu:16.04

MAINTAINER Arne Neumann <discoursegraphs.programming@arne.cl>

RUN apt-get update && \
    apt-get install -y python-dev python-pip git graphviz graphviz-dev \
        libxml2-dev libxslt-dev && \
    easy_install -U setuptools && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/discoursegraphs/
ADD docs docs/
ADD src src/
ADD tests tests/
ADD LICENSE Makefile NEWS.rst README.rst requirements.txt setup.py ./

# on current Ubuntu systems you will need to install pygraphviz manually,
# cf. http://stackoverflow.com/questions/32885486/pygraphviz-importerror-undefined-symbol-agundirected
RUN pip2 install pygraphviz==1.3.1 \
    --install-option="--include-path=/usr/include/graphviz" \
    --install-option="--library-path=/usr/lib/graphviz/" && \
    pip2 install -U pip && \
    pip2 install -r requirements.txt
