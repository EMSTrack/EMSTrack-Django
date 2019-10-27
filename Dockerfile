# Using ubuntu as a base image
FROM python:3.7

# Getting rid of debconf messages
ARG DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN set -x && \
    apt-get update -y && \
    apt-get install -y apt-utils && \
    apt-get install -y dumb-init git gettext \
            gdal-bin libgdal-dev python3-gdal \
            postgresql-client mosquitto-clients

# Install node
RUN curl -sL https://deb.nodesource.com/setup_10.x | bash - && \
    apt-get install -y nodejs

# Build variables
ARG BUILD_APP_HOME=/app
ARG BUILD_SCRIPT_HOME=/usr/local/bin

ENV APP_HOME=$BUILD_APP_HOME
ENV SCRIPT_HOME=$BUILD_SCRIPT_HOME
WORKDIR $APP_HOME

ENV PATH="$APP_HOME/node_modules/.bin:${PATH}"

# install requirements
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# install npm packages
COPY package.json package.json
RUN npm install

# link migration directories into persistent volume
RUN set -x && \
    mkdir -p /etc/emstrack/migrations && \
    mkdir -p /etc/emstrack/migrations/ambulance && \
    mkdir ambulance && \
    ln -s /etc/emstrack/migrations/ambulance $APP_HOME/ambulance/migrations && \
    mkdir -p /etc/emstrack/migrations/login && \
    mkdir login && \
    ln -s /etc/emstrack/migrations/login     $APP_HOME/login/migrations && \
    mkdir -p /etc/emstrack/migrations/hospital && \
    mkdir hospital && \
    ln -s /etc/emstrack/migrations/hospital  $APP_HOME/hospital/migrations && \
    mkdir -p /etc/emstrack/migrations/equipment && \
    mkdir equipment && \
    ln -s /etc/emstrack/migrations/equipment $APP_HOME/equipment/migrations && \
    # mosquitto directories
    mkdir -p /mosquitto/data && \
    touch /mosquitto/data/passwd && \
    mkdir -p /mosquitto-test/data && \
    touch /mosquitto-test/data/passwd && \
    # log directories
    mkdir -p /etc/emstrack/log && \
    touch /etc/emstrack/log/django.log && \
    touch /etc/emstrack/log/emstrack.log

# Clone application
COPY . .

# Init scripts
COPY scripts/. $SCRIPT_HOME
RUN chmod +x $SCRIPT_HOME/emstrack-*.sh

# Init mqttclient
COPY init/mqtt-client.sh /etc/init.d
RUN chmod /etc/init.d/mqtt-client.sh
RUN update-rc.d mqtt-client defaults

# Entrypoint script
COPY docker-entrypoint.sh $SCRIPT_HOME/docker-entrypoint.sh
RUN chmod +x $SCRIPT_HOME/docker-entrypoint.sh

COPY docker-entrypoint-init.sh $SCRIPT_HOME/docker-entrypoint-init.sh
RUN chmod +x $SCRIPT_HOME/docker-entrypoint-init.sh

# Add VOLUME to allow backup of config, logs and databases
ENTRYPOINT ["/usr/bin/dumb-init", "--", "docker-entrypoint.sh"]
CMD ["all"]
