FROM jupyter/base-notebook:latest

LABEL authors="Ethan Green <egreen4@unca.edu>, Matthew Dippel <mdip226@gmail.com>"
USER root
ENV VIRTUAL_ENV=/opt/venv
# ENV CHOWN_EXTRA=$VIRTUAL_ENV
# ENV CHOWN_EXTRA_OPTS="-R"
# set up virtual environment inside container
RUN python3 -m venv $VIRTUAL_ENV
# activate the venv
ENV PYTHONPATH="$VIRTUAL_ENV:$PYTHONPATH"
ENV PATH="$VIRTUAL_ENV:$PATH"
# make the venv a volume
VOLUME [ "/opt/venv" ]
WORKDIR /usr/src/app
USER ${NB_UID}
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . /usr/src/app