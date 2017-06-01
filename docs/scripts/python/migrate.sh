#!/bin/bash

python ../../../eng100l/manage.py makemigrations
python ../../../eng100l/manage.py makemigrations ambulances
python ../../../eng100l/manage.py migrate
python ../../../eng100l/manage.py createsuperuser
