const expect = require('chai').expect;

import { MqttClient } from "../mqtt-client";

import { Client } from "../client";

describe('client connection', () => {

    const mqttClient = new MqttClient('localhost', 8884, 'test-client', 1);

    const userName = 'admin';
    const password = 'cruzrojaadmin';

    it('connect', function(done) {

        mqttClient.connect({
            userName: userName,
            password: password,
            onSuccess: () => {
                done();
            },
            onFailure: (cntxt, errorCode, errorMessage) => {
                done(errorMessage);
            }
        });

    });

    it('is connected', function() {

        expect(client.mqttClient.isConnected).to.equal(true);

    });

    const client = new Client(mqttClient);

    it('should disconnect', function(done) {

        const resolvingPromise = new Promise(function(resolve, reject) {
            // the function is executed automatically when the promise is constructed
            client.disconnect();
            while (client.isConnected) { /* wait */ }
            resolve('disconnected');

            setTimeout(() => reject(new Error("timeout!")), 1000);
        });

        resolvingPromise
            .then(
                (result) => {
                    expect(result).to.equal('disconnected');
                    expect(client.mqttClient.isConnected).to.equal(false);
                    expect(client.event_observer).to.equal(null);
                },
                () => {}
            )
            .finally(done);

    })

});
