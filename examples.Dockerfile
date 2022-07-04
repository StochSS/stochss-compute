# FROM jupyter/minimal-notebook
# # Start from a core stack version
# # Install from requirements.txt file
# COPY --chown=${NB_UID}:${NB_GID} requirements.txt /tmp/
# RUN pip install --quiet --no-cache-dir --requirement /tmp/requirements.txt && \
#     fix-permissions "${CONDA_DIR}" && \
#     fix-permissions "/home/${NB_USER}"
# COPY . .
FROM python:3.8.10-buster

LABEL authors="Ethan Green <egreen4@unca.edu>, Matthew Dippel <mdip226@gmail.com>"

# ENV VIRTUAL_ENV=/opt/venv
# # set up virtual environment inside container
# RUN python3 -m venv $VIRTUAL_ENV
# # activate the venv
# ENV PYTHONPATH="$VIRTUAL_ENV:$PYTHONPATH"
# ENV PATH="$VIRTUAL_ENV:$PATH"
# # make the venv a volume
# VOLUME [ "/opt/venv" ]
# WORKDIR /usr/src/app
RUN groupadd -r user && useradd -r -g user sssc
WORKDIR /home/sssc
COPY requirements.txt .
RUN pip install -r requirements.txt
USER sssc

COPY . /usr/src/app
RUN python startup.py --host 0.0.0.0 &
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=9999"]