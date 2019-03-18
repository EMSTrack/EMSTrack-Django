const expect = require('chai').expect;

const axios = require('axios');

import { MqttClient } from "../mqtt-client";

import { Client } from "../client";

describe('client connection', () => {

    const userName = 'admin';
    const password = 'cruzrojaadmin';

    let token = null;
    let mqttPassword = null;

    let mqttClient = null;
    let httpClient = null;
    let client = null;

    it('get token', function(done) {

        axios.post('http://localhost:8000/en/auth/token/',
            {
                username: userName,
                password: password
            }
        )
            .then( (response) => {
                token = response.data.token;
                expect(token !== null).to.equal(true);
                console.log(token);
                done();
            })
            .catch( (error ) => {
                console.log(error);
                done(new Error(error));
            });

    });

    it('create http client and get password', function(done) {

        httpClient = axios.create({
            baseURL: 'http://localhost:8000/en/api/',
            timeout: 1000,
            headers: {'Authorization': 'Token ' + token}
        });

        httpClient.get('user/' + userName + '/password/')
            .then( (response) => {
                console.log(response);
                mqttPassword = response.data;
                expect(mqttPassword !== null).to.equal(true);
                done();
            })
            .catch( (error ) => {
                console.log(error);
                done(new Error(error));
            });

    });

    it('create mqtt client', function(done) {

        mqttClient = new MqttClient('localhost', 8884, 'test-client', 1);

        mqttClient.connect({
            userName: userName,
            password: mqttPassword,
            onSuccess: () => {
                done();
            },
            onFailure: (cntxt, errorCode, errorMessage) => {
                done(new Error(errorMessage));
            }
        });

    });

    it('is connected', function() {

        expect(client.mqttClient.isConnected).to.equal(true);

    });

    it('create client', function() {

        const client = new Client(mqttClient, httpClient);

    });

    it('should disconnect', function(done) {

        const resolvingPromise = new Promise(function(resolve, reject) {
            // the function is executed automatically when the promise is constructed
            client.disconnect();
            while (client.mqttClient.isConnected) { /* wait */ }
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
