FROM python:3.8.10-buster

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

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . /usr/src/app

ARG FLASK_ENV="production"
ENV FLASK_ENV="${FLASK_ENV}" \
    PYTHONUNBUFFERED="true"

EXPOSE 29681

CMD [ "python", "startup.py", "--host", "0.0.0.0"]