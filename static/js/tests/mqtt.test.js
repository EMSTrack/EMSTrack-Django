const expect = require('chai').expect;

const settings = require('./mqtt/client-harness');

const axios = require('axios');

import { MqttClient } from "../mqtt-client";

describe('mqtt connection using password', () => {

    const mqttClient = new MqttClient('localhost', 8884, 'test-client', 1);

    const userName = 'admin';
    const password = 'cruzrojaadmin';

    it('should connect', function(done) {

        mqttClient.connect({
            userName: userName,
            password: password
        })
            .then( () => {
                done();
            })
            .catch( (error) => {
                console.log(error); done(new Error('Did not receive!'));
            });

    });

    it('is connected', function() {

        expect(mqttClient.isConnected).to.equal(true);

    });

    it('should disconnect', function(done) {

        const resolvingPromise = new Promise(function(resolve, reject) {
            // the function is executed automatically when the promise is constructed
            mqttClient.disconnect();
            while (mqttClient.isConnected) { /* wait */ }
            resolve('disconnected');

            setTimeout(() => reject(new Error("timeout!")), 1000);
        });

        resolvingPromise
            .then(
                (result) => {
                    expect(result).to.equal('disconnected');
                    expect(mqttClient.isConnected).to.equal(false);
                    expect(mqttClient.client).to.equal(undefined);
                },
                () => {}
            )
            .finally(done);

    })

});

describe('mqtt messages', () => {

    const mqttClient = new MqttClient('localhost', 8884, 'test-client', 1);

    const userName = 'admin';
    const password = 'cruzrojaadmin';

    it('connect', function(done) {

        mqttClient.connect({
            userName: userName,
            password: password
        })
            .then( () => {
                done();
            })
            .catch( (error) => {
                console.log(error); done(new Error('Did not receive!'));
            });

    });

    it('send message', function(done) {

        const fn = (event) =>  {
            if (event.event === 'messageSent') {
                mqttClient.remove(fn);
                done();
            }
        };

        mqttClient.observe(fn);
        mqttClient.publish('test/message', 'Hi!', 2, false);

    });

    it('subscribe', function(done) {

        mqttClient.subscribe('test/message', {
            onSuccess: () => {
                done();
            },
            onFailure: (cntxt, errorCode, errorMessage) => {
                done(new Error(errorMessage));
            }
        })

    });

    it('message arrived', function(done) {

        const fn = (event, message) => {
            if (event.event === 'messageArrived') {
                mqttClient.remove(fn);
                expect(event.object.destinationName).to.equal('test/message');
                expect(event.object.payloadString).to.equal('Hi!');
                done();
            }
        };

        mqttClient.observe(fn);
        mqttClient.publish('test/message', 'Hi!', 2, false);

    });

    it('disconnect', function(done) {

        const resolvingPromise = new Promise(function(resolve, reject) {
            // the function is executed automatically when the promise is constructed
            mqttClient.disconnect();
            while (mqttClient.isConnected) { /* wait */ }
            resolve('disconnected');

            setTimeout(() => reject(new Error("timeout!")), 1000);
        });

        resolvingPromise
            .then(
                (result) => {
                    expect(result).to.equal('disconnected');
                    expect(mqttClient.isConnected).to.equal(false);
                    expect(mqttClient.client).to.equal(undefined);
                },
                () => {}
            )
            .finally(done);

    })

});

describe('mqtt connection using api', () => {

    const userName = 'admin';
    const password = 'cruzrojaadmin';
    let token = null;

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
                console.log(error);
                done(new Error(error));
            });

    });

    it('get password', function(done) {

        const instance = axios.create({
            baseURL: 'http://localhost:8000/en/api/',
            timeout: 1000,
            headers: {'Authorization': 'Token ' + token}
        });

        let mqttPassword = null;

        instance.get('user/' + userName + '/password/')
            .then( (response) => {
                mqttPassword = response.data;
                expect(mqttPassword !== null).to.equal(true);
                done();
            })
            .catch( (error ) => {
                console.log(error);
                done(new Error(error));
            });

    });

});
