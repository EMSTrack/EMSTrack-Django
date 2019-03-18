import { MqttClient, MqttEvent } from "./mqtt-client";

const axios = require('axios');

import { TopicObserver } from "./topic-observer";

export class Client extends TopicObserver {

    constructor(client) {

        // call super
        super();

        this.mqttClient = client;
        this.event_observer = null;

        // register observer
        this.event_observer = (event) => this.eventHandler(event);
        this.mqttClient.observe(this.event_observer);

    }

    disconnect() {

        // return if not connected
        if (!this.mqttClient.isConnected)
            return;

        // remove observer
        this.mqttClient.remove(this.observer);
        this.event_observer = null;

        // connect to client
        this.mqttClient.disconnect();

    }

    eventHandler(event) {

        if (event.event === 'messageReceived') {

            const topic = event.object.destinationName;
            const payload = event.object.payloadString;

            // broadcast
            this.observers.broadcast(topic, payload);

        }

    }

}

/*
    connect(username, options) {

        // return if already connected
        if (this.mqttClient.isConnected)
            return;

        // retrieve temporary password for mqttClient and connect to broker
        axios.get(this.ApiBaseUrl + 'user/' + username + '/password/')
            .then(response => {

                console.log( "success" );
                console.log(response.data);

                // override options
                options['username'] = username;
                options['password'] = response.data.password;

                // connect to client
                this.mqttClient.connect(options);

                // register observer
                this.event_observer = (event) => this.eventHandler(event);
                this.mqttClient.observe(this.event_observer);

            })
            .catch(error => {
                console.log(error);
            });

    }

*/