#!/bin/bash

sudo chmod -R 777 postgres_data/
uvicorn tesi.main:app --reload --port 7000