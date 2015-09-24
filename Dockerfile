# Dockerfile to build a discoursegraphs container image

FROM ipython/notebook

MAINTAINER Arne Neumann <discoursegraphs.programming@arne.cl>

RUN apt-get update
RUN apt-get install -y python-dev python-pip git graphviz-dev libxml2-dev libxslt-dev

RUN easy_install -U setuptools

WORKDIR /opt/
RUN git clone https://github.com/arne-cl/discoursegraphs.git
RUN git clone https://github.com/arne-cl/neonx.git

WORKDIR /opt/neonx/
RUN python setup.py install

WORKDIR /opt/discoursegraphs/
RUN python setup.py install

