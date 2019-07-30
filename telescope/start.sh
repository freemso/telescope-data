#!/usr/bin/env bash

cd  `dirname $0`

export FLASK_APP=app.py

NEW_RELIC_CONFIG_FILE=newrelic.ini
export NEW_RELIC_CONFIG_FILE
newrelic-admin run-program gunicorn --workers 10 --timeout 100 --bind 0.0.0.0:35556 app:app
