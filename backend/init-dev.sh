#!/bin/sh
alembic upgrade head
uvicorn main:app --reload --host 0.0.0.0 --port 5000