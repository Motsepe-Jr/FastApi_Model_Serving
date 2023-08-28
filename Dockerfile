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

COPY .env /app/.env
COPY ./app /app/app
COPY ./requirements.txt /app/requirements.txt
COPY ./entrypoint.sh /app/entrypoint.sh

WORKDIR /app

RUN python3 -m pip install --upgrade pip
RUN python3 -m venv /opt/venv && /opt/venv/bin/python -m pip install -r requirements.txt

CMD ["entrypoint.sh"]
