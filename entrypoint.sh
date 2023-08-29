#!/bin/bash

RUN_PORT=${PORT:-8000}

/opt/venv/bin/gunicorn --worker-tmp-dir /dev/shm -k uvicorn.workers.UvicornWorker --bind "0.0.0.0:${RUN_PORT}" app.main:app
