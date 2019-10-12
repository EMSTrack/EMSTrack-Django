#!/bin/bash

COMMAND=$1

# Initialized?
if [ "$COMMAND" = 'init' ]; then
    rm /etc/emstrack/emstrack.initialized
fi

if docker-entrypoint-init.sh; then
    echo "> Initialization complete"
fi

# Run commands
if [ "$COMMAND" = 'basic' ] || [ "$COMMAND" = 'all' ] || [ "$COMMAND" = 'test' ]; then

    echo "> Starting basic services"
    
    echo "> Waiting for postgres"
    timer="5"
    until pg_isready -U postgres -h $DB_HOST --quiet; do
        >&2 echo "Postgres is unavailable - sleeping for $timer seconds"
        sleep $timer
    done

    if [ "$COMMAND" = 'all' ]; then

        echo "> Starting mqttclient"
	    python -u /app/manage.py mqttclient > /etc/emstrack/log/mqttclient.log 2>&1 &

    fi

    echo "> Starting uWSGI"
    #touch /home/worker/app/reload
    #nohup bash -c "uwsgi --touch-reload=/home/worker/app/reload --http :8000 --module emstrack.wsgi > uwsgi.log 2>&1 &"
    python manage.py runserver 0.0.0.0:8000

else

    echo "> No services started" 
    echo "> Running '$@'"

    exec "$@"

fi
