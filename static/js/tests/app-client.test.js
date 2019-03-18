const expect = require('chai').expect;

const axios = require('axios');

import { MqttClient } from "../mqtt-client";

import { AppClient } from "../app-client";

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
                done();
            })
            .catch( (error ) => {
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
                mqttPassword = response.data;
                expect(mqttPassword !== null).to.equal(true);
                done();
            })
            .catch( (error ) => {
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

    it('publish and receive', function(done) {

        client = new AppClient(mqttClient, httpClient);

        if (true) {

            let receivedData = '';
            const fn = function (data) {
                console.log(data);
                receivedData = data;
            };

            new Promise(function (resolve, reject) {

                client.subscribe('test/data', fn, {qos: 2});
                client.publish('test/data', 'something', 2, false);

                while (receivedData === '') { /* wait */
                }
                resolve('got it!');

                setTimeout(() => reject(new Error("timeout!")), 1000);

            })
                .then(
                    () => {
                        expect(receivedData).to.equal('something');
                        client.unsubscribe('test/data', fn);
                    },
                    () => {
                    }
                )
                .finally(done);

        } else

            done();

    });

    it('retrieve data', function(done) {

        // retrieve ambulances
        expect(client.ambulances).to.be.an('undefined');
        client.retrieveAmbulances();
        expect(client.ambulances).to.be.an('object');

        done();

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
