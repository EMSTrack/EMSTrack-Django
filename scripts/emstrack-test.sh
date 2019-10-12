#!/bin/bash

echo "> Starting test..."

echo "> Running basic tests..."
DJANGO_LOG_LEVEL=DEBUG python manage.py test --verbosity=2 ambulance emstrack equipment hospital login

echo "> Running mqtt tests..."
DJANGO_LOG_LEVEL=DEBUG python manage.py test --verbosity=2 mqtt
