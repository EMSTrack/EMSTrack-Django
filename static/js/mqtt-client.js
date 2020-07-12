import { Client } from 'paho-mqtt';

import { Observer } from './observer';

import { logger } from './logger';

export class MqttEvent {

    constructor(event, object) {
        this.event = event;
        this.object = object;
    }

}

export class MqttConnectEvent extends MqttEvent {
    constructor(reconnect, uri) {
        super('connect', {reconnect: reconnect, uri: uri});
    }
}


export class MqttConnectionLostEvent extends MqttEvent {
    constructor(errorCode, errorMessage) {
        super('lostConnection', {errorCode: errorCode, errorMessage: errorMessage});
    }
}

export class MqttMessageSentEvent extends MqttEvent {
    constructor(message) {
        super('messageSent', message);
    }
}


export class MqttMessageArrivedEvent extends MqttEvent {
    constructor(message) {
        super('messageArrived', message);
    }
}


export class MqttClient extends Observer {

    constructor(host, port, clientId, logLevel = 1) {

        // call super
        super();

        this.host = host;
        this.port = port;
        this.clientId = clientId;
        this.logLevel = logLevel;

        this.client = undefined;
        this.isConnected = false;
    }

    connect(options = {}) {

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
        const mqttOptions = {
            timeout: 60,
            useSSL: true,
            cleanSession: true
        };

        // Altering using user-provided options
        for (const property in options) {
            if (options.hasOwnProperty(property)) {
                mqttOptions[property] = options[property];
            }
        }

        return new Promise( (resolve, reject) => {

            mqttOptions.onSuccess = (ctx) => { resolve('connected'); }
            mqttOptions.onFailure = (ctx, errorCode, errorMessage) => {
                reject( new Error("error '" + errorCode + "': " + errorMessage));
            }

            // attempt to connect to MQTT broker
            this.client.connect(mqttOptions);

        });

    }

    disconnect() {
        if (typeof this.client !== 'undefined') {
            this.client.disconnect();
            this.client = undefined;
        }
    }

    subscribe(filter, options) {
        if (typeof this.client !== 'undefined') {
            this.client.subscribe(filter, options);
        }
    }

    publish(topic, payload, qos, retained) {
        if (typeof this.client !== 'undefined') {
            this.client.publish(topic, payload, qos, retained);
        }
    }

    unsubscribe(filter, options) {
        if (typeof this.client !== 'undefined') {
            this.client.unsubscribe(filter, options);
        }
    }

    onConnected(reconnect, uri) {
        if (this.logLevel > 0)
            logger.log('info', "Connected to mqtt broker");
        this.isConnected = true;
        this.broadcast(new MqttConnectEvent(reconnect, uri));
    }

    onConnectionLost(errorCode, errorMessage) {
        if (this.logLevel > 0)
            logger.log('info', "Disconnected from mqtt broker");
        this.isConnected = false;
        this.broadcast(new MqttConnectionLostEvent(errorCode, errorMessage));
    }

    onMessageDelivered(message) {
        if (this.logLevel > 2)
            logger.log('debug', "Message '%s:%s' delivered", message.destinationName, message.payloadString);
        this.broadcast(new MqttMessageSentEvent(message));
    }

    onMessageArrived(message) {
        if (this.logLevel > 1)
            logger.log('debug', "Message '%s:%s' arrived", message.destinationName, message.payloadString);
        this.broadcast(new MqttMessageArrivedEvent(message));
    }

}