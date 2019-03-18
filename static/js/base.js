import { MqttClient } from "./mqtt-client";

import { AppClient } from "./app-client";

const httpClient = require('axios');

let apiClient;

let APIBaseUrl = window.location.origin;
console.log(APIBaseUrl);

// Ready function
$(function () {

    let mqttClient;

    // retrieve temporary password for mqttClient and connect to broker
    console.log('Retrieving MQTT password');
    httpClient.get(APIBaseUrl + 'user/' + username + '/password/')
        .then( (response) => {

            // got password
            const password = response.data;
            mqttClient = new MqttClient('localhost', 8884, 'test-client');

            console.log('Connecting to MQTT broker');
            return mqttClient.connect({
                userName: username,
                password: password
            });

        })
        .then( () => {

            // instantiate client
            apiClient = new AppClient(mqttClient, httpClient);

            // retrieve ambulances
            console.log('Retrieving ambulances');
            return apiClient.retrieveAmbulances();

        })
        .then( (ambulances) => {
            console.log(Object.keys(ambulances).length + ' ambulances retrieved.');
            console.log('Done initializing ApiClient');
        })
        .catch( (error ) => {
            console.log('Failed to initialize ApiClient');
            console.log(error);
        });

});
