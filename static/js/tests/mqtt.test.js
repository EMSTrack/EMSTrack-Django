const expect = require('chai').expect;

import { MqttClient } from "../mqtt";

describe('mqtt', () => {

    const mqttClient = new MqttClient('localhost', 8884, 'test-client', 1);

    const userName = 'admin';
    const password = 'cruzrojaadmin';

    context('connect', function() {
        it('should subscribe', function(done) {
            mqttClient.connect({
                userName: userName,
                password: password,
                onSuccess: () => { done(); },
                onFailure: (cntxt, errorCode, errorMessage) => { done(errorMessage); }
            });
        })
    })

});
