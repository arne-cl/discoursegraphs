# Dockerfile to build a discoursegraphs container image

FROM jupyter/notebook

MAINTAINER Arne Neumann <discoursegraphs.programming@arne.cl>

RUN apt-get update
RUN apt-get install -y python-dev python-pip git graphviz-dev libxml2-dev libxslt-dev

RUN easy_install -U setuptools

WORKDIR /opt/discoursegraphs/
ADD data data/
ADD docs docs/
ADD src src/
ADD tests tests/
ADD LICENSE Makefile NEWS.rst README.rst requirements.txt setup.py ./

RUN pip2.7 install -r requirements.txt
