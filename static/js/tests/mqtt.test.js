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
        it('should subscribe', function(done) {
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

});
