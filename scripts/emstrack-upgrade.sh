#!/bin/bash

echo "> Starting upgrade..."

# stop services
echo "> Stoping services"
emstrack-down

# git pull to update
echo "> Pulling changes"
git pull

# run updates
echo "> Upgrading database"
python manage.py makemigrations
python manage.py migrate

echo "> Upgrading static files"
./node_modules/.bin/webpack --config webpack-map-config.js
./node_modules/.bin/webpack --config webpack-ambulance-config.js
./node_modules/.bin/webpack --config webpack-point-widget-config.js
./node_modules/.bin/webpack --config webpack-call-config.js
./node_modules/.bin/webpack --config webpack-base-config.js
python manage.py collectstatic --no-input
python manage.py compilemessages

# start services
echo "> Restarting services"
emstrack-up all

echo "> Upgrade complete"
