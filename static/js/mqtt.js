import { Client } from 'paho-mqtt';

import { Observer } from './observer';

export class MqttClient extends Observer {

    constructor(host, port, clientId, logLevel) {

        // call super
        super();

        logLevel = logLevel || 1;

        this.host = host;
        this.port = port;
        this.clientId = clientId;
        this.logLevel = logLevel;

        this.client = null;
        this.isConnected = false;
    }

    connect(options) {

        options = options || {};

        // just return if already connected
        if (this.isConnected)
            return;

        // create mqtt client
        this.client = new Client(this.host, this.port, this.clientId);

        // set callback handlers
        this.client.onMessageArrived = (message) => this.onMessageArrived(message);
        this.client.onConnectionLost = (errorCode, errorMessage) => this.onConnectionLost(errorCode, errorMessage);
        this.client.onMessageDelivered = (message) => this.onMessageDelivered(message);
        this.client.onConnected = (reconnect, uri) => this.onConnected(reconnect, uri);

        // options
        this.options = {
            timeout: 60,
            useSSL: true,
            cleanSession: true
        };

        // Altering using user-provided options
        for (const property in options) {
            if (options.hasOwnProperty(property)) {
                this.options[property] = options[property];
            }
        }

        console.log(this.options);

        // attempt to connect to MQTT broker
        this.client.connect(this.options);

    }

    disconnect() {
        this.client.disconnect();
    }

    onConnected(reconnect, uri) {
        if (this.logLevel > 0)
            console.log("Connected to mqtt client");
        this.isConnected = true;
    }

    onConnectionLost(errorCode, errorMessage) {
        if (this.logLevel > 0)
            console.log("Disconnected from mqtt client");
        this.isConnected = false;
    }

    onMessageDelivered(message) {
        if (this.logLevel > 2)
            console.log("Message '" + message.destinationName + ':' + message.payloadString + "' delivered");
    }

    onMessageArrived(message) {
        if (this.logLevel > 1)
            console.log("Message '" + message.destinationName + ':' + message.payloadString + "' arrived");

        // broadcast message
        this.broadcast(message);
    }

}