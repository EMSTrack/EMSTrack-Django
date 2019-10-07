#!/bin/bash

echo "> Starting basic services"
    
echo "> Waiting for postgres"
timer="5"
until pg_isready -U postgres -h db --quiet; do
    >&2 echo "Postgres is unavailable - sleeping for $timer seconds"
    sleep $timer
done

echo "> Starting mosquitto"
service mosquitto start
sleep $timer

echo "> Starting uWSGI"
touch /app/reload
nohup bash -c "uwsgi --touch-reload=/app/reload --socket emstrack.sock --module emstrack.wsgi --uid www-data --gid www-data --chmod-socket=664 >/var/log/uwsgi.log 2>&1 &"

echo "> Starting nginx"
service nginx start

echo "> Basic services up"

if [ "$1" = 'all' ]; then

    echo "> Starting all services"
    
    echo "> Starting mqttclient"
    service supervisor start
    supervisorctl start mqttclient
    
    echo "> All services up"
    
fi
