#!/bin/sh
alembic upgrade head
gunicorn main:app --worker-class uvicorn.workers.UvicornWorker --workers 4 --bind 0.0.0.0:5000