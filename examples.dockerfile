FROM jupyter/minimal-notebook

LABEL authors="Ethan Green <egreen4@unca.edu>, Matthew Dippel <mdip226@gmail.com>"

USER root

RUN apt-get update && apt-get install -y g++ make

USER jovyan

COPY --chown=jovyan:users requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir bokeh

COPY --chown=jovyan:users stochss_compute stochss_compute

COPY --chown=jovyan:users examples examples

COPY --chown=jovyan:users *.py *.md ./

WORKDIR /home/jovyan/examples