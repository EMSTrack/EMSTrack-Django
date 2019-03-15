const expect = require('chai').expect;

var settings = require('./mqtt/client-harness');

import { MqttClient } from "../mqtt";

describe('mqtt', () => {

    console.log(settings);

    context('subscribe', function() {
        it('should subscribe', function() {
            expect(1).to.equal(1)
        })
    })

    const mqttClient = new MqttClient('localhost', 8884, 'test-client', 1);

    const userName = 'admin';
    const password = 'cruzrojaadmin';

    context('connect', function() {
        it('should connect', function(done) {
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
        })
    })


    const resolvingPromise = new Promise(function(resolve, reject) {
        // the function is executed automatically when the promise is constructed
        mqttClient.disconnect();
        while (mqttClient.isConnected) { /* wait */ }
        resolve('disconnected');

        setTimeout(() => reject(new Error("timeout!")), 1000);
    });

    context('disconnect', function() {
        it('should disconnect', function(done) {
            resolvingPromise.then( (result) => {
                expect(result).to.equal('disconnected');
            }).finally(done);
        })
    })

});
