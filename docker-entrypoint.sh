#!/bin/bash

set -e
COMMAND=$1

# Run commands
if [ "$COMMAND" = 'basic' ] || [ "$COMMAND" = 'all' ];
then

    # Initialized?
    if [ "$COMMAND" = 'init' ]; then
        rm /etc/emstrack/emstrack.initialized
    fi

    if docker-entrypoint-init.sh; then
        echo "> Initialization complete"
    fi

    echo "> Starting basic services"
    
    echo "> Waiting for postgres"
    timer="5"
    until pg_isready -U postgres -h $DB_HOST --quiet; do
        >&2 echo "Postgres is unavailable - sleeping for $timer seconds"
        sleep $timer
    done

    if [ "$COMMAND" = 'all' ]; then

        echo "> Starting mqttclient"
	    python manage.py mqttclient > /etc/emstrack/log/mqttclient.log 2>&1 &

    fi

    echo "> Starting uWSGI"
    # nohup bash -c "uwsgi --touch-reload=/home/worker/app/reload --http 0.0.0.0:8000 --module emstrack.wsgi > /etc/emstrack/log/uwsgi.log 2>&1 &"
    # python manage.py runserver 0.0.0.0:8000
    touch /app/reload
    uwsgi --touch-reload=/app/reload --ini uwsgi.ini

else

    echo "> No services started" 
    echo "> Running '$@'"

    exec "$@"

fi
