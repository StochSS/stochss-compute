FROM jupyter/minimal-notebook
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV CHOWN_HOME=yes