# Use the official python 3.6 running on debian
FROM python:3.6

# Getting rid of debconf messages
ARG DEBIAN_FRONTEND=noninteractive

ARG USERNAME=cruzroja
ARG PASSWORD=password
ARG DATABASE=ambulances

ARG SECRET_KEY=CH4NG3M3!
ARG HOSTNAME=" 'cruzroja.ucsd.edu', 'localhost', '127.0.0.1' "

ARG MQTT_USERNAME=admin
ARG MQTT_PASSWORD=cruzrojaadmin
ARG MQTT_EMAIL=webmaster@cruzroja.ucsd.edu
ARG MQTT_CLIENTID=django

# Set working directory
WORKDIR /app

# Add code to the container
ADD ./eng100l /app/

# Install dependencies
RUN apt-get update -y
RUN apt-get install -y apt-utils git
RUN apt-get install -y postgresql postgresql-contrib
RUN apt-get install -y postgis
RUN apt-get install -y gdal-bin libgdal-dev python3-gdal
RUN apt-get install -y openssl cmake

RUN apt-get install -y vim sudo

# Install python requirements
RUN pip install -r requirements.txt

# Build from source code
WORKDIR /src

# Download source code for libwebsockets
# THIS MIGHT NOT BE NECESSARY IN THE FUTURE!
# CURRENT VERSION OF LIBWEBSOCKET GENERATES
# ERROR IN MOSQUITTO-AUTH-PLUG
RUN git clone https://github.com/warmcat/libwebsockets

# Download source code for mosquitto
RUN git clone https://github.com/eclipse/mosquitto

# Download source code for mosquitto-auth-plug
RUN git clone https://github.com/jpmens/mosquitto-auth-plug

# Build libwebsockets
WORKDIR /src/libwebsockets/build
RUN cmake ..
RUN make install

# Configure and build mosquitto
WORKDIR /src/mosquitto
RUN cp config.mk config.mk.in
RUN sed -e 's/WITH_SRV:=yes/WITH_SRV:=no/' \
        -e 's/WITH_WEBSOCKETS:=no/WITH_WEBSOCKETS:=yes/' \
	-e 's/WITH_DOCS:=yes/WITH_DOCS:=no/' \
	config.mk.in > config.mk
RUN make binary install 

# Configure and build mosquitto-auth-plug
WORKDIR /src/mosquitto-auth-plug
RUN sed -e 's/BACKEND_MYSQL ?= yes/BACKEND_MYSQL ?= no/' \
        -e 's/BACKEND_POSTGRES ?= no/BACKEND_POSTGRES ?= yes/' \
	-e 's/BACKEND_HTTP ?= no/BACKEND_HTTP ?= yes/' \
	-e 's,MOSQUITTO_SRC =,MOSQUITTO_SRC =/src/mosquitto,' \
	-e 's,OPENSSLDIR = /usr,OPENSSLDIR = /usr/bin,' \
	config.mk.in > config.mk
RUN make; cp auth-plug.so /usr/local/lib

# Run ldconfig
RUN ldconfig

# Setup Postgres
WORKDIR /app
COPY docker/postgresql/init.psql init.psql
RUN sed -i'' \
        -e 's/\[username\]/'"$USERNAME"'/g' \
        -e 's/\[password\]/'"$PASSWORD"'/g' \
        -e 's/\[database\]/'"$DATABASE"'/g' \
	init.psql
USER postgres
RUN /etc/init.d/postgresql start &&\
    psql -f init.psql
USER root
RUN rm init.psql

# Setup Django
WORKDIR /app
COPY docker/settings.py eng100l/settings.py
RUN sed -i'' \
        -e 's/\[username\]/'"$USERNAME"'/g' \
        -e 's/\[password\]/'"$PASSWORD"'/g' \
        -e 's/\[database\]/'"$DATABASE"'/g' \
        -e 's/\[secret-key\]/'"$SECRET_KEY"'/g' \
        -e 's/\[hostname\]/'"$HOSTNAME"'/g' \
        -e 's/\[mqtt-password\]/'"$MQTT_PASSWORD"'/g' \
        -e 's/\[mqtt-username\]/'"$MQTT_USERNAME"'/g' \
        -e 's/\[mqtt-email\]/'"$MQTT_EMAIL"'/g' \
        -e 's/\[mqtt-clientid\]/'"$MQTT_CLIENTID"'/g' \
	eng100l/settings.py
RUN /etc/init.d/postgresql start &&\
    python manage.py makemigrations &&\
    python manage.py makemigrations ambulances &&\
    python manage.py migrate

# Install certificates
COPY docker/certificates/example-com.ca.crt /etc/certificates/example.com/example-com.ca.crt
COPY docker/certificates/example-com.srv.crt /etc/certificates/example.com/example-com.srv.crt
COPY docker/certificates/example-com.srv.key /etc/certificates/example.com/example-com.srv.key

# Setup mosquitto
RUN useradd -M mosquitto
RUN usermod -L mosquitto
COPY docker/mosquitto/mosquitto.conf /etc/mosquitto/mosquitto.conf
COPY docker/mosquitto/conf.d /etc/mosquitto/conf.d
COPY docker/init.d/mosquitto /etc/init.d/mosquitto
RUN chmod +x /etc/init.d/mosquitto
RUN update-rc.d mosquitto defaults
RUN mkdir /var/log/mosquitto
RUN chown -R mosquitto:mosquitto /var/log/mosquitto
RUN mkdir /var/lib/mosquitto
RUN chown -R mosquitto:mosquitto /var/lib/mosquitto

# Expose the mosquitto posts
EXPOSE 1883
EXPOSE 8883
EXPOSE 8884

EXPOSE 8000

# Go back to home
WORKDIR /app

# Configure application
COPY docs/db.json docker/db.json
RUN service postgresql start &&\
    service mosquitto start &&\
    nohup bash -c "python manage.py runserver 2>&1 &" &&\
    python manage.py flush --no-input &&\
    python manage.py loaddata docker/db.json

# Add VOLUMEs to allow backup of config, logs and databases
VOLUME ["/etc/postgresql", "/var/log/postgresql", "/var/lib/postgresql", \
        "/etc/mosquitto", "/var/log/mosquitto", "/var/lib/mosquitto" ]

CMD service postgresql start &&\
    service mosquitto start &&\
    python manage.py runserver 0.0.0.0:8000
