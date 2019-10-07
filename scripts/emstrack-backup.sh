#!/bin/bash

echo "> ATTENTION: stop services before backing up database to preserve integrity"

echo "> Backing up database"
mkdir -p /etc/emstrack/fixtures
# python manage.py dumpdata --natural > /etc/emstrack/fixtures/backup.json
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission > /etc/emstrack/fixtures/backup.json

echo "> Done backing up database"
