#!/bin/bash

pid=0

# Cleanup
cleanup() {

    echo "Container stopped, cleaning up..."

    # stop supervisor
    service supervisor stop

    # stop postgres
    service postgresql stop

    echo "Exiting..."

    if [ $pid -ne 0 ]; then
	kill -SIGTERM "$pid"
	wait "$pid"
    fi
    exit 143; # 128 + 15 -- SIGTERM

}

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
    
    # Trap SIGTERM
    trap 'kill ${!}; cleanup' SIGTERM

    echo "> Waiting for postgres"
    timer="5"
    until pg_isready -U postgres -h db --quiet; do
	>&2 echo "Postgres is unavailable - sleeping for $timer seconds"
	sleep $timer
    done

    echo "> Starting uWSGI"
    nohup bash -c "uwsgi --touch-reload=/home/worker/app/reload --http :8000 --module emstrack.wsgi > uwsgi.log 2>&1 &"

    echo "> Basic services up"

    if [ "$COMMAND" = 'all' ]; then

	echo "> Starting all services"
	
	echo "> Starting mqttclient"
	service supervisor start

	echo "> All services up"

    fi

    pid="$!"
    
    # Wait forever
    while true
    do
	tail -f /dev/null & wait ${!}
    done
    
    # Call cleanup
    cleanup

else

    echo "> No services started" 
    echo "> Running '$@'"

    exec "$@"

fi
