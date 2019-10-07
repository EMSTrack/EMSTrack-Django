# Using ubuntu as a base image
FROM ubuntu:18.04

# Getting rid of debconf messages
ARG DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update -y
RUN apt-get install -y apt-utils git

# Install python
RUN apt-get install -y python3-pip python3-dev 

# Install postgres and postgis
RUN apt-get install -y postgresql-client
RUN apt-get install -y gdal-bin libgdal-dev python3-gdal

# Install opensll
RUN apt-get install -y openssl

# Install utilities
RUN apt-get install -y vim sudo less
RUN apt-get install -y uuid-dev

# Make python3 default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1
RUN ln -s /usr/bin/pip3 /usr/bin/pip

# Install supervisor (make sure it runs on python2)
RUN apt-get install -y supervisor
RUN sed -i'' \
        -e 's/bin\/python/bin\/python2/' \
	/usr/bin/supervisord
RUN sed -i'' \
        -e 's/bin\/python/bin\/python2/' \
	/usr/bin/supervisorctl

# Install cron
RUN apt-get install -y cron

# Install gettext
RUN apt-get install -y gettext

# Install mosquitto-clients
RUN apt-get install -y mosquitto-clients

# Install npm
RUN curl -sL https://deb.nodesource.com/setup_10.x -o nodesource_setup.sh
RUN bash nodesource_setup.sh
RUN apt-get install -y nodejs

# Install sudo
RUN apt-get -y install sudo

# upgrade pip
RUN pip install --upgrade pip

# create non-privileged user
RUN useradd -ms /bin/bash worker
RUN adduser worker sudo

# /etc/emstrack
RUN mkdir -p /etc/emstrack/migrations
RUN mkdir -p /etc/emstrack/log/mqttclient
RUN chown -R worker:worker /etc/emstrack

# /etc/mosquitto
RUN mkdir -p /etc/mosquitto
RUN chown -R worker:worker /etc/mosquitto

# Setup mqttclient
COPY supervisor/mqttclient.conf /etc/supervisor/conf.d/mqttclient.conf

# switch to unprivileged worker
USER worker
WORKDIR /home/worker
RUN mkdir app
RUN mkdir src
RUN chown -R worker:worker /home/worker

ENV PATH="/home/worker/.local/bin:${PATH}"

# Install uwsgi
RUN pip install --user uwsgi

# Clone application
ARG BUILD_APP_HOME=/home/worker/app
ENV APP_HOME=$BUILD_APP_HOME

WORKDIR /home/worker/app
COPY --chown=worker:worker . .

# install requirements
RUN pip install --user -r requirements.txt

# link migration directories into persistent volume
RUN mkdir -p /etc/emstrack/migrations
RUN mkdir /etc/emstrack/migrations/ambulance
RUN ln -s /etc/emstrack/migrations/ambulance $APP_HOME/ambulance/migrations
RUN mkdir /etc/emstrack/migrations/login
RUN ln -s /etc/emstrack/migrations/login     $APP_HOME/login/migrations
RUN mkdir /etc/emstrack/migrations/hospital
RUN ln -s /etc/emstrack/migrations/hospital  $APP_HOME/hospital/migrations
RUN mkdir /etc/emstrack/migrations/equipment
RUN ln -s /etc/emstrack/migrations/equipment $APP_HOME/equipment/migrations

# NPM packages
RUN npm install

# Init scripts

COPY --chown=worker:worker scripts/. /home/worker/.local/bin/.
RUN chmod +x /home/worker/.local/bin/*

# Entrypoint script
COPY --chown=worker:worker docker-entrypoint.sh /home/worker/.local/bin/docker-entrypoint.sh
RUN chmod +x /home/worker/.local/bin/docker-entrypoint.sh

COPY --chown=worker:worker docker-entrypoint-init.sh /home/worker/.local/bin/docker-entrypoint-init.sh
RUN chmod +x /home/worker/.local/bin/docker-entrypoint-init.sh

# Add VOLUME to allow backup of config, logs and databases
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["all"]
