#!/bin/bash

TEST="./mqtt/tests/test_panic.py"

echo "> Starting test..."
SMS_PROVIDER= DJANGO_LOG_LEVEL=DEBUG python manage.py test --verbosity=2 $TEST