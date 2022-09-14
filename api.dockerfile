FROM python:3.9.14-buster

LABEL authors="Ethan Green <egreen4@unca.edu>, Matthew Dippel <mdip226@gmail.com>"

# set up virtual environment inside container
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
# activate the venv
ENV PYTHONPATH="$VIRTUAL_ENV:$PYTHONPATH"
ENV PATH="$VIRTUAL_ENV:$PATH"
# make the venv a volume
VOLUME [ "/opt/venv" ]

WORKDIR /usr/src/app

COPY stochss_compute /usr/src/app/stochss_compute
COPY *.txt *.py *.md *.dockerfile *.cfg /usr/src/app/
RUN pip install .

EXPOSE 29681

CMD [ "stochss-compute-cluster"]