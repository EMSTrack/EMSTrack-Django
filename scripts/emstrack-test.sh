#!/bin/bash

echo "> Starting test..."

# stop mqttclient
supervisorctl stop mqttclient

# run tests
python manage.py test $*

# start mqttclient
supervisorctl start mqttclient
