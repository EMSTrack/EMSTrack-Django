import { MqttClient, MqttEvent } from "./mqtt";

import { Observer } from "./observer";

export class Client extends Observer {

    constructor(host, port, clientId) {
        this.mqttClient = new MqttClient(host, port, clientId);
        this.observer = null;
    }

    connect(username, options) {

        // return if already connected
        if (this.mqttClient.isConnected)
            return;

        // retrieve temporary password for mqttClient and connect to broker
        $.getJSON(APIBaseUrl + 'user/' + this.username + '/password/',
            (password) => {

                // override options
                options['username'] = username;
                options['password'] = password;

                // connect to client
                this.mqttClient.connect(options);

                // register observer
                this.observer = (event) => this.eventHandler(event);
                this.mqttClient.observe(this.observer);

            });
    }

    disconnect() {

        // return if not connected
        if (!this.mqttClient.isConnected)
            return;

        // remove observer
        this.mqttClient.remove(this.observer);
        this.observer = null;

        // connect to client
        this.mqttClient.disconnect();

    }

    eventHandler(event) {

        if (event.event === 'messageReceived') {

        }

    }

}

