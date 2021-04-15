FROM python:3.9-buster

LABEL maintainer="Ethan Green <egreen4@unca.edu>"

COPY . /usr/src/app
WORKDIR /usr/src/app

RUN pip install --no-cache-dir poetry
RUN poetry install

ARG FLASK_ENV="production"
ENV FLASK_ENV="${FLASK_ENV}" \
    PYTHONUNBUFFERED="true"

EXPOSE 1234

CMD [ "poetry", "run", "stochss-remote"]