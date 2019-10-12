#!/bin/bash

set -e
COMMAND=$1

# Initialized?
if [ "$COMMAND" = 'init' ]; then
    rm /etc/emstrack/emstrack.initialized
fi

if docker-entrypoint-init.sh; then
    echo "> Initialization complete"
fi

# Run commands
if [ "$COMMAND" = 'basic' ] || [ "$COMMAND" = 'all' ];
then

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
    #touch /home/worker/app/reload
    #nohup bash -c "uwsgi --touch-reload=/home/worker/app/reload --http :8000 --module emstrack.wsgi > uwsgi.log 2>&1 &"
    python manage.py runserver 0.0.0.0:8000

elif [ "$COMMAND" = 'test' ];
then

    echo "> Running tests..."
    DJANGO_LOG_LEVEL=DEBUG python manage.py test --verbosity=2

else

    echo "> No services started" 
    echo "> Running '$@'"

    exec "$@"

fi
