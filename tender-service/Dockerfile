FROM python:3.11-slim

ENV FLASK_APP run.py

RUN apt-get update

RUN apt-get -y install default-libmysqlclient-dev gcc libicu-dev libsqlite3-dev pkg-config

RUN useradd -m pushkind
WORKDIR /home/pushkind
USER pushkind
ENV PATH="$PATH:/home/pushkind/.local/bin"

COPY --chown=pushkind:pushkind icu.c ./
RUN gcc -shared icu.c -g -o libsqliteicu.so -fPIC `pkg-config --libs --cflags icu-uc icu-io`

RUN python -m pip install --upgrade pip
RUN python -m pip install build wheel setuptools poetry

COPY --chown=pushkind:pushkind poetry.toml ./
COPY --chown=pushkind:pushkind pyproject.toml ./
RUN poetry install

COPY --chown=pushkind:pushkind app app
COPY --chown=pushkind:pushkind tests tests
COPY --chown=pushkind:pushkind run.py config.py consumer.py boot.sh test.sh deploy.sh ./
RUN chmod +x boot.sh && chmod +x test.sh && chmod +x deploy.sh
RUN mkdir db

CMD ["./boot.sh"]
