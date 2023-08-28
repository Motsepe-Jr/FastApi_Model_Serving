FROM python:3.9-slim

RUN apt-get update && \
    apt-get install -y \
    build-essential \
    python3-dev \
    python3-setuptools \
    git \
    git-crypt \
    unzip \
    chromium-driver \
    gcc \
    make

RUN python -m pip install cassandra-driver

RUN apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*


COPY ./app ./app/app
COPY ./requirements.txt ./app/requirements.txt

WORKDIR /app

RUN python3 -m pip install --upgrade pip
RUN python3 -m venv /opt/venv && /opt/venv/bin/python -m pip install -r requirements.txt


