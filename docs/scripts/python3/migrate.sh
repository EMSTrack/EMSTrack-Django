#!/bin/bash

python3 ../../../eng100l/manage.py makemigrations
python3 ../../../eng100l/manage.py makemigrations ambulances
python3 ../../../eng100l/manage.py migrate
python3 ../../../eng100l/manage.py createsuperuser
