FROM jupyter/minimal-notebook

LABEL authors="Ethan Green <egreen4@unca.edu>, Matthew Dippel <mdip226@gmail.com>"

USER root

RUN apt-get update && apt-get install -y g++ make

USER jovyan

RUN pip install --no-cache-dir bokeh

COPY --chown=jovyan:users stochss_compute stochss_compute

COPY --chown=jovyan:users examples examples

COPY --chown=jovyan:users *.txt *.py *.md ./

RUN pip install .

WORKDIR /home/jovyan/examples