#!/usr/bin/env bash

cd  `dirname $0`

export FLASK_APP=app.py

gunicorn --workers 10 --timeout 100 --bind 0.0.0.0:35556 app:app
