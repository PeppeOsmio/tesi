#!/bin/bash

poetry run alembic upgrade head

exec poetry run uvicorn tesi.main:app --host 0.0.0.0 --port 8000