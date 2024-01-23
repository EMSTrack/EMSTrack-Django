#!/bin/bash

INIT_FILE=/etc/emstrack/emstrack.initialized
if [ -f $INIT_FILE ]; then
    echo "> Container is already initialized"

    echo "> Rebuild MQTT password files"
    python manage.py mqttpwfile --encode_salt
    cp pwfile /mosquitto/data/passwd
    cp aclfile /mosquitto/data/acl
    cp pwfile /mosquitto-test/data/passwd
    cp aclfile /mosquitto-test/data/acl
    chown -R 1883:1883 /mosquitto/data
    chown -R 1883:1883 /mosquitto-test/data

    echo "> Creating webpackage bundles"
    webpack --config webpack/map-config.js
    webpack --config webpack/ambulance-config.js
    webpack --config webpack/point-widget-config.js
    webpack --config webpack/call-config.js
    webpack --config webpack/base-config.js
    webpack --config webpack/report-vehicle-mileage-config.js
    webpack --config webpack/report-vehicle-activity-config.js
    webpack --config webpack/video-config.js
    webpack --config webpack/equipment-config.js

    echo "> Recovering static files"
    python manage.py collectstatic --no-input
    python manage.py compilemessages

    # exit
    exit 1
fi

echo "> Initializing container..."

# Wait for postgres
timer="5"
until pg_isready -d postgres://postgres:$DB_PASSWORD@$DB_HOST; do
    >&2 echo "Postgres is unavailable - sleeping for $timer seconds"
    sleep $timer
done

# Setup Postgres
sed -i'' \
    -e 's/\[username\]/'"$DB_USERNAME"'/g' \
    -e 's/\[password\]/'"$DB_PASSWORD"'/g' \
    -e 's/\[database\]/'"$DB_DATABASE"'/g' \
    init/init.psql
psql -f init/init.psql -d postgres://postgres:$DB_PASSWORD@$DB_HOST

# Setup Django
# python manage.py makemigrations ambulance login hospital equipment
python manage.py migrate

# Has backup?
if [ -e "/etc/emstrack/fixtures/backup.json" ] ;
then
    echo "Fixtures found"
    python manage.py loaddata /etc/emstrack/fixtures/backup.json
else
    echo "Fixtures not found, bootstraping"
    python manage.py bootstrap
fi

# password file
python manage.py mqttpwfile
cp pwfile /mosquitto/data/passwd
cp pwfile /mosquitto-test/data/passwd
chown -R 1883:1883 /mosquitto/data
chown -R 1883:1883 /mosquitto-test/data

# deploy webpack
webpack --config webpack/map-config.js
webpack --config webpack/ambulance-config.js
webpack --config webpack/point-widget-config.js
webpack --config webpack/call-config.js
webpack --config webpack/base-config.js
webpack --config webpack/report-vehicle-mileage-config.js
webpack --config webpack/report-vehicle-activity-config.js
webpack --config webpack/video-config.js
webpack --config webpack/equipment-config.js

python manage.py collectstatic --no-input
python manage.py compilemessages

# Mark as initialized
DATE=$(date +%Y-%m-%d)
cat << EOF > /etc/emstrack/emstrack.initialized
# Container initialized on $DATE
PORT=$PORT
SSL_PORT=$SSL_PORT
HOSTNAME=$HOSTNAME

DB_USERNAME=$DB_USERNAME
DB_PASSWORD=$DB_PASSWORD
DB_DATABASE=$DB_DATABASE
DB_HOST=$DB_HOST

DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY
DJANGO_HOSTNAMES=$DJANGO_HOSTNAMES
DJANGO_DEBUG=$DJANGO_DEBUG

MQTT_USERNAME=$MQTT_USERNAME
MQTT_PASSWORD=$MQTT_PASSWORD
MQTT_EMAIL=$MQTT_EMAIL
MQTT_CLIENTID=$MQTT_CLIENTID

MQTT_BROKER_HTTP_IP=$MQTT_BROKER_HTTP_IP
MQTT_BROKER_HTTP_PORT=$MQTT_BROKER_HTTP_PORT
MQTT_BROKER_HTTP_WITH_TLS=$MQTT_BROKER_HTTP_WITH_TLS
MQTT_BROKER_HTTP_HOSTNAME=$MQTT_BROKER_HTTP_HOSTNAME

MQTT_BROKER_HOST=$MQTT_BROKER_HOST
MQTT_BROKER_PORT=$MQTT_BROKER_PORT
MQTT_BROKER_SSL_HOST=$MQTT_BROKER_SSL_HOST
MQTT_BROKER_SSL_PORT=$MQTT_BROKER_SSL_PORT
MQTT_BROKER_WEBSOCKETS_HOST=$MQTT_BROKER_WEBSOCKETS_HOST
MQTT_BROKER_WEBSOCKETS_PORT=$MQTT_BROKER_WEBSOCKETS_PORT
MQTT_BROKER_TEST_HOST=$MQTT_BROKER_TEST_HOST

MAP_PROVIDER=$MAP_PROVIDER
MAP_PROVIDER_TOKEN=$MAP_PROVIDER_TOKEN
EOF

exit 0
