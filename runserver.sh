#!/bin/bash
echo Starting server...
source .venv/bin/activate
gunicorn -c gunicorn.conf.py app:app
