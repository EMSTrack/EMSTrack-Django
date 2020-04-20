#!/bin/bash

echo "> Starting test..."

echo "> Running basic tests..."
SMS_PROVIDER= DJANGO_ENABLE_MQTT_PUBLISH=False DJANGO_LOG_LEVEL=DEBUG python manage.py test --verbosity=2 ambulance emstrack equipment hospital login

echo "> Running mqtt tests..."
SMS_PROVIDER= DJANGO_LOG_LEVEL=DEBUG python manage.py test --verbosity=2 mqtt
