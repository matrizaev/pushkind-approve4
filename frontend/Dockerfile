FROM python:3.11-slim

ENV FLASK_APP run.py

RUN apt-get update

RUN apt-get -y install default-libmysqlclient-dev gcc

RUN useradd -m pushkind
WORKDIR /home/pushkind
USER pushkind
ENV PATH="$PATH:/home/pushkind/.local/bin"

RUN python -m pip install --upgrade pip
RUN python -m pip install build wheel setuptools poetry

COPY --chown=pushkind:pushkind poetry.toml ./
COPY --chown=pushkind:pushkind pyproject.toml ./
RUN poetry install

COPY --chown=pushkind:pushkind app app
COPY --chown=pushkind:pushkind run.py config.py boot.sh consumer.py ./
RUN chmod +x boot.sh

CMD ["./boot.sh"]

EXPOSE 5000
