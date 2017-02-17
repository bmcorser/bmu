FROM python:2.7

ADD . /src
WORKDIR /src
RUN ./install.sh
