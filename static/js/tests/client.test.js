import $ from 'jquery';

import { Client } from "../client";

describe('client connection', () => {

    const client = new Client('localhost', 8884, 'test-client');

    const userName = 'admin';

    it('should connect', function(done) {

        client.connect(userName, {
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
                    expect(client.isConnected).to.equal(false);
                    expect(client.client).to.equal(null);
                },
                () => {}
            )
            .finally(done);

    })

});
