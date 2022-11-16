FROM python:slim

ENV FLASK_APP run.py

RUN apt-get update

RUN apt-get -y install default-libmysqlclient-dev gcc

RUN useradd -m pushkind
WORKDIR /home/pushkind
USER pushkind

RUN python3 -m venv venv
RUN venv/bin/python3 -m pip install --upgrade pip
RUN venv/bin/python3 -m pip install build wheel setuptools

COPY --chown=pushkind:pushkind requirements.txt ./
RUN venv/bin/pip install -r requirements.txt

COPY --chown=pushkind:pushkind app app
COPY --chown=pushkind:pushkind tests tests
COPY --chown=pushkind:pushkind run.py config.py consumer.py boot.sh test.sh deploy.sh ./
RUN chmod +x boot.sh && chmod +x test.sh && chmod +x deploy.sh

CMD ["./boot.sh"]
